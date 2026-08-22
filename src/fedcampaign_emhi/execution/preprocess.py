import hashlib
from pathlib import Path

from fedcampaign_emhi.artifacts.dependencies import descendant_ids
from fedcampaign_emhi.artifacts.paths import ArtifactLayout, build_artifact_layout
from fedcampaign_emhi.artifacts.provenance import material_fingerprint
from fedcampaign_emhi.artifacts.records import ArtifactManifest
from fedcampaign_emhi.artifacts.storage import payload_digest, write_atomic_json
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.datasets.inventory import configured_raw_directory, inventory_raw_directory
from fedcampaign_emhi.domain.enums import (
    ArtifactLifecycleState,
    ArtifactNamespace,
    DatasetName,
    DownstreamArtifactKind,
    OverwritePolicy,
    PreprocessingLayer,
)
from fedcampaign_emhi.domain.types import (
    ArtifactDependencyNode,
    ArtifactIdentity,
    ConfigurationDigest,
    MaterialDependencyFingerprint,
    PreprocessExecutionRecord,
    PreprocessingLayerDecision,
)

PREPROCESSING_LAYER_ORDER: tuple[PreprocessingLayer, ...] = (
    PreprocessingLayer.INVENTORY,
    PreprocessingLayer.PREPARED,
    PreprocessingLayer.SPLITS,
    PreprocessingLayer.PARTITIONS,
    PreprocessingLayer.CAMPAIGN_REGISTRY,
)


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
        upstream = () if index == 0 else (layer_ids[index - 1],)
        nodes.append(
            ArtifactDependencyNode(
                artifact_id=artifact_id,
                material_fingerprint=_structural_fingerprint(artifact_id),
                upstream_ids=upstream,
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
    reconstruct_from: list[tuple[DatasetName, PreprocessingLayer | None]] = []
    for name in datasets:
        start_layer, dataset_decisions = _execute_dataset(
            loaded, repository, name, overwrite_policy
        )
        reconstruct_from.append((name, start_layer))
        decisions.extend(dataset_decisions)
    return PreprocessExecutionRecord(
        decisions=tuple(decisions),
        requested_datasets=datasets,
        reconstruct_from=tuple(reconstruct_from),
    )


def _execute_dataset(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    overwrite_policy: OverwritePolicy,
) -> tuple[PreprocessingLayer | None, tuple[PreprocessingLayerDecision, ...]]:
    layout = build_artifact_layout(loaded, repository)
    reusable_flags: list[bool] = []
    stored_fingerprints: tuple[MaterialDependencyFingerprint | None, ...] = ()
    for layer in PREPROCESSING_LAYER_ORDER:
        stored = _read_stored_fingerprint(layout, dataset_name, layer)
        stored_fingerprints = (*stored_fingerprints, stored)
        current = _layer_fingerprint(loaded, repository, dataset_name, layer, stored_fingerprints)
        reusable_flags.append(stored is not None and stored == current)
    start_layer = nearest_reconstruction_layer(tuple(reusable_flags), overwrite_policy)
    decisions: list[PreprocessingLayerDecision] = []
    ancestor_changed = False
    for index, layer in enumerate(PREPROCESSING_LAYER_ORDER):
        previous = stored_fingerprints[index]
        current = _layer_fingerprint(loaded, repository, dataset_name, layer, stored_fingerprints)
        must_rebuild = start_layer is not None and (
            ancestor_changed or _layer_at_or_after(layer, start_layer)
        )
        if overwrite_policy is OverwritePolicy.OVERWRITE:
            must_rebuild = True
        reused = (not must_rebuild) and reusable_flags[index]
        reconstructed = not reused
        if reconstructed:
            current = _materialize_layer(
                loaded, repository, dataset_name, layer, stored_fingerprints
            )
            stored_fingerprints = (
                *stored_fingerprints[:index],
                current,
                *stored_fingerprints[index + 1 :],
            )
            if previous is not None and previous != current:
                ancestor_changed = True
            elif previous == current:
                ancestor_changed = False
        invalidated: tuple[ArtifactIdentity, ...] = ()
        if reconstructed and previous is not None and previous != current:
            invalidated = tuple(
                artifact_id
                for artifact_id in descendant_ids(
                    preprocessing_dependency_graph(dataset_name),
                    (layer_artifact_id(dataset_name, layer),),
                )
                if _is_protected_downstream(dataset_name, artifact_id)
            )
        if reconstructed and previous is None:
            ancestor_changed = True
        decisions.append(
            PreprocessingLayerDecision(
                dataset_name=dataset_name,
                layer=layer,
                reused=reused,
                reconstructed=reconstructed,
                previous_fingerprint=previous,
                current_fingerprint=current,
                invalidated_descendant_ids=invalidated,
            )
        )
    return start_layer, tuple(decisions)


def _layer_at_or_after(layer: PreprocessingLayer, start: PreprocessingLayer) -> bool:
    return PREPROCESSING_LAYER_ORDER.index(layer) >= PREPROCESSING_LAYER_ORDER.index(start)


def _structural_fingerprint(artifact_id: ArtifactIdentity) -> MaterialDependencyFingerprint:
    return hashlib.sha256(artifact_id.encode("utf-8")).hexdigest()


def _is_protected_downstream(dataset_name: DatasetName, artifact_id: ArtifactIdentity) -> bool:
    return any(
        artifact_id == downstream_artifact_id(dataset_name, kind)
        for kind in preprocess_must_not_regenerate()
    )


def _layer_path(
    layout: ArtifactLayout, dataset_name: DatasetName, layer: PreprocessingLayer
) -> Path:
    return (
        layout.roots.outputs_root
        / "preprocessing"
        / dataset_directory_stem(dataset_name)
        / f"{layer.value}.json"
    )


def _read_stored_fingerprint(
    layout: ArtifactLayout, dataset_name: DatasetName, layer: PreprocessingLayer
) -> MaterialDependencyFingerprint | None:
    path = _layer_path(layout, dataset_name, layer)
    if not path.is_file():
        return None
    manifest = ArtifactManifest.model_validate_json(path.read_bytes())
    return manifest.material_fingerprint


def _layer_fingerprint(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    layer: PreprocessingLayer,
    stored_fingerprints: tuple[MaterialDependencyFingerprint | None, ...],
) -> MaterialDependencyFingerprint:
    payload = _layer_payload(loaded, repository, dataset_name, layer, stored_fingerprints)
    content = payload_digest(payload)
    upstream = _upstream_digest(layer, stored_fingerprints)
    upstreams = () if upstream is None else (upstream,)
    return material_fingerprint(loaded.material_digest, (*upstreams, content))


def _upstream_digest(
    layer: PreprocessingLayer,
    stored_fingerprints: tuple[MaterialDependencyFingerprint | None, ...],
) -> ConfigurationDigest | None:
    index = PREPROCESSING_LAYER_ORDER.index(layer)
    if index == 0:
        return None
    return stored_fingerprints[index - 1]


def _layer_payload(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    layer: PreprocessingLayer,
    stored_fingerprints: tuple[MaterialDependencyFingerprint | None, ...],
) -> YamlNode:
    raw_directory = configured_raw_directory(loaded, dataset_name, repository)
    files = inventory_raw_directory(raw_directory, repository)
    payload: YamlNode = {
        "dataset": dataset_name.value,
        "layer": layer.value,
        "configuration_digest": loaded.material_digest,
        "file_sha256": [entry.sha256 for entry in files],
        "file_paths": [entry.relative_path for entry in files],
        "upstream": _upstream_digest(layer, stored_fingerprints),
    }
    return payload


def _materialize_layer(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    layer: PreprocessingLayer,
    stored_fingerprints: tuple[MaterialDependencyFingerprint | None, ...],
) -> MaterialDependencyFingerprint:
    layout = build_artifact_layout(loaded, repository)
    payload = _layer_payload(loaded, repository, dataset_name, layer, stored_fingerprints)
    content = payload_digest(payload)
    fingerprint = _layer_fingerprint(loaded, repository, dataset_name, layer, stored_fingerprints)
    relative = (
        Path("preprocessing") / dataset_directory_stem(dataset_name) / f"{layer.value}.json"
    ).as_posix()
    manifest = ArtifactManifest(
        artifact_id=layer_artifact_id(dataset_name, layer),
        namespace=ArtifactNamespace.OUTPUTS,
        experiment_name=None,
        relative_path=relative,
        content_digest=content,
        material_fingerprint=fingerprint,
        upstream_ids=()
        if _upstream_digest(layer, stored_fingerprints) is None
        else (
            layer_artifact_id(
                dataset_name, PREPROCESSING_LAYER_ORDER[PREPROCESSING_LAYER_ORDER.index(layer) - 1]
            ),
        ),
        lifecycle_state=ArtifactLifecycleState.VALID,
    )
    destination = _layer_path(layout, dataset_name, layer)
    staging = layout.roots.outputs_root / "cache" / "staging"
    write_atomic_json(destination, manifest.model_dump(mode="json"), staging)
    return fingerprint
