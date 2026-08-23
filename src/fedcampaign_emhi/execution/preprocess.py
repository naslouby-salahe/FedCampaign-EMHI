import hashlib
from collections.abc import MutableMapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from fedcampaign_emhi.artifacts.dependencies import descendant_ids
from fedcampaign_emhi.artifacts.paths import ArtifactLayout, build_artifact_layout
from fedcampaign_emhi.artifacts.provenance import material_fingerprint
from fedcampaign_emhi.artifacts.records import (
    ArtifactManifest,
    BenignHorizonRecord,
    BenignPartitionRecord,
    CampaignRecord,
    CampaignRegistryRecord,
    DatasetInventoryFileRecord,
    DatasetInventoryRecord,
    DatasetSplitRecord,
    PreparedDatasetRecord,
    PreparedEpochRecord,
)
from fedcampaign_emhi.artifacts.storage import file_sha256, payload_digest, write_atomic_json
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.datasets.campaigns import build_campaign_registry
from fedcampaign_emhi.datasets.edge_iiotset.canonicalization import (
    canonical_event_type as edge_canonical_event_type,
    record_enters_epoch_event_count,
)
from fedcampaign_emhi.datasets.edge_iiotset.ground_truth import edge_iiotset_ground_truth
from fedcampaign_emhi.datasets.edge_iiotset.loading import load_edge_iiotset_csv_with_exclusions
from fedcampaign_emhi.datasets.edge_iiotset.validation import (
    select_secondary_clients,
    separate_benign_and_evaluation as separate_edge_benign_and_evaluation,
)
from fedcampaign_emhi.datasets.inventory import (
    configured_raw_directory,
    discover_raw_paths,
    inventory_raw_directory,
)
from fedcampaign_emhi.datasets.partitions import epoch_index
from fedcampaign_emhi.datasets.preprocessing import (
    chronological_benign_partitions,
    chronological_partition_lengths,
    common_benign_epoch_bounds,
    complete_benign_horizons,
    epoch_feature_vector,
    inclusive_epoch_range,
)
from fedcampaign_emhi.datasets.ton_iot_network.canonicalization import (
    canonical_client_id,
    canonical_event_type as ton_canonical_event_type,
    event_type_hash_bucket as ton_event_type_hash_bucket,
)
from fedcampaign_emhi.datasets.ton_iot_network.ground_truth import ton_iot_network_ground_truth
from fedcampaign_emhi.datasets.ton_iot_network.loading import (
    load_ton_iot_network_csv_with_exclusions,
)
from fedcampaign_emhi.datasets.ton_iot_network.validation import (
    select_primary_clients,
    separate_benign_and_evaluation as separate_ton_benign_and_evaluation,
)
from fedcampaign_emhi.domain.enums import (
    ArtifactLifecycleState,
    ArtifactNamespace,
    ClaimState,
    DatasetName,
    DownstreamArtifactKind,
    GroundTruthClass,
    OverwritePolicy,
    PreprocessingLayer,
)
from fedcampaign_emhi.domain.types import (
    ArtifactDependencyNode,
    ArtifactIdentity,
    ClientId,
    ClientMaliciousEpochs,
    ConfigurationDigest,
    EdgeIiotsetFlowRecord,
    EpochIndexValue,
    ExcludedRecord,
    MaterialDependencyFingerprint,
    PreprocessExecutionRecord,
    PreprocessingLayerDecision,
    RecordCount,
    SignedInt,
    TonIotNetworkFlowRecord,
)

PREPROCESSING_LAYER_ORDER: tuple[PreprocessingLayer, ...] = (
    PreprocessingLayer.INVENTORY,
    PreprocessingLayer.PREPARED,
    PreprocessingLayer.SPLITS,
    PreprocessingLayer.PARTITIONS,
    PreprocessingLayer.CAMPAIGN_REGISTRY,
)


@dataclass(frozen=True)
class DatasetMaterialization:
    inventory: DatasetInventoryRecord
    prepared: PreparedDatasetRecord
    split: DatasetSplitRecord
    partitions: BenignPartitionRecord
    campaigns: CampaignRegistryRecord


def requested_datasets(dataset_name: DatasetName | None) -> tuple[DatasetName, ...]:
    if dataset_name is None:
        return (DatasetName.TON_IOT_NETWORK, DatasetName.EDGE_IIOTSET)
    return (dataset_name,)


def preprocess_must_not_regenerate() -> tuple[DownstreamArtifactKind, ...]:
    return (
        DownstreamArtifactKind.DETECTOR_MODELS,
        DownstreamArtifactKind.SCORES,
        DownstreamArtifactKind.EXPERIMENT_EVALUATIONS,
        DownstreamArtifactKind.STATISTICS,
        DownstreamArtifactKind.REPORTS,
    )


def dataset_directory_stem(dataset_name: DatasetName) -> ArtifactIdentity:
    return dataset_name.value.replace(" ", "_")


def layer_artifact_id(dataset_name: DatasetName, layer: PreprocessingLayer) -> ArtifactIdentity:
    return f"preprocess.{dataset_directory_stem(dataset_name)}.{layer.value}"


def downstream_artifact_id(
    dataset_name: DatasetName, kind: DownstreamArtifactKind
) -> ArtifactIdentity:
    return f"downstream.{dataset_directory_stem(dataset_name)}.{kind.name.lower()}"


def preprocessing_dependency_graph(dataset_name: DatasetName) -> tuple[ArtifactDependencyNode, ...]:
    layer_ids = tuple(layer_artifact_id(dataset_name, layer) for layer in PREPROCESSING_LAYER_ORDER)
    nodes: list[ArtifactDependencyNode] = []
    for index, artifact_id in enumerate(layer_ids):
        upstream_ids = () if index == 0 else (layer_ids[index - 1],)
        nodes.append(
            ArtifactDependencyNode(
                artifact_id=artifact_id,
                material_fingerprint=_structural_fingerprint(artifact_id),
                upstream_ids=upstream_ids,
            )
        )
    registry_id = layer_ids[-1]
    for kind in preprocess_must_not_regenerate():
        downstream_id = downstream_artifact_id(dataset_name, kind)
        nodes.append(
            ArtifactDependencyNode(
                artifact_id=downstream_id,
                material_fingerprint=_structural_fingerprint(downstream_id),
                upstream_ids=(registry_id,),
            )
        )
    return tuple(nodes)


def nearest_reconstruction_layer(
    reusable: tuple[bool, ...], overwrite_policy: OverwritePolicy
) -> PreprocessingLayer | None:
    if overwrite_policy is OverwritePolicy.OVERWRITE:
        return PREPROCESSING_LAYER_ORDER[0]
    for layer, is_reusable in zip(PREPROCESSING_LAYER_ORDER, reusable, strict=True):
        if not is_reusable:
            return layer
    return None


def execute_preprocess(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName | None,
    overwrite_policy: OverwritePolicy,
) -> PreprocessExecutionRecord:
    datasets = requested_datasets(dataset_name)
    decisions: list[PreprocessingLayerDecision] = []
    reconstruction_boundaries: list[tuple[DatasetName, PreprocessingLayer | None]] = []
    for requested_dataset in datasets:
        start_layer, dataset_decisions = _execute_dataset(
            loaded, repository, requested_dataset, overwrite_policy
        )
        reconstruction_boundaries.append((requested_dataset, start_layer))
        decisions.extend(dataset_decisions)
    return PreprocessExecutionRecord(
        decisions=tuple(decisions),
        requested_datasets=datasets,
        reconstruct_from=tuple(reconstruction_boundaries),
    )


def _execute_dataset(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    overwrite_policy: OverwritePolicy,
) -> tuple[PreprocessingLayer | None, tuple[PreprocessingLayerDecision, ...]]:
    layout = build_artifact_layout(loaded, repository)
    raw_directory = configured_raw_directory(loaded, dataset_name, repository)
    raw_inventory = inventory_raw_directory(raw_directory, repository)
    inventory_digest = payload_digest(
        cast(
            YamlNode,
            [
                {
                    "relative_path": entry.relative_path,
                    "sha256": entry.sha256,
                    "byte_count": entry.byte_count,
                }
                for entry in raw_inventory
            ],
        )
    )
    expected_fingerprints = _expected_fingerprints(loaded, dataset_name, inventory_digest)
    reusable = tuple(
        _layer_is_reusable(layout, dataset_name, layer, expected_fingerprints[index])
        for index, layer in enumerate(PREPROCESSING_LAYER_ORDER)
    )
    previous_fingerprints = tuple(
        _stored_fingerprint(layout, dataset_name, layer) for layer in PREPROCESSING_LAYER_ORDER
    )
    start_layer = nearest_reconstruction_layer(reusable, overwrite_policy)
    if start_layer is None:
        return None, tuple(
            PreprocessingLayerDecision(
                dataset_name=dataset_name,
                layer=layer,
                reused=True,
                reconstructed=False,
                previous_fingerprint=previous_fingerprints[index],
                current_fingerprint=expected_fingerprints[index],
                invalidated_descendant_ids=(),
            )
            for index, layer in enumerate(PREPROCESSING_LAYER_ORDER)
        )
    materialization = _build_dataset_materialization(
        loaded, repository, dataset_name, inventory_digest
    )
    decisions: list[PreprocessingLayerDecision] = []
    ancestor_changed = False
    start_index = PREPROCESSING_LAYER_ORDER.index(start_layer)
    for index, layer in enumerate(PREPROCESSING_LAYER_ORDER):
        previous = previous_fingerprints[index]
        current = expected_fingerprints[index]
        reconstructed = overwrite_policy is OverwritePolicy.OVERWRITE or index >= start_index
        if reconstructed:
            _materialize_layer(
                layout,
                dataset_name,
                layer,
                current,
                materialization,
                expected_fingerprints,
            )
        changed = reconstructed and previous is not None and previous != current
        ancestor_changed = ancestor_changed or changed
        decisions.append(
            PreprocessingLayerDecision(
                dataset_name=dataset_name,
                layer=layer,
                reused=not reconstructed,
                reconstructed=reconstructed,
                previous_fingerprint=previous,
                current_fingerprint=current,
                invalidated_descendant_ids=_downstream_invalidation(
                    dataset_name,
                    layer,
                    previous,
                    current,
                    reconstructed and (changed or ancestor_changed),
                ),
            )
        )
    return start_layer, tuple(decisions)


def _expected_fingerprints(
    loaded: LoadedScientificConfiguration,
    dataset_name: DatasetName,
    inventory_digest: ConfigurationDigest,
) -> tuple[MaterialDependencyFingerprint, ...]:
    fingerprints: list[MaterialDependencyFingerprint] = []
    producer_digest = _producer_code_digest()
    for layer in PREPROCESSING_LAYER_ORDER:
        upstream = fingerprints[-1] if fingerprints else None
        payload = cast(
            YamlNode,
            {
                "configuration_digest": loaded.material_digest,
                "dataset": dataset_name.value,
                "layer": layer.value,
                "raw_inventory_digest": inventory_digest,
                "upstream": upstream,
                "producer_code_digest": producer_digest,
            },
        )
        layer_digest = payload_digest(payload)
        upstream_digests = () if upstream is None else (upstream,)
        fingerprints.append(
            material_fingerprint(
                loaded.material_digest,
                (*upstream_digests, inventory_digest, layer_digest),
            )
        )
    return tuple(fingerprints)


def _producer_code_digest() -> ConfigurationDigest:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _layer_is_reusable(
    layout: ArtifactLayout,
    dataset_name: DatasetName,
    layer: PreprocessingLayer,
    expected_fingerprint: MaterialDependencyFingerprint,
) -> bool:
    manifest = _read_manifest(layout, dataset_name, layer)
    if manifest is None:
        return False
    if manifest.lifecycle_state is not ArtifactLifecycleState.VALID:
        return False
    if manifest.material_fingerprint != expected_fingerprint:
        return False
    product_path = layout.roots.outputs_root / manifest.relative_path
    return product_path.is_file() and file_sha256(product_path) == manifest.content_digest


def _stored_fingerprint(
    layout: ArtifactLayout,
    dataset_name: DatasetName,
    layer: PreprocessingLayer,
) -> MaterialDependencyFingerprint | None:
    manifest = _read_manifest(layout, dataset_name, layer)
    return None if manifest is None else manifest.material_fingerprint


def _build_dataset_materialization(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    inventory_digest: ConfigurationDigest,
) -> DatasetMaterialization:
    raw_directory = configured_raw_directory(loaded, dataset_name, repository)
    inventory_entries = inventory_raw_directory(raw_directory, repository)
    inventory = DatasetInventoryRecord(
        dataset_name=dataset_name,
        files=tuple(
            DatasetInventoryFileRecord(
                relative_path=entry.relative_path,
                sha256=entry.sha256,
                byte_count=entry.byte_count,
            )
            for entry in inventory_entries
        ),
        content_digest=inventory_digest,
    )
    if dataset_name is DatasetName.TON_IOT_NETWORK:
        return _build_ton_materialization(loaded, raw_directory, inventory)
    if dataset_name is DatasetName.EDGE_IIOTSET:
        return _build_edge_materialization(loaded, raw_directory, inventory)
    raise ValueError(f"unsupported dataset {dataset_name.value}")


def _csv_paths(raw_directory: Path) -> tuple[Path, ...]:
    return tuple(
        path for path in discover_raw_paths(raw_directory) if path.suffix.lower() == ".csv"
    )


def _increment_bucket(
    counts: tuple[RecordCount, ...], bucket_index: SignedInt
) -> tuple[RecordCount, ...]:
    return tuple(
        count + 1 if index == bucket_index else count for index, count in enumerate(counts)
    )


def _load_ton_records(
    raw_directory: Path,
) -> tuple[tuple[TonIotNetworkFlowRecord, ...], tuple[ExcludedRecord, ...]]:
    records: tuple[TonIotNetworkFlowRecord, ...] = ()
    exclusions: tuple[ExcludedRecord, ...] = ()
    for path in _csv_paths(raw_directory):
        file_records, file_exclusions = load_ton_iot_network_csv_with_exclusions(path)
        records = (*records, *file_records)
        exclusions = (*exclusions, *file_exclusions)
    return records, exclusions


def _build_ton_materialization(
    loaded: LoadedScientificConfiguration,
    raw_directory: Path,
    inventory: DatasetInventoryRecord,
) -> DatasetMaterialization:
    records, exclusions = _load_ton_records(raw_directory)
    separation = separate_ton_benign_and_evaluation(records)
    selection = select_primary_clients(
        records,
        loaded.values.time.real_data_epoch_seconds,
        loaded.values.datasets.eligibility.minimum_benign_event_records,
        loaded.values.datasets.eligibility.minimum_nonempty_benign_epochs,
        loaded.values.datasets.primary.target_client_count,
    )
    prepared = _prepare_ton_epochs(
        loaded, records, len(exclusions), len(separation.discrepancies)
    )
    split, partitions = _build_ton_partitions(
        loaded,
        selection.selected_client_ids,
        selection.eligible_client_ids,
        selection.claim_state,
        separation.benign_records,
    )
    campaigns = _build_ton_campaigns(
        loaded, selection.selected_client_ids, separation.evaluation_records
    )
    return DatasetMaterialization(
        inventory=inventory,
        prepared=prepared,
        split=split,
        partitions=partitions,
        campaigns=campaigns,
    )


def _prepare_ton_epochs(
    loaded: LoadedScientificConfiguration,
    records: tuple[TonIotNetworkFlowRecord, ...],
    excluded_count: RecordCount,
    discrepancy_count: RecordCount,
) -> PreparedDatasetRecord:
    bucket_count = loaded.values.datasets.preprocessing.event_type_hash_bucket_count
    counts: MutableMapping[tuple[ClientId, EpochIndexValue], tuple[RecordCount, ...]] = {}
    ambiguous: MutableMapping[tuple[ClientId, EpochIndexValue], RecordCount] = {}
    malicious: MutableMapping[tuple[ClientId, EpochIndexValue], RecordCount] = {}
    for record in records:
        client_id = canonical_client_id(record.source_ip)
        epoch = epoch_index(
            record.timestamp_seconds, loaded.values.time.real_data_epoch_seconds
        ).index
        key = (client_id, epoch)
        current = counts.get(key, tuple(0 for _index in range(bucket_count)))
        event_type = ton_canonical_event_type(record.protocol_token, record.service_token)
        bucket = ton_event_type_hash_bucket(event_type, bucket_count)
        counts[key] = _increment_bucket(current, bucket)
        ground_truth = ton_iot_network_ground_truth(record.binary_label, record.attack_type)
        if ground_truth.classification is GroundTruthClass.AMBIGUOUS:
            ambiguous[key] = ambiguous.get(key, 0) + 1
        elif ground_truth.classification is GroundTruthClass.MALICIOUS:
            malicious[key] = malicious.get(key, 0) + 1
    epochs = tuple(
        _prepared_epoch(
            DatasetName.TON_IOT_NETWORK,
            client_id,
            epoch,
            bucket_counts,
            ambiguous.get((client_id, epoch), 0),
            malicious.get((client_id, epoch), 0),
        )
        for (client_id, epoch), bucket_counts in sorted(counts.items())
    )
    return PreparedDatasetRecord(
        dataset_name=DatasetName.TON_IOT_NETWORK,
        epochs=epochs,
        excluded_record_count=excluded_count,
        ground_truth_discrepancy_count=discrepancy_count,
    )


def _prepared_epoch(
    dataset_name: DatasetName,
    client_id: ClientId,
    epoch: EpochIndexValue,
    bucket_counts: tuple[RecordCount, ...],
    ambiguous_count: RecordCount,
    malicious_count: RecordCount,
) -> PreparedEpochRecord:
    vector = epoch_feature_vector(bucket_counts)
    ground_truth = GroundTruthClass.BENIGN
    if malicious_count > 0:
        ground_truth = GroundTruthClass.MALICIOUS
    if ambiguous_count > 0:
        ground_truth = GroundTruthClass.AMBIGUOUS
    return PreparedEpochRecord(
        dataset_name=dataset_name,
        client_id=client_id,
        epoch_index=epoch,
        feature_values=(
            *vector.log1p_bucket_counts,
            float(vector.total_raw_event_count),
            vector.shannon_entropy,
        ),
        ground_truth=ground_truth,
        raw_event_count=vector.total_raw_event_count,
        ambiguous_event_count=ambiguous_count,
    )


def _build_ton_partitions(
    loaded: LoadedScientificConfiguration,
    selected_client_ids: tuple[ClientId, ...],
    eligible_client_ids: tuple[ClientId, ...],
    claim_state: ClaimState,
    benign_records: tuple[TonIotNetworkFlowRecord, ...],
) -> tuple[DatasetSplitRecord, BenignPartitionRecord]:
    per_client_epochs = tuple(
        tuple(
            sorted(
                {
                    epoch_index(
                        record.timestamp_seconds,
                        loaded.values.time.real_data_epoch_seconds,
                    ).index
                    for record in benign_records
                    if canonical_client_id(record.source_ip) == client_id
                }
            )
        )
        for client_id in selected_client_ids
    )
    return _build_common_partitions(
        loaded,
        DatasetName.TON_IOT_NETWORK,
        selected_client_ids,
        eligible_client_ids,
        claim_state,
        per_client_epochs,
    )


def _build_ton_campaigns(
    loaded: LoadedScientificConfiguration,
    selected_client_ids: tuple[ClientId, ...],
    evaluation_records: tuple[TonIotNetworkFlowRecord, ...],
) -> CampaignRegistryRecord:
    malicious_epochs = tuple(
        ClientMaliciousEpochs(
            client_id=client_id,
            malicious_epochs=tuple(
                sorted(
                    {
                        epoch_index(
                            record.timestamp_seconds,
                            loaded.values.time.real_data_epoch_seconds,
                        ).index
                        for record in evaluation_records
                        if canonical_client_id(record.source_ip) == client_id
                        and ton_iot_network_ground_truth(
                            record.binary_label, record.attack_type
                        ).classification
                        is GroundTruthClass.MALICIOUS
                    }
                )
            ),
        )
        for client_id in selected_client_ids
    )
    return _campaign_record(
        loaded, DatasetName.TON_IOT_NETWORK, selected_client_ids, malicious_epochs
    )


def _load_edge_records(
    raw_directory: Path,
) -> tuple[tuple[EdgeIiotsetFlowRecord, ...], tuple[ExcludedRecord, ...]]:
    records: tuple[EdgeIiotsetFlowRecord, ...] = ()
    exclusions: tuple[ExcludedRecord, ...] = ()
    for path in _csv_paths(raw_directory):
        file_records, file_exclusions = load_edge_iiotset_csv_with_exclusions(path)
        records = (*records, *file_records)
        exclusions = (*exclusions, *file_exclusions)
    return records, exclusions


def _build_edge_materialization(
    loaded: LoadedScientificConfiguration,
    raw_directory: Path,
    inventory: DatasetInventoryRecord,
) -> DatasetMaterialization:
    records, exclusions = _load_edge_records(raw_directory)
    separation = separate_edge_benign_and_evaluation(records)
    selection = select_secondary_clients(
        records,
        loaded.values.time.real_data_epoch_seconds,
        loaded.values.datasets.eligibility.minimum_benign_event_records,
        loaded.values.datasets.eligibility.minimum_nonempty_benign_epochs,
        loaded.values.datasets.secondary.target_client_count,
        loaded.values.datasets.secondary.minimum_eligible_client_count,
    )
    prepared = _prepare_edge_epochs(
        loaded, records, len(exclusions), len(separation.discrepancies)
    )
    split, partitions = _build_edge_partitions(
        loaded,
        selection.selected_client_ids,
        selection.eligible_client_ids,
        selection.claim_state,
        separation.benign_records,
    )
    campaigns = _build_edge_campaigns(
        loaded, selection.selected_client_ids, separation.evaluation_records
    )
    return DatasetMaterialization(
        inventory=inventory,
        prepared=prepared,
        split=split,
        partitions=partitions,
        campaigns=campaigns,
    )


def _prepare_edge_epochs(
    loaded: LoadedScientificConfiguration,
    records: tuple[EdgeIiotsetFlowRecord, ...],
    excluded_count: RecordCount,
    discrepancy_count: RecordCount,
) -> PreparedDatasetRecord:
    bucket_count = loaded.values.datasets.preprocessing.event_type_hash_bucket_count
    counts: MutableMapping[tuple[ClientId, EpochIndexValue], tuple[RecordCount, ...]] = {}
    ambiguous: MutableMapping[tuple[ClientId, EpochIndexValue], RecordCount] = {}
    malicious: MutableMapping[tuple[ClientId, EpochIndexValue], RecordCount] = {}
    for record in records:
        client_id = record.source_host.strip()
        epoch = epoch_index(
            record.timestamp_seconds, loaded.values.time.real_data_epoch_seconds
        ).index
        key = (client_id, epoch)
        if record_enters_epoch_event_count(record.protocol_group):
            current = counts.get(key, tuple(0 for _index in range(bucket_count)))
            event_type = edge_canonical_event_type(record.protocol_group)
            bucket = ton_event_type_hash_bucket(event_type, bucket_count)
            counts[key] = _increment_bucket(current, bucket)
        elif key not in counts:
            counts[key] = tuple(0 for _index in range(bucket_count))
        ground_truth = edge_iiotset_ground_truth(record.binary_label, record.attack_type)
        if ground_truth.classification is GroundTruthClass.AMBIGUOUS:
            ambiguous[key] = ambiguous.get(key, 0) + 1
        elif ground_truth.classification is GroundTruthClass.MALICIOUS:
            malicious[key] = malicious.get(key, 0) + 1
    epochs = tuple(
        _prepared_epoch(
            DatasetName.EDGE_IIOTSET,
            client_id,
            epoch,
            bucket_counts,
            ambiguous.get((client_id, epoch), 0),
            malicious.get((client_id, epoch), 0),
        )
        for (client_id, epoch), bucket_counts in sorted(counts.items())
    )
    return PreparedDatasetRecord(
        dataset_name=DatasetName.EDGE_IIOTSET,
        epochs=epochs,
        excluded_record_count=excluded_count,
        ground_truth_discrepancy_count=discrepancy_count,
    )


def _build_edge_partitions(
    loaded: LoadedScientificConfiguration,
    selected_client_ids: tuple[ClientId, ...],
    eligible_client_ids: tuple[ClientId, ...],
    claim_state: ClaimState,
    benign_records: tuple[EdgeIiotsetFlowRecord, ...],
) -> tuple[DatasetSplitRecord, BenignPartitionRecord]:
    per_client_epochs = tuple(
        tuple(
            sorted(
                {
                    epoch_index(
                        record.timestamp_seconds,
                        loaded.values.time.real_data_epoch_seconds,
                    ).index
                    for record in benign_records
                    if record.source_host.strip() == client_id
                }
            )
        )
        for client_id in selected_client_ids
    )
    return _build_common_partitions(
        loaded,
        DatasetName.EDGE_IIOTSET,
        selected_client_ids,
        eligible_client_ids,
        claim_state,
        per_client_epochs,
    )


def _build_edge_campaigns(
    loaded: LoadedScientificConfiguration,
    selected_client_ids: tuple[ClientId, ...],
    evaluation_records: tuple[EdgeIiotsetFlowRecord, ...],
) -> CampaignRegistryRecord:
    malicious_epochs = tuple(
        ClientMaliciousEpochs(
            client_id=client_id,
            malicious_epochs=tuple(
                sorted(
                    {
                        epoch_index(
                            record.timestamp_seconds,
                            loaded.values.time.real_data_epoch_seconds,
                        ).index
                        for record in evaluation_records
                        if record.source_host.strip() == client_id
                        and edge_iiotset_ground_truth(
                            record.binary_label, record.attack_type
                        ).classification
                        is GroundTruthClass.MALICIOUS
                    }
                )
            ),
        )
        for client_id in selected_client_ids
    )
    return _campaign_record(
        loaded, DatasetName.EDGE_IIOTSET, selected_client_ids, malicious_epochs
    )


def _build_common_partitions(
    loaded: LoadedScientificConfiguration,
    dataset_name: DatasetName,
    selected_client_ids: tuple[ClientId, ...],
    eligible_client_ids: tuple[ClientId, ...],
    claim_state: ClaimState,
    per_client_epochs: tuple[tuple[EpochIndexValue, ...], ...],
) -> tuple[DatasetSplitRecord, BenignPartitionRecord]:
    bounds = common_benign_epoch_bounds(per_client_epochs)
    if bounds is None:
        return (
            DatasetSplitRecord(
                dataset_name=dataset_name,
                selected_client_ids=selected_client_ids,
                eligible_client_ids=eligible_client_ids,
                claim_state=ClaimState.NOT_TESTED,
                detector_fit_epochs=(),
                nuisance_fit_epochs=(),
                threshold_calibration_epochs=(),
                heldout_benign_epochs=(),
            ),
            BenignPartitionRecord(
                dataset_name=dataset_name,
                calibration_horizons=(),
                heldout_horizons=(),
            ),
        )
    common_epochs = inclusive_epoch_range(bounds[0], bounds[1])
    fractions = loaded.values.datasets.preprocessing.benign_partition_fractions
    lengths = chronological_partition_lengths(
        len(common_epochs),
        fractions.detector_fit,
        fractions.nuisance_fit,
        fractions.threshold_and_policy_calibration,
    )
    partitions = chronological_benign_partitions(common_epochs, lengths)
    split = DatasetSplitRecord(
        dataset_name=dataset_name,
        selected_client_ids=selected_client_ids,
        eligible_client_ids=eligible_client_ids,
        claim_state=claim_state,
        detector_fit_epochs=partitions.detector_fit,
        nuisance_fit_epochs=partitions.nuisance_fit,
        threshold_calibration_epochs=partitions.threshold_and_policy_calibration,
        heldout_benign_epochs=partitions.heldout_benign,
    )
    horizon_length = loaded.values.campaign.evaluation_horizon_epochs
    calibration_horizons = complete_benign_horizons(
        partitions.threshold_and_policy_calibration, horizon_length
    )
    heldout_horizons = complete_benign_horizons(partitions.heldout_benign, horizon_length)
    return (
        split,
        BenignPartitionRecord(
            dataset_name=dataset_name,
            calibration_horizons=tuple(
                BenignHorizonRecord(
                    start_epoch=horizon.start_epoch,
                    epoch_indexes=horizon.epoch_indexes,
                )
                for horizon in calibration_horizons
            ),
            heldout_horizons=tuple(
                BenignHorizonRecord(
                    start_epoch=horizon.start_epoch,
                    epoch_indexes=horizon.epoch_indexes,
                )
                for horizon in heldout_horizons
            ),
        ),
    )


def _campaign_record(
    loaded: LoadedScientificConfiguration,
    dataset_name: DatasetName,
    selected_client_ids: tuple[ClientId, ...],
    malicious_epochs: tuple[ClientMaliciousEpochs, ...],
) -> CampaignRegistryRecord:
    registry = build_campaign_registry(
        dataset_name,
        selected_client_ids,
        malicious_epochs,
        loaded.values.campaign.merge_max_intervening_benign_epochs,
        loaded.values.distributed_support.minimum_clients,
        loaded.values.campaign.distributed_first_activity_window_epochs,
        loaded.values.campaign.minimum_duration_epochs,
        loaded.values.campaign.prestart_warmup_epochs,
    )
    return CampaignRegistryRecord(
        dataset_name=dataset_name,
        campaigns=tuple(
            CampaignRecord(
                start_epoch=entry.start_epoch,
                end_epoch=entry.end_epoch,
                participating_client_ids=entry.sorted_participating_client_ids,
                integrity_checksum=entry.integrity_checksum,
            )
            for entry in registry
        ),
    )


def _record_for_layer(
    materialization: DatasetMaterialization,
    layer: PreprocessingLayer,
) -> (
    DatasetInventoryRecord
    | PreparedDatasetRecord
    | DatasetSplitRecord
    | BenignPartitionRecord
    | CampaignRegistryRecord
):
    if layer is PreprocessingLayer.INVENTORY:
        return materialization.inventory
    if layer is PreprocessingLayer.PREPARED:
        return materialization.prepared
    if layer is PreprocessingLayer.SPLITS:
        return materialization.split
    if layer is PreprocessingLayer.PARTITIONS:
        return materialization.partitions
    return materialization.campaigns


def _materialize_layer(
    layout: ArtifactLayout,
    dataset_name: DatasetName,
    layer: PreprocessingLayer,
    fingerprint: MaterialDependencyFingerprint,
    materialization: DatasetMaterialization,
    expected_fingerprints: tuple[MaterialDependencyFingerprint, ...],
) -> None:
    record = _record_for_layer(materialization, layer)
    payload = cast(YamlNode, record.model_dump(mode="json"))
    content_digest = payload_digest(payload)
    product_path = _product_path(layout, dataset_name, layer)
    staging = layout.roots.outputs_root / "cache" / "staging"
    write_atomic_json(product_path, payload, staging)
    index = PREPROCESSING_LAYER_ORDER.index(layer)
    upstream_ids = ()
    if index > 0:
        upstream_ids = (layer_artifact_id(dataset_name, PREPROCESSING_LAYER_ORDER[index - 1]),)
        if expected_fingerprints[index - 1] == fingerprint:
            raise ValueError("preprocessing dependency fingerprint cannot equal its parent")
    manifest = ArtifactManifest(
        artifact_id=layer_artifact_id(dataset_name, layer),
        namespace=ArtifactNamespace.OUTPUTS,
        experiment_name=None,
        relative_path=product_path.relative_to(layout.roots.outputs_root).as_posix(),
        content_digest=content_digest,
        material_fingerprint=fingerprint,
        upstream_ids=upstream_ids,
        lifecycle_state=ArtifactLifecycleState.VALID,
    )
    write_atomic_json(
        _manifest_path(layout, dataset_name, layer),
        cast(YamlNode, manifest.model_dump(mode="json")),
        staging,
    )


def _product_path(
    layout: ArtifactLayout, dataset_name: DatasetName, layer: PreprocessingLayer
) -> Path:
    stem = dataset_directory_stem(dataset_name)
    root = layout.roots.outputs_root / "preprocessing"
    if layer is PreprocessingLayer.INVENTORY:
        return root / "inventories" / f"{stem}.json"
    if layer is PreprocessingLayer.PREPARED:
        return root / "prepared" / f"{stem}.json"
    if layer is PreprocessingLayer.SPLITS:
        return root / "splits" / f"{stem}.json"
    if layer is PreprocessingLayer.PARTITIONS:
        return root / "metadata" / f"{stem}-benign-partitions.json"
    return root / "metadata" / f"{stem}-campaign-registry.json"


def _manifest_path(
    layout: ArtifactLayout, dataset_name: DatasetName, layer: PreprocessingLayer
) -> Path:
    stem = dataset_directory_stem(dataset_name)
    return (
        layout.roots.outputs_root
        / "preprocessing"
        / "metadata"
        / f"{stem}-{layer.value}-manifest.json"
    )


def _read_manifest(
    layout: ArtifactLayout, dataset_name: DatasetName, layer: PreprocessingLayer
) -> ArtifactManifest | None:
    path = _manifest_path(layout, dataset_name, layer)
    if not path.is_file():
        return None
    try:
        return ArtifactManifest.model_validate_json(path.read_bytes())
    except ValueError:
        return None


def _downstream_invalidation(
    dataset_name: DatasetName,
    layer: PreprocessingLayer,
    previous: MaterialDependencyFingerprint | None,
    current: MaterialDependencyFingerprint,
    reconstructed_and_changed: bool,
) -> tuple[ArtifactIdentity, ...]:
    if not reconstructed_and_changed or previous is None or previous == current:
        return ()
    return tuple(
        artifact_id
        for artifact_id in descendant_ids(
            preprocessing_dependency_graph(dataset_name),
            (layer_artifact_id(dataset_name, layer),),
        )
        if _is_protected_downstream(dataset_name, artifact_id)
    )


def _structural_fingerprint(artifact_id: ArtifactIdentity) -> MaterialDependencyFingerprint:
    return hashlib.sha256(artifact_id.encode("utf-8")).hexdigest()


def _is_protected_downstream(dataset_name: DatasetName, artifact_id: ArtifactIdentity) -> bool:
    return any(
        artifact_id == downstream_artifact_id(dataset_name, kind)
        for kind in preprocess_must_not_regenerate()
    )
