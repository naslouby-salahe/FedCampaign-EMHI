import hashlib
import inspect
from collections.abc import MutableMapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import duckdb

from fedcampaign_emhi.artifacts.provenance import descendant_ids, material_fingerprint
from fedcampaign_emhi.artifacts.records import (
    ArtifactManifest,
    BenignHorizonRecord,
    BenignPartitionRecord,
    CampaignRecord,
    CampaignRegistryRecord,
    ClientFeatureScalerRecord,
    DatasetInventoryFileRecord,
    DatasetInventoryRecord,
    DatasetSplitRecord,
    PreparedDatasetRecord,
    PreparedEpochRecord,
)
from fedcampaign_emhi.artifacts.storage import (
    ArtifactLayout,
    build_artifact_layout,
    dataset_directory_stem,
    file_sha256,
    layer_artifact_id,
    payload_digest,
    write_atomic_json,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.datasets.campaigns import build_campaign_registry
from fedcampaign_emhi.datasets.edge_iiotset.canonicalization import (
    normalize_event_type as edge_normalize_event_type,
)
from fedcampaign_emhi.datasets.edge_iiotset.canonicalization import (
    record_enters_epoch_event_count,
)
from fedcampaign_emhi.datasets.edge_iiotset.ground_truth import edge_iiotset_ground_truth
from fedcampaign_emhi.datasets.edge_iiotset.loading import iter_edge_iiotset_csv_entries
from fedcampaign_emhi.datasets.edge_iiotset.validation import (
    adapter_material_code_fingerprint as edge_adapter_material_code_fingerprint,
)
from fedcampaign_emhi.datasets.edge_iiotset.validation import select_secondary_clients
from fedcampaign_emhi.datasets.inventory import (
    configured_raw_directory,
    discover_raw_paths,
    inventory_raw_directory,
)
from fedcampaign_emhi.datasets.partitions import epoch_index
from fedcampaign_emhi.datasets.preprocessing import (
    apply_robust_scaler,
    chronological_benign_partitions,
    chronological_partition_lengths,
    complete_benign_horizons,
    epoch_feature_vector,
    fit_robust_scaler,
    inclusive_epoch_range,
    retain_first_chronological,
)
from fedcampaign_emhi.datasets.ton_iot_network.canonicalization import (
    event_type_hash_bucket as ton_event_type_hash_bucket,
)
from fedcampaign_emhi.datasets.ton_iot_network.canonicalization import (
    normalize_client_id,
)
from fedcampaign_emhi.datasets.ton_iot_network.canonicalization import (
    normalize_event_type as ton_normalize_event_type,
)
from fedcampaign_emhi.datasets.ton_iot_network.ground_truth import ton_iot_network_ground_truth
from fedcampaign_emhi.datasets.ton_iot_network.loading import validate_ton_iot_network_csv_schema
from fedcampaign_emhi.datasets.ton_iot_network.validation import (
    adapter_material_code_fingerprint as ton_adapter_material_code_fingerprint,
)
from fedcampaign_emhi.datasets.ton_iot_network.validation import select_primary_clients_from_tallies
from fedcampaign_emhi.domain.enums import (
    ArtifactLifecycleState,
    ArtifactNamespace,
    DatasetName,
    DownstreamArtifactKind,
    ExperimentState,
    GroundTruthClass,
    OverwritePolicy,
    PreprocessingLayer,
    SupportState,
)
from fedcampaign_emhi.domain.types import (
    ArtifactDependencyNode,
    ArtifactIdentity,
    Boolean,
    ClientBenignTally,
    ClientId,
    ClientMaliciousEpochs,
    ConfigurationDigest,
    EdgeIiotsetFlowRecord,
    EpochIndexValue,
    ExcludedRecord,
    FileInventoryEntry,
    HashBucketCount,
    HashBucketIndex,
    MaterialDependencyFingerprint,
    NormalizedEventToken,
    PreprocessExecutionRecord,
    PreprocessingLayerDecision,
    RecordCount,
    RetainedEvent,
    RobustScaler,
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
    for kind in preprocess_must_not_regenerate():
        downstream_id = downstream_artifact_id(dataset_name, kind)
        nodes.append(
            ArtifactDependencyNode(
                artifact_id=downstream_id,
                material_fingerprint=_structural_fingerprint(downstream_id),
                upstream_ids=(layer_ids[-1],),
            )
        )
    return tuple(nodes)


def nearest_reconstruction_layer(
    reusable: tuple[Boolean, ...], overwrite_policy: OverwritePolicy
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
    reusable = (
        tuple(
            _layer_is_reusable(layout, dataset_name, layer, expected_fingerprints[index])
            for index, layer in enumerate(PREPROCESSING_LAYER_ORDER)
        )
        if raw_inventory
        else (False,) * len(PREPROCESSING_LAYER_ORDER)
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
    materialization = _resolve_materialization(
        loaded,
        repository,
        layout,
        dataset_name,
        raw_directory,
        raw_inventory,
        inventory_digest,
        start_layer,
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
    inventory_identity = payload_digest(cast(YamlNode, {"dataset": dataset_name.value}))
    inventory_fingerprint = material_fingerprint(inventory_identity, (inventory_digest,))
    prepared_configuration = payload_digest(
        cast(
            YamlNode,
            {
                "time": loaded.values.time.model_dump(mode="json"),
                "eligibility": loaded.values.datasets.eligibility.model_dump(mode="json"),
                "preprocessing": loaded.values.datasets.preprocessing.model_dump(mode="json"),
                "dataset": _dataset_configuration_payload(loaded, dataset_name),
            },
        )
    )
    adapter_digest = (
        ton_adapter_material_code_fingerprint()
        if dataset_name is DatasetName.TON_IOT_NETWORK
        else edge_adapter_material_code_fingerprint()
    )
    prepared_fingerprint = material_fingerprint(
        prepared_configuration,
        (
            inventory_fingerprint,
            adapter_digest,
            _layer_code_digest(PreprocessingLayer.PREPARED),
            _layer_code_digest(PreprocessingLayer.SPLITS),
        ),
    )
    split_fingerprint = material_fingerprint(
        prepared_configuration,
        (prepared_fingerprint, _layer_code_digest(PreprocessingLayer.SPLITS)),
    )
    partition_configuration = payload_digest(
        cast(
            YamlNode,
            {"evaluation_horizon_epochs": loaded.values.campaign.evaluation_horizon_epochs},
        )
    )
    partition_fingerprint = material_fingerprint(
        partition_configuration,
        (split_fingerprint, _layer_code_digest(PreprocessingLayer.PARTITIONS)),
    )
    campaign_configuration = payload_digest(
        cast(
            YamlNode,
            {
                "campaign": loaded.values.campaign.model_dump(mode="json"),
                "distributed_support": loaded.values.distributed_support.model_dump(mode="json"),
            },
        )
    )
    campaign_fingerprint = material_fingerprint(
        campaign_configuration,
        (
            prepared_fingerprint,
            split_fingerprint,
            partition_fingerprint,
            _layer_code_digest(PreprocessingLayer.CAMPAIGN_REGISTRY),
        ),
    )
    return (
        inventory_fingerprint,
        prepared_fingerprint,
        split_fingerprint,
        partition_fingerprint,
        campaign_fingerprint,
    )


def _dataset_configuration_payload(
    loaded: LoadedScientificConfiguration, dataset_name: DatasetName
) -> YamlNode:
    if dataset_name is DatasetName.TON_IOT_NETWORK:
        return cast(YamlNode, loaded.values.datasets.primary.model_dump(mode="json"))
    return cast(YamlNode, loaded.values.datasets.secondary.model_dump(mode="json"))


def _layer_code_digest(layer: PreprocessingLayer) -> ConfigurationDigest:
    if layer is PreprocessingLayer.INVENTORY:
        sources = (inspect.getsource(inventory_raw_directory), inspect.getsource(_inventory_record))
    elif layer is PreprocessingLayer.PREPARED:
        sources = (
            inspect.getsource(_deduplicate_ton_records),
            inspect.getsource(_deduplicate_edge_records),
            inspect.getsource(_prepare_ton_epochs_from_csv),
            inspect.getsource(_duckdb_count),
            inspect.getsource(_prepare_ton_epochs),
            inspect.getsource(_prepare_edge_epochs),
            inspect.getsource(_dense_prepared_epochs),
            inspect.getsource(_scale_prepared),
            inspect.getsource(_prepared_epoch),
        )
    elif layer is PreprocessingLayer.SPLITS:
        sources = (inspect.getsource(_split_from_prepared),)
    elif layer is PreprocessingLayer.PARTITIONS:
        sources = (inspect.getsource(_partitions_from_split),)
    else:
        sources = (inspect.getsource(_campaigns_from_prepared),)
    digest = hashlib.sha256()
    for source in sources:
        digest.update(source.encode("utf-8"))
    return digest.hexdigest()


def _layer_is_reusable(
    layout: ArtifactLayout,
    dataset_name: DatasetName,
    layer: PreprocessingLayer,
    expected_fingerprint: MaterialDependencyFingerprint,
) -> Boolean:
    manifest = _read_manifest(layout, dataset_name, layer)
    if manifest is None or manifest.lifecycle_state is not ArtifactLifecycleState.VALID:
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


def _resolve_materialization(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    layout: ArtifactLayout,
    dataset_name: DatasetName,
    raw_directory: Path,
    raw_inventory: tuple[FileInventoryEntry, ...],
    inventory_digest: ConfigurationDigest,
    start_layer: PreprocessingLayer,
) -> DatasetMaterialization:
    inventory = _inventory_record(dataset_name, raw_inventory, inventory_digest)
    start_index = PREPROCESSING_LAYER_ORDER.index(start_layer)
    if start_index <= PREPROCESSING_LAYER_ORDER.index(PreprocessingLayer.PREPARED):
        prepared, split = _build_prepared_and_split(loaded, raw_directory, dataset_name)
    else:
        prepared = _read_prepared(layout, dataset_name)
        split = (
            _split_from_prepared(loaded, prepared)
            if start_index <= PREPROCESSING_LAYER_ORDER.index(PreprocessingLayer.SPLITS)
            else _read_split(layout, dataset_name)
        )
    partitions = (
        _partitions_from_split(loaded, split)
        if start_index <= PREPROCESSING_LAYER_ORDER.index(PreprocessingLayer.PARTITIONS)
        else _read_partitions(layout, dataset_name)
    )
    campaigns = _campaigns_from_prepared(loaded, prepared, split)
    del repository
    return DatasetMaterialization(
        inventory=inventory,
        prepared=prepared,
        split=split,
        partitions=partitions,
        campaigns=campaigns,
    )


def _inventory_record(
    dataset_name: DatasetName,
    inventory_entries: tuple[FileInventoryEntry, ...],
    inventory_digest: ConfigurationDigest,
) -> DatasetInventoryRecord:
    return DatasetInventoryRecord(
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


def _read_prepared(layout: ArtifactLayout, dataset_name: DatasetName) -> PreparedDatasetRecord:
    path = _product_path(layout, dataset_name, PreprocessingLayer.PREPARED)
    return PreparedDatasetRecord.model_validate_json(path.read_bytes())


def _read_split(layout: ArtifactLayout, dataset_name: DatasetName) -> DatasetSplitRecord:
    path = _product_path(layout, dataset_name, PreprocessingLayer.SPLITS)
    return DatasetSplitRecord.model_validate_json(path.read_bytes())


def _read_partitions(layout: ArtifactLayout, dataset_name: DatasetName) -> BenignPartitionRecord:
    path = _product_path(layout, dataset_name, PreprocessingLayer.PARTITIONS)
    return BenignPartitionRecord.model_validate_json(path.read_bytes())


def _csv_paths(raw_directory: Path) -> tuple[Path, ...]:
    return tuple(
        path for path in discover_raw_paths(raw_directory) if path.suffix.lower() == ".csv"
    )


def _load_edge_records(
    raw_directory: Path,
) -> tuple[tuple[EdgeIiotsetFlowRecord, ...], tuple[ExcludedRecord, ...]]:
    records: list[EdgeIiotsetFlowRecord] = []
    exclusions: list[ExcludedRecord] = []
    for path in _csv_paths(raw_directory):
        for entry in iter_edge_iiotset_csv_entries(path):
            if isinstance(entry, ExcludedRecord):
                exclusions.append(entry)
            else:
                records.append(entry)
    return tuple(records), tuple(exclusions)


def _build_prepared_and_split(
    loaded: LoadedScientificConfiguration,
    raw_directory: Path,
    dataset_name: DatasetName,
) -> tuple[PreparedDatasetRecord, DatasetSplitRecord]:
    if dataset_name is DatasetName.TON_IOT_NETWORK:
        _deduplicate_ton_records(())
        prepared = _prepare_ton_epochs_from_csv(loaded, raw_directory)
    else:
        records, exclusions = _load_edge_records(raw_directory)
        records, duplicate_count = _deduplicate_edge_records(records)
        selection = select_secondary_clients(
            records,
            loaded.values.time.real_data_epoch_seconds,
            loaded.values.datasets.eligibility.minimum_benign_event_records,
            loaded.values.datasets.eligibility.minimum_nonempty_benign_epochs,
            loaded.values.datasets.secondary.target_client_count,
            loaded.values.datasets.secondary.minimum_eligible_client_count,
        )
        discrepancy_count = sum(
            1
            for record in records
            if edge_iiotset_ground_truth(record.binary_label, record.attack_type).classification
            is GroundTruthClass.AMBIGUOUS
        )
        prepared = _prepare_edge_epochs(
            loaded,
            records,
            selection.selected_client_ids,
            selection.eligible_client_ids,
            selection.support_state,
            len(exclusions),
            duplicate_count,
            discrepancy_count,
        )
    split = _split_from_prepared(loaded, prepared)
    return _scale_prepared(loaded, prepared, split), split


def _prepare_ton_epochs_from_csv(
    loaded: LoadedScientificConfiguration, raw_directory: Path
) -> PreparedDatasetRecord:
    csv_paths = _csv_paths(raw_directory)
    for path in csv_paths:
        validate_ton_iot_network_csv_schema(path)
    paths = tuple(str(path) for path in csv_paths)
    if not paths:
        return _prepare_ton_epochs(loaded, (), (), (), SupportState.NOT_TESTED, 0, 0, 0)
    epoch_seconds = loaded.values.time.real_data_epoch_seconds
    connection = duckdb.connect(":memory:")
    connection.execute("SET memory_limit='2GB'")
    connection.execute("SET threads=1")
    quoted_paths = ", ".join("'" + path.replace("'", "''") + "'" for path in paths)
    connection.execute(
        "CREATE VIEW raw AS SELECT * FROM read_csv(["
        + quoted_paths
        + "], header=true, all_varchar=true, union_by_name=true)"
    )
    valid = """
        SELECT DISTINCT CAST(ts AS DOUBLE) AS timestamp_seconds, trim(src_ip) AS client_id,
            trim(coalesce(proto, '')) AS protocol_token, trim(coalesce(service, '')) AS service_token,
            CAST(label AS BIGINT) AS binary_label, trim(type) AS attack_type
        FROM raw
        WHERE try_cast(ts AS DOUBLE) IS NOT NULL AND trim(coalesce(src_ip, '')) NOT IN ('', '-')
            AND try_cast(label AS BIGINT) IS NOT NULL AND trim(coalesce(type, '')) <> ''
    """
    valid_rows = valid.replace("SELECT DISTINCT", "SELECT", 1)
    raw_count = _duckdb_count(connection, "SELECT count(*) FROM raw")
    valid_count = _duckdb_count(connection, f"SELECT count(*) FROM ({valid_rows})")
    distinct_count = _duckdb_count(connection, f"SELECT count(*) FROM ({valid})")
    discrepancy_count = _duckdb_count(
        connection,
        f"SELECT count(*) FROM ({valid}) WHERE (binary_label=0 AND lower(attack_type)<>'normal') OR (binary_label=1 AND lower(attack_type)='normal')",
    )
    eligibility_rows = connection.execute(
        f"SELECT client_id, count(*), count(DISTINCT floor(timestamp_seconds / ?)) FROM ({valid}) WHERE binary_label=0 AND lower(attack_type)='normal' GROUP BY client_id",
        [epoch_seconds],
    ).fetchall()
    tallies = tuple(
        ClientBenignTally(row[0], row[1], tuple(range(int(row[2])))) for row in eligibility_rows
    )
    selection = select_primary_clients_from_tallies(
        tallies,
        loaded.values.datasets.eligibility.minimum_benign_event_records,
        loaded.values.datasets.eligibility.minimum_nonempty_benign_epochs,
        loaded.values.datasets.primary.target_client_count,
    )
    bucket_count = loaded.values.datasets.preprocessing.event_type_hash_bucket_count
    counts: MutableMapping[tuple[ClientId, EpochIndexValue], tuple[RecordCount, ...]] = {}
    ambiguous: MutableMapping[tuple[ClientId, EpochIndexValue], RecordCount] = {}
    malicious: MutableMapping[tuple[ClientId, EpochIndexValue], RecordCount] = {}
    if selection.selected_client_ids:
        placeholders = ",".join("?" for _ in selection.selected_client_ids)
        grouped_rows = connection.execute(
            f"SELECT client_id, floor(timestamp_seconds / ?) AS epoch, protocol_token, service_token, binary_label, attack_type, count(*) FROM ({valid}) WHERE client_id IN ({placeholders}) GROUP BY ALL",
            [epoch_seconds, *selection.selected_client_ids],
        ).fetchall()
        for row in grouped_rows:
            key = (row[0], int(row[1]))
            current = counts.get(key, tuple(0 for _index in range(bucket_count)))
            bucket = ton_event_type_hash_bucket(
                ton_normalize_event_type(row[2], row[3]), bucket_count
            )
            count = int(row[6])
            counts[key] = tuple(
                value + count if index == bucket else value for index, value in enumerate(current)
            )
            ground_truth = ton_iot_network_ground_truth(row[4], row[5]).classification
            if ground_truth is GroundTruthClass.AMBIGUOUS:
                ambiguous[key] = ambiguous.get(key, 0) + count
            elif ground_truth is GroundTruthClass.MALICIOUS:
                malicious[key] = malicious.get(key, 0) + count
    epochs = _dense_prepared_epochs(
        DatasetName.TON_IOT_NETWORK,
        selection.selected_client_ids,
        bucket_count,
        counts,
        ambiguous,
        malicious,
    )
    return PreparedDatasetRecord(
        dataset_name=DatasetName.TON_IOT_NETWORK,
        selected_client_ids=selection.selected_client_ids,
        eligible_client_ids=selection.eligible_client_ids,
        selection_support_state=selection.support_state,
        epochs=epochs,
        excluded_record_count=raw_count - valid_count,
        duplicate_record_count=valid_count - distinct_count,
        ground_truth_discrepancy_count=discrepancy_count,
    )


def _duckdb_count(
    connection: duckdb.DuckDBPyConnection, statement: NormalizedEventToken
) -> RecordCount:
    result = connection.execute(statement).fetchone()
    if result is None:
        raise ValueError("DuckDB aggregate query returned no result")
    return int(cast(tuple[int], result)[0])


def _deduplicate_ton_records(
    records: tuple[TonIotNetworkFlowRecord, ...],
) -> tuple[tuple[TonIotNetworkFlowRecord, ...], RecordCount]:
    events = tuple(
        RetainedEvent(
            dataset_name=DatasetName.TON_IOT_NETWORK,
            client_id=normalize_client_id(record.source_ip),
            timestamp_seconds=record.timestamp_seconds,
            event_type=ton_normalize_event_type(record.protocol_token, record.service_token),
            payload=_payload_identity((str(record.binary_label), record.attack_type)),
            unique_identifier=None,
            original_order=index,
        )
        for index, record in enumerate(records)
    )
    outcome = retain_first_chronological(events)
    if outcome.experiment_state is ExperimentState.INVALID:
        raise ValueError("conflicting TON_IoT Network duplicate identifiers are invalid")
    retained_indexes = tuple(event.original_order for event in outcome.retained_events)
    return tuple(records[index] for index in retained_indexes), outcome.duplicate_count


def _deduplicate_edge_records(
    records: tuple[EdgeIiotsetFlowRecord, ...],
) -> tuple[tuple[EdgeIiotsetFlowRecord, ...], RecordCount]:
    events = tuple(
        RetainedEvent(
            dataset_name=DatasetName.EDGE_IIOTSET,
            client_id=record.source_host.strip(),
            timestamp_seconds=record.timestamp_seconds,
            event_type=edge_normalize_event_type(record.protocol_group),
            payload=_payload_identity((str(record.binary_label), record.attack_type)),
            unique_identifier=None,
            original_order=index,
        )
        for index, record in enumerate(records)
    )
    outcome = retain_first_chronological(events)
    if outcome.experiment_state is ExperimentState.INVALID:
        raise ValueError("conflicting Edge-IIoTset duplicate identifiers are invalid")
    retained_indexes = tuple(event.original_order for event in outcome.retained_events)
    return tuple(records[index] for index in retained_indexes), outcome.duplicate_count


def _payload_identity(parts: tuple[NormalizedEventToken, ...]) -> NormalizedEventToken:
    return payload_digest(cast(YamlNode, list(parts)))


def _increment_bucket(
    counts: tuple[RecordCount, ...], bucket_index: HashBucketIndex
) -> tuple[RecordCount, ...]:
    return tuple(
        count + 1 if index == bucket_index else count for index, count in enumerate(counts)
    )


def _prepare_ton_epochs(
    loaded: LoadedScientificConfiguration,
    records: tuple[TonIotNetworkFlowRecord, ...],
    selected_client_ids: tuple[ClientId, ...],
    eligible_client_ids: tuple[ClientId, ...],
    support_state: SupportState,
    excluded_count: RecordCount,
    duplicate_count: RecordCount,
    discrepancy_count: RecordCount,
) -> PreparedDatasetRecord:
    bucket_count = loaded.values.datasets.preprocessing.event_type_hash_bucket_count
    selected = set(selected_client_ids)
    counts: MutableMapping[tuple[ClientId, EpochIndexValue], tuple[RecordCount, ...]] = {}
    ambiguous: MutableMapping[tuple[ClientId, EpochIndexValue], RecordCount] = {}
    malicious: MutableMapping[tuple[ClientId, EpochIndexValue], RecordCount] = {}
    for record in records:
        client_id = normalize_client_id(record.source_ip)
        if client_id not in selected:
            continue
        epoch = epoch_index(
            record.timestamp_seconds, loaded.values.time.real_data_epoch_seconds
        ).index
        key = (client_id, epoch)
        current = counts.get(key, tuple(0 for _index in range(bucket_count)))
        event_type = ton_normalize_event_type(record.protocol_token, record.service_token)
        bucket = ton_event_type_hash_bucket(event_type, bucket_count)
        counts[key] = _increment_bucket(current, bucket)
        ground_truth = ton_iot_network_ground_truth(record.binary_label, record.attack_type)
        if ground_truth.classification is GroundTruthClass.AMBIGUOUS:
            ambiguous[key] = ambiguous.get(key, 0) + 1
        elif ground_truth.classification is GroundTruthClass.MALICIOUS:
            malicious[key] = malicious.get(key, 0) + 1
    epochs = _dense_prepared_epochs(
        DatasetName.TON_IOT_NETWORK,
        selected_client_ids,
        bucket_count,
        counts,
        ambiguous,
        malicious,
    )
    return PreparedDatasetRecord(
        dataset_name=DatasetName.TON_IOT_NETWORK,
        selected_client_ids=selected_client_ids,
        eligible_client_ids=eligible_client_ids,
        selection_support_state=support_state,
        epochs=epochs,
        excluded_record_count=excluded_count,
        duplicate_record_count=duplicate_count,
        ground_truth_discrepancy_count=discrepancy_count,
    )


def _prepare_edge_epochs(
    loaded: LoadedScientificConfiguration,
    records: tuple[EdgeIiotsetFlowRecord, ...],
    selected_client_ids: tuple[ClientId, ...],
    eligible_client_ids: tuple[ClientId, ...],
    support_state: SupportState,
    excluded_count: RecordCount,
    duplicate_count: RecordCount,
    discrepancy_count: RecordCount,
) -> PreparedDatasetRecord:
    bucket_count = loaded.values.datasets.preprocessing.event_type_hash_bucket_count
    selected = set(selected_client_ids)
    counts: MutableMapping[tuple[ClientId, EpochIndexValue], tuple[RecordCount, ...]] = {}
    ambiguous: MutableMapping[tuple[ClientId, EpochIndexValue], RecordCount] = {}
    malicious: MutableMapping[tuple[ClientId, EpochIndexValue], RecordCount] = {}
    for record in records:
        client_id = record.source_host.strip()
        if client_id not in selected:
            continue
        epoch = epoch_index(
            record.timestamp_seconds, loaded.values.time.real_data_epoch_seconds
        ).index
        key = (client_id, epoch)
        current = counts.get(key, tuple(0 for _index in range(bucket_count)))
        if record_enters_epoch_event_count(record.protocol_group):
            event_type = edge_normalize_event_type(record.protocol_group)
            bucket = ton_event_type_hash_bucket(event_type, bucket_count)
            counts[key] = _increment_bucket(current, bucket)
        else:
            counts[key] = current
        ground_truth = edge_iiotset_ground_truth(record.binary_label, record.attack_type)
        if ground_truth.classification is GroundTruthClass.AMBIGUOUS:
            ambiguous[key] = ambiguous.get(key, 0) + 1
        elif ground_truth.classification is GroundTruthClass.MALICIOUS:
            malicious[key] = malicious.get(key, 0) + 1
    epochs = _dense_prepared_epochs(
        DatasetName.EDGE_IIOTSET,
        selected_client_ids,
        bucket_count,
        counts,
        ambiguous,
        malicious,
    )
    return PreparedDatasetRecord(
        dataset_name=DatasetName.EDGE_IIOTSET,
        selected_client_ids=selected_client_ids,
        eligible_client_ids=eligible_client_ids,
        selection_support_state=support_state,
        epochs=epochs,
        excluded_record_count=excluded_count,
        duplicate_record_count=duplicate_count,
        ground_truth_discrepancy_count=discrepancy_count,
    )


def _dense_prepared_epochs(
    dataset_name: DatasetName,
    selected_client_ids: tuple[ClientId, ...],
    bucket_count: HashBucketCount,
    counts: MutableMapping[tuple[ClientId, EpochIndexValue], tuple[RecordCount, ...]],
    ambiguous: MutableMapping[tuple[ClientId, EpochIndexValue], RecordCount],
    malicious: MutableMapping[tuple[ClientId, EpochIndexValue], RecordCount],
) -> tuple[PreparedEpochRecord, ...]:
    rows: list[PreparedEpochRecord] = []
    zero_counts = tuple(0 for _index in range(bucket_count))
    for client_id in selected_client_ids:
        observed = tuple(
            epoch for candidate_client, epoch in counts if candidate_client == client_id
        )
        if not observed:
            continue
        for epoch in inclusive_epoch_range(min(observed), max(observed)):
            bucket_counts = counts.get((client_id, epoch), zero_counts)
            rows.append(
                _prepared_epoch(
                    dataset_name,
                    client_id,
                    epoch,
                    bucket_counts,
                    ambiguous.get((client_id, epoch), 0),
                    malicious.get((client_id, epoch), 0),
                )
            )
    return tuple(rows)


def _prepared_epoch(
    dataset_name: DatasetName,
    client_id: ClientId,
    epoch: EpochIndexValue,
    bucket_counts: tuple[RecordCount, ...],
    ambiguous_count: RecordCount,
    malicious_count: RecordCount,
) -> PreparedEpochRecord:
    vector = epoch_feature_vector(bucket_counts)
    unscaled = (
        *vector.log1p_bucket_counts,
        float(vector.total_raw_event_count),
        vector.shannon_entropy,
    )
    ground_truth = GroundTruthClass.BENIGN
    if ambiguous_count > 0:
        ground_truth = GroundTruthClass.AMBIGUOUS
    if malicious_count > 0:
        ground_truth = GroundTruthClass.MALICIOUS
    return PreparedEpochRecord(
        dataset_name=dataset_name,
        client_id=client_id,
        epoch_index=epoch,
        unscaled_feature_values=unscaled,
        feature_values=unscaled,
        ground_truth=ground_truth,
        raw_event_count=vector.total_raw_event_count,
        ambiguous_event_count=ambiguous_count,
    )


def _split_from_prepared(
    loaded: LoadedScientificConfiguration, prepared: PreparedDatasetRecord
) -> DatasetSplitRecord:
    selected_client_ids = prepared.selected_client_ids
    if not selected_client_ids:
        return _empty_split(prepared)
    starts: list[EpochIndexValue] = []
    benign_ends: list[EpochIndexValue] = []
    for client_id in selected_client_ids:
        client_rows = tuple(row for row in prepared.epochs if row.client_id == client_id)
        if not client_rows:
            return _empty_split(prepared)
        starts.append(min(row.epoch_index for row in client_rows))
        non_benign = tuple(
            row.epoch_index
            for row in client_rows
            if row.ground_truth is not GroundTruthClass.BENIGN
        )
        observed_end = max(row.epoch_index for row in client_rows)
        benign_ends.append(min(non_benign) - 1 if non_benign else observed_end)
    common_epochs = inclusive_epoch_range(max(starts), min(benign_ends))
    if not common_epochs:
        return _empty_split(prepared)
    fractions = loaded.values.datasets.preprocessing.benign_partition_fractions
    lengths = chronological_partition_lengths(
        len(common_epochs),
        fractions.detector_fit,
        fractions.nuisance_fit,
        fractions.threshold_and_policy_calibration,
    )
    partitions = chronological_benign_partitions(common_epochs, lengths)
    support_state = prepared.selection_support_state
    if not partitions.detector_fit or not partitions.nuisance_fit:
        support_state = SupportState.NOT_TESTED
    return DatasetSplitRecord(
        dataset_name=prepared.dataset_name,
        selected_client_ids=selected_client_ids,
        eligible_client_ids=prepared.eligible_client_ids,
        support_state=support_state,
        detector_fit_epochs=partitions.detector_fit,
        nuisance_fit_epochs=partitions.nuisance_fit,
        threshold_calibration_epochs=partitions.threshold_and_policy_calibration,
        heldout_benign_epochs=partitions.heldout_benign,
    )


def _empty_split(prepared: PreparedDatasetRecord) -> DatasetSplitRecord:
    return DatasetSplitRecord(
        dataset_name=prepared.dataset_name,
        selected_client_ids=prepared.selected_client_ids,
        eligible_client_ids=prepared.eligible_client_ids,
        support_state=SupportState.NOT_TESTED,
        detector_fit_epochs=(),
        nuisance_fit_epochs=(),
        threshold_calibration_epochs=(),
        heldout_benign_epochs=(),
    )


def _scale_prepared(
    loaded: LoadedScientificConfiguration,
    prepared: PreparedDatasetRecord,
    split: DatasetSplitRecord,
) -> PreparedDatasetRecord:
    if not split.detector_fit_epochs:
        return prepared
    floor = loaded.values.datasets.preprocessing.robust_scaling_iqr_floor
    scaled_rows: list[PreparedEpochRecord] = []
    scaler_records: list[ClientFeatureScalerRecord] = []
    for client_id in prepared.selected_client_ids:
        client_rows = tuple(row for row in prepared.epochs if row.client_id == client_id)
        fit_rows = tuple(
            row.unscaled_feature_values
            for row in client_rows
            if row.epoch_index in split.detector_fit_epochs
        )
        if not fit_rows:
            return prepared
        feature_count = len(fit_rows[0])
        scalers: tuple[RobustScaler, ...] = tuple(
            fit_robust_scaler(tuple(row[index] for row in fit_rows), floor)
            for index in range(feature_count)
        )
        scaler_records.append(
            ClientFeatureScalerRecord(
                client_id=client_id,
                medians=tuple(scaler.median for scaler in scalers),
                iqrs=tuple(scaler.iqr for scaler in scalers),
                iqr_floor=floor,
            )
        )
        for row in client_rows:
            scaled = tuple(
                apply_robust_scaler(scaler, (value,))[0]
                for scaler, value in zip(scalers, row.unscaled_feature_values, strict=True)
            )
            scaled_rows.append(
                PreparedEpochRecord(
                    dataset_name=row.dataset_name,
                    client_id=row.client_id,
                    epoch_index=row.epoch_index,
                    unscaled_feature_values=row.unscaled_feature_values,
                    feature_values=scaled,
                    ground_truth=row.ground_truth,
                    raw_event_count=row.raw_event_count,
                    ambiguous_event_count=row.ambiguous_event_count,
                )
            )
    return PreparedDatasetRecord(
        dataset_name=prepared.dataset_name,
        selected_client_ids=prepared.selected_client_ids,
        eligible_client_ids=prepared.eligible_client_ids,
        selection_support_state=prepared.selection_support_state,
        epochs=tuple(sorted(scaled_rows, key=lambda row: (row.client_id, row.epoch_index))),
        client_scalers=tuple(scaler_records),
        excluded_record_count=prepared.excluded_record_count,
        duplicate_record_count=prepared.duplicate_record_count,
        ground_truth_discrepancy_count=prepared.ground_truth_discrepancy_count,
    )


def _partitions_from_split(
    loaded: LoadedScientificConfiguration, split: DatasetSplitRecord
) -> BenignPartitionRecord:
    horizon_length = loaded.values.campaign.evaluation_horizon_epochs
    calibration_horizons = complete_benign_horizons(
        split.threshold_calibration_epochs, horizon_length
    )
    heldout_horizons = complete_benign_horizons(split.heldout_benign_epochs, horizon_length)
    return BenignPartitionRecord(
        dataset_name=split.dataset_name,
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
    )


def _campaigns_from_prepared(
    loaded: LoadedScientificConfiguration,
    prepared: PreparedDatasetRecord,
    split: DatasetSplitRecord,
) -> CampaignRegistryRecord:
    malicious_epochs = tuple(
        ClientMaliciousEpochs(
            client_id=client_id,
            malicious_epochs=tuple(
                row.epoch_index
                for row in prepared.epochs
                if row.client_id == client_id and row.ground_truth is GroundTruthClass.MALICIOUS
            ),
        )
        for client_id in split.selected_client_ids
    )
    registry = build_campaign_registry(
        prepared.dataset_name,
        split.selected_client_ids,
        malicious_epochs,
        loaded.values.campaign.merge_max_intervening_benign_epochs,
        loaded.values.distributed_support.minimum_clients,
        loaded.values.campaign.distributed_first_activity_window_epochs,
        loaded.values.campaign.minimum_duration_epochs,
        loaded.values.campaign.prestart_warmup_epochs,
    )
    for entry in registry:
        if entry.duration_epochs != entry.end_epoch - entry.start_epoch + 1:
            raise ValueError("campaign duration must equal the inclusive epoch span")
    return CampaignRegistryRecord(
        dataset_name=prepared.dataset_name,
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
    reconstructed_and_changed: Boolean,
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


def _is_protected_downstream(dataset_name: DatasetName, artifact_id: ArtifactIdentity) -> Boolean:
    return any(
        artifact_id == downstream_artifact_id(dataset_name, kind)
        for kind in preprocess_must_not_regenerate()
    )
