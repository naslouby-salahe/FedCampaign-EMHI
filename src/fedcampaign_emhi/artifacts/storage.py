import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from fedcampaign_emhi.artifacts.records import ArtifactManifest
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import (
    ArtifactLifecycleState,
    ArtifactNamespace,
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
    MaterialDependencyFingerprint,
    RelativePath,
    SeedValue,
)
from fedcampaign_emhi.runtime import deterministic_digest, deterministic_utf8_bytes

OUTPUTS_PREPROCESSING_CHILDREN = (
    "inventories",
    "validation",
    "prepared",
    "splits",
    "features",
    "metadata",
)


def dataset_directory_stem(dataset_name: DatasetName) -> ArtifactIdentity:
    return dataset_name.value.replace(" ", "_")


def layer_artifact_id(dataset_name: DatasetName, layer: PreprocessingLayer) -> ArtifactIdentity:
    return f"preprocess.{dataset_directory_stem(dataset_name)}.{layer.value}"


def method_artifact_stem(method_name: MethodName) -> RelativePath:
    return method_name.value.lower().replace(" ", "-").replace("≤", "at-most-").replace("_", "-")


def detector_score_artifact_id(dataset_name: DatasetName, root_seed: SeedValue) -> ArtifactIdentity:
    return f"detector-scores.{dataset_directory_stem(dataset_name)}.seed-{root_seed}"


def marginal_rank_artifact_id(dataset_name: DatasetName, root_seed: SeedValue) -> ArtifactIdentity:
    return f"marginal-ranks.{dataset_directory_stem(dataset_name)}.seed-{root_seed}"


def emhi_fit_artifact_id(
    dataset_name: DatasetName, root_seed: SeedValue, method_name: MethodName
) -> ArtifactIdentity:
    return f"emhi-fit.{dataset_directory_stem(dataset_name)}.seed-{root_seed}.{method_artifact_stem(method_name)}"


def detector_score_artifact_path(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    root_seed: SeedValue,
) -> Path:
    layout = build_artifact_layout(loaded, repository)
    return (
        layout.roots.outputs_root
        / "artifacts"
        / "scores"
        / dataset_directory_stem(dataset_name)
        / f"seed-{root_seed}.json"
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
        / "artifacts"
        / "fitted"
        / dataset_directory_stem(dataset_name)
        / f"seed-{root_seed}-marginal-ranks.json"
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
        / "artifacts"
        / "fitted"
        / dataset_directory_stem(dataset_name)
        / f"seed-{root_seed}"
        / f"{method_artifact_stem(method_name)}.json"
    )


OUTPUTS_ARTIFACT_CHILDREN = (
    "models",
    "scores",
    "fitted",
    "baselines",
    "derived",
)
OUTPUTS_CACHE_CHILDREN = (
    "preprocessing",
    "models",
    "evaluation",
    "analysis",
    "staging",
)
EXPERIMENT_OUTPUT_TREES = {
    "artifacts": ("fitted", "predictions", "derived"),
    "evaluations": ("records", "comparisons", "aggregates"),
    "metrics": ("per_seed", "per_condition", "aggregate"),
    "statistics": ("tests", "confidence_intervals", "effects", "multiplicity"),
    "checkpoints": ("training", "execution"),
    "diagnostics": ("scientific", "numerical", "runtime"),
    "logs": ("execution", "failures"),
    "provenance": ("configuration", "data", "seeds", "code", "environment", "dependencies"),
}
EXPERIMENT_RESULTS_TREES = {
    "figures": ("main", "supplementary"),
    "tables": ("main", "supplementary"),
    "metrics": ("primary", "secondary", "summary"),
    "statistics": ("tests", "confidence_intervals", "effects", "multiplicity"),
    "source_data": ("figures", "tables"),
}
PROJECT_SUMMARY_TREES = {
    "figures": ("main", "supplementary"),
    "tables": ("main", "supplementary"),
    "metrics": ("primary", "summary"),
    "statistics": ("comparisons", "confidence_intervals", "effects", "multiplicity"),
    "source_data": ("figures", "tables"),
    "reproducibility": ("configuration", "datasets", "seeds", "software", "execution"),
}


@dataclass(frozen=True)
class ArtifactLayout:
    roots: ArtifactRoots

    def experiment_outputs_root(self, experiment_name: ExperimentName) -> Path:
        return self.roots.outputs_root / "experiments" / experiment_name.value

    def experiment_results_root(self, experiment_name: ExperimentName) -> Path:
        return self.roots.results_root / "experiments" / experiment_name.value

    def required_directories(self) -> tuple[Path, ...]:
        paths: list[Path] = [
            self.roots.outputs_root,
            self.roots.results_root,
            self.roots.outputs_root / "preprocessing",
            self.roots.outputs_root / "artifacts",
            self.roots.outputs_root / "experiments",
            self.roots.outputs_root / "cache",
            self.roots.results_root / "experiments",
            self.roots.results_root / "project_summary",
        ]
        paths.extend(
            _child_directories(
                self.roots.outputs_root / "preprocessing", OUTPUTS_PREPROCESSING_CHILDREN
            )
        )
        paths.extend(
            _child_directories(self.roots.outputs_root / "artifacts", OUTPUTS_ARTIFACT_CHILDREN)
        )
        paths.extend(_child_directories(self.roots.outputs_root / "cache", OUTPUTS_CACHE_CHILDREN))
        for experiment_name in ExperimentName:
            experiment_output = self.experiment_outputs_root(experiment_name)
            paths.append(experiment_output)
            paths.extend(_nested_directories(experiment_output, EXPERIMENT_OUTPUT_TREES))
            experiment_result = self.experiment_results_root(experiment_name)
            paths.append(experiment_result)
            paths.extend(_nested_directories(experiment_result, EXPERIMENT_RESULTS_TREES))
        paths.extend(
            _nested_directories(self.roots.results_root / "project_summary", PROJECT_SUMMARY_TREES)
        )
        return tuple(paths)


def _child_directories(parent: Path, children: tuple[RelativePath, ...]) -> tuple[Path, ...]:
    return tuple(parent / child for child in children)


def _nested_directories(
    root: Path, tree: Mapping[RelativePath, tuple[RelativePath, ...]]
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
        destination.with_suffix(".manifest.json"),
        manifest.model_dump(mode="json"),
        layout.roots.outputs_root / "cache" / "staging",
    )


def read_json_bytes(path: Path) -> DeterministicUtf8Bytes:
    return path.read_bytes()
