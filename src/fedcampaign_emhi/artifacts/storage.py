import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from fedcampaign_emhi.artifacts.records import ArtifactManifest
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import (
    ArtifactFilenamePattern,
    ArtifactFileSuffix,
    ArtifactIdentityKind,
    ArtifactLifecycleState,
    ArtifactNamespace,
    ArtifactPathSegment,
    DatasetName,
    ExperimentName,
    MethodName,
    PreprocessingLayer,
)
from fedcampaign_emhi.domain.types import (
    ArtifactIdentity,
    ArtifactRoots,
    ConfigurationDigest,
    DeterministicUtf8Bytes,
    FigureBytes,
    MaterialDependencyFingerprint,
    RelativePath,
    SeedValue,
)
from fedcampaign_emhi.runtime import deterministic_digest, deterministic_utf8_bytes

OUTPUTS_PREPROCESSING_CHILDREN = (
    ArtifactPathSegment.INVENTORIES,
    ArtifactPathSegment.VALIDATION,
    ArtifactPathSegment.PREPARED,
    ArtifactPathSegment.SPLITS,
    ArtifactPathSegment.FEATURES,
    ArtifactPathSegment.METADATA,
)


def dataset_directory_stem(dataset_name: DatasetName) -> ArtifactIdentity:
    return dataset_name.replace(" ", "_")


def layer_artifact_id(dataset_name: DatasetName, layer: PreprocessingLayer) -> ArtifactIdentity:
    return f"{ArtifactIdentityKind.PREPROCESS}.{dataset_directory_stem(dataset_name)}.{layer}"


def method_artifact_stem(method_name: MethodName) -> RelativePath:
    return method_name.value.lower().replace(" ", "-").replace("≤", "at-most-").replace("_", "-")


def detector_score_artifact_id(dataset_name: DatasetName, root_seed: SeedValue) -> ArtifactIdentity:
    return f"{ArtifactIdentityKind.DETECTOR_SCORES}.{dataset_directory_stem(dataset_name)}.seed-{root_seed}"


def marginal_rank_artifact_id(dataset_name: DatasetName, root_seed: SeedValue) -> ArtifactIdentity:
    return f"{ArtifactIdentityKind.MARGINAL_RANKS}.{dataset_directory_stem(dataset_name)}.seed-{root_seed}"


def emhi_fit_artifact_id(
    dataset_name: DatasetName, root_seed: SeedValue, method_name: MethodName
) -> ArtifactIdentity:
    return f"{ArtifactIdentityKind.EMHI_FIT}.{dataset_directory_stem(dataset_name)}.seed-{root_seed}.{method_artifact_stem(method_name)}"


def detector_score_artifact_path(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    root_seed: SeedValue,
) -> Path:
    layout = build_artifact_layout(loaded, repository)
    return (
        layout.roots.outputs_root
        / ArtifactPathSegment.ARTIFACTS
        / ArtifactPathSegment.SCORES
        / dataset_directory_stem(dataset_name)
        / ArtifactFilenamePattern.SEEDED_JSON.format(seed=root_seed)
    )


def marginal_rank_artifact_path(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    root_seed: SeedValue,
) -> Path:
    layout = build_artifact_layout(loaded, repository)
    return (
        layout.roots.outputs_root
        / ArtifactPathSegment.ARTIFACTS
        / ArtifactPathSegment.FITTED
        / dataset_directory_stem(dataset_name)
        / ArtifactFilenamePattern.SEEDED_MARGINAL_RANKS_JSON.format(seed=root_seed)
    )


def emhi_fit_artifact_path(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    root_seed: SeedValue,
    method_name: MethodName,
) -> Path:
    layout = build_artifact_layout(loaded, repository)
    return (
        layout.roots.outputs_root
        / ArtifactPathSegment.ARTIFACTS
        / ArtifactPathSegment.FITTED
        / dataset_directory_stem(dataset_name)
        / ArtifactFilenamePattern.SEEDED_DIRECTORY.format(seed=root_seed)
        / ArtifactFilenamePattern.METHOD_JSON.format(method=method_artifact_stem(method_name))
    )


OUTPUTS_ARTIFACT_CHILDREN = (
    ArtifactPathSegment.MODELS,
    ArtifactPathSegment.SCORES,
    ArtifactPathSegment.FITTED,
    ArtifactPathSegment.BASELINES,
    ArtifactPathSegment.DERIVED,
)
OUTPUTS_CACHE_CHILDREN = (
    ArtifactPathSegment.PREPROCESSING,
    ArtifactPathSegment.MODELS,
    ArtifactPathSegment.EVALUATION,
    ArtifactPathSegment.ANALYSIS,
    ArtifactPathSegment.STAGING,
)
EXPERIMENT_OUTPUT_TREES = {
    ArtifactPathSegment.ARTIFACTS: (
        ArtifactPathSegment.FITTED,
        ArtifactPathSegment.PREDICTIONS,
        ArtifactPathSegment.DERIVED,
    ),
    ArtifactPathSegment.EVALUATIONS: (
        ArtifactPathSegment.RECORDS,
        ArtifactPathSegment.COMPARISONS,
        ArtifactPathSegment.AGGREGATES,
    ),
    ArtifactPathSegment.METRICS: (
        ArtifactPathSegment.PER_SEED,
        ArtifactPathSegment.PER_CONDITION,
        ArtifactPathSegment.AGGREGATE,
    ),
    ArtifactPathSegment.STATISTICS: (
        ArtifactPathSegment.TESTS,
        ArtifactPathSegment.CONFIDENCE_INTERVALS,
        ArtifactPathSegment.EFFECTS,
        ArtifactPathSegment.MULTIPLICITY,
    ),
    ArtifactPathSegment.CHECKPOINTS: (ArtifactPathSegment.TRAINING, ArtifactPathSegment.EXECUTION),
    ArtifactPathSegment.DIAGNOSTICS: (
        ArtifactPathSegment.SCIENTIFIC,
        ArtifactPathSegment.NUMERICAL,
        ArtifactPathSegment.RUNTIME,
    ),
    ArtifactPathSegment.LOGS: (ArtifactPathSegment.EXECUTION, ArtifactPathSegment.FAILURES),
    ArtifactPathSegment.FIGURES: (ArtifactPathSegment.MAIN, ArtifactPathSegment.SUPPLEMENTARY),
    ArtifactPathSegment.TABLES: (ArtifactPathSegment.MAIN, ArtifactPathSegment.SUPPLEMENTARY),
    ArtifactPathSegment.SOURCE_DATA: (ArtifactPathSegment.FIGURES, ArtifactPathSegment.TABLES),
    ArtifactPathSegment.PROVENANCE: (
        ArtifactPathSegment.CONFIGURATION,
        ArtifactPathSegment.DATA,
        ArtifactPathSegment.SEEDS,
        ArtifactPathSegment.ENVIRONMENT,
        ArtifactPathSegment.DEPENDENCIES,
    ),
}
EXPERIMENT_RESULTS_TREES = {
    ArtifactPathSegment.FIGURES: (ArtifactPathSegment.MAIN, ArtifactPathSegment.SUPPLEMENTARY),
    ArtifactPathSegment.TABLES: (ArtifactPathSegment.MAIN, ArtifactPathSegment.SUPPLEMENTARY),
    ArtifactPathSegment.METRICS: (
        ArtifactPathSegment.PRIMARY,
        ArtifactPathSegment.SECONDARY,
        ArtifactPathSegment.SUMMARY,
    ),
    ArtifactPathSegment.STATISTICS: (
        ArtifactPathSegment.TESTS,
        ArtifactPathSegment.CONFIDENCE_INTERVALS,
        ArtifactPathSegment.EFFECTS,
        ArtifactPathSegment.MULTIPLICITY,
    ),
    ArtifactPathSegment.SOURCE_DATA: (ArtifactPathSegment.FIGURES, ArtifactPathSegment.TABLES),
}
PROJECT_SUMMARY_TREES = {
    ArtifactPathSegment.FIGURES: (ArtifactPathSegment.MAIN, ArtifactPathSegment.SUPPLEMENTARY),
    ArtifactPathSegment.TABLES: (ArtifactPathSegment.MAIN, ArtifactPathSegment.SUPPLEMENTARY),
    ArtifactPathSegment.METRICS: (ArtifactPathSegment.PRIMARY, ArtifactPathSegment.SUMMARY),
    ArtifactPathSegment.STATISTICS: (
        ArtifactPathSegment.COMPARISONS,
        ArtifactPathSegment.CONFIDENCE_INTERVALS,
        ArtifactPathSegment.EFFECTS,
        ArtifactPathSegment.MULTIPLICITY,
    ),
    ArtifactPathSegment.SOURCE_DATA: (ArtifactPathSegment.FIGURES, ArtifactPathSegment.TABLES),
    ArtifactPathSegment.REPRODUCIBILITY: (
        ArtifactPathSegment.CONFIGURATION,
        ArtifactPathSegment.DATASETS,
        ArtifactPathSegment.SEEDS,
        ArtifactPathSegment.SOFTWARE,
        ArtifactPathSegment.EXECUTION,
    ),
}


@dataclass(frozen=True)
class ArtifactLayout:
    roots: ArtifactRoots

    def experiment_outputs_root(self, experiment_name: ExperimentName) -> Path:
        return self.roots.outputs_root / ArtifactPathSegment.EXPERIMENTS / experiment_name

    def experiment_results_root(self, experiment_name: ExperimentName) -> Path:
        return self.roots.results_root / ArtifactPathSegment.EXPERIMENTS / experiment_name

    def required_directories(self) -> tuple[Path, ...]:
        outputs_root = self.roots.namespace_root(ArtifactNamespace.OUTPUTS)
        results_root = self.roots.namespace_root(ArtifactNamespace.RESULTS)
        paths: list[Path] = [
            outputs_root,
            results_root,
            outputs_root / ArtifactPathSegment.PREPROCESSING,
            outputs_root / ArtifactPathSegment.ARTIFACTS,
            outputs_root / ArtifactPathSegment.EXPERIMENTS,
            outputs_root / ArtifactPathSegment.CACHE,
            results_root / ArtifactPathSegment.EXPERIMENTS,
            results_root / ArtifactPathSegment.PROJECT_SUMMARY,
        ]
        paths.extend(
            _child_directories(
                outputs_root / ArtifactPathSegment.PREPROCESSING,
                OUTPUTS_PREPROCESSING_CHILDREN,
            )
        )
        paths.extend(
            _child_directories(
                outputs_root / ArtifactPathSegment.ARTIFACTS, OUTPUTS_ARTIFACT_CHILDREN
            )
        )
        paths.extend(
            _child_directories(outputs_root / ArtifactPathSegment.CACHE, OUTPUTS_CACHE_CHILDREN)
        )
        for experiment_name in ExperimentName:
            experiment_output = self.experiment_outputs_root(experiment_name)
            paths.append(experiment_output)
            paths.extend(_nested_directories(experiment_output, EXPERIMENT_OUTPUT_TREES))
            experiment_result = self.experiment_results_root(experiment_name)
            paths.append(experiment_result)
            paths.extend(_nested_directories(experiment_result, EXPERIMENT_RESULTS_TREES))
        paths.extend(
            _nested_directories(
                results_root / ArtifactPathSegment.PROJECT_SUMMARY, PROJECT_SUMMARY_TREES
            )
        )
        return tuple(paths)


def _child_directories(parent: Path, children: tuple[ArtifactPathSegment, ...]) -> tuple[Path, ...]:
    return tuple(parent / child for child in children)


def _nested_directories(
    root: Path, tree: Mapping[ArtifactPathSegment, tuple[ArtifactPathSegment, ...]]
) -> tuple[Path, ...]:
    paths: list[Path] = []
    for parent, children in tree.items():
        parent_path = root / parent
        paths.append(parent_path)
        paths.extend(parent_path / child for child in children)
    return tuple(paths)


def build_artifact_layout(
    loaded: LoadedScientificConfiguration, repository: Path
) -> ArtifactLayout:
    roots = ArtifactRoots(
        outputs_root=(repository / loaded.values.artifacts.outputs_root).resolve(),
        results_root=(repository / loaded.values.artifacts.results_root).resolve(),
    )
    return ArtifactLayout(roots=roots)


def encode_deterministic_payload(payload: YamlNode) -> DeterministicUtf8Bytes:
    return deterministic_utf8_bytes(payload)


def payload_digest(payload: YamlNode) -> ConfigurationDigest:
    return deterministic_digest(payload)


def file_sha256(path: Path) -> ConfigurationDigest:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def write_atomic_json(
    destination: Path, payload: YamlNode, staging_directory: Path
) -> ConfigurationDigest:
    staging_directory.mkdir(parents=True, exist_ok=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    encoded = encode_deterministic_payload(payload)
    digest = hashlib.sha256(encoded).hexdigest()
    staging_path = staging_directory / f"{destination.name}.{digest}.partial"
    staging_path.write_bytes(encoded)
    staging_path.replace(destination)
    return digest


def write_atomic_bytes(
    destination: Path, payload: DeterministicUtf8Bytes | FigureBytes, staging_directory: Path
) -> ConfigurationDigest:
    staging_directory.mkdir(parents=True, exist_ok=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(payload).hexdigest()
    staging_path = staging_directory / f"{destination.name}.{digest}.partial"
    staging_path.write_bytes(payload)
    staging_path.replace(destination)
    return digest


def write_artifact_manifest(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    destination: Path,
    artifact_id: ArtifactIdentity,
    content_digest: ConfigurationDigest,
    fingerprint: MaterialDependencyFingerprint,
    upstream_ids: tuple[ArtifactIdentity, ...],
) -> None:
    layout = build_artifact_layout(loaded, repository)
    manifest = ArtifactManifest(
        artifact_id=artifact_id,
        namespace=ArtifactNamespace.OUTPUTS,
        experiment_name=None,
        relative_path=destination.relative_to(layout.roots.outputs_root).as_posix(),
        content_digest=content_digest,
        material_fingerprint=fingerprint,
        upstream_ids=upstream_ids,
        lifecycle_state=ArtifactLifecycleState.VALID,
    )
    write_atomic_json(
        destination.with_suffix(ArtifactFileSuffix.MANIFEST_JSON),
        manifest.model_dump(mode="json"),
        layout.roots.outputs_root / ArtifactPathSegment.CACHE / ArtifactPathSegment.STAGING,
    )
