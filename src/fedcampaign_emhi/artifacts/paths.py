from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import ExperimentName
from fedcampaign_emhi.domain.types import ArtifactRoots, RelativePath

OUTPUTS_PREPROCESSING_CHILDREN = (
    "inventories",
    "validation",
    "prepared",
    "splits",
    "features",
    "metadata",
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
