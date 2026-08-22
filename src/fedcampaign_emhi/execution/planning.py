from dataclasses import dataclass

from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import ExecutionRole, ExperimentName, ExperimentState
from fedcampaign_emhi.domain.types import ArtifactFilename, ResumeStep, SeedCount
from fedcampaign_emhi.experiments.coordinates import enumerate_experiment_plan
from fedcampaign_emhi.experiments.definitions import resolve_experiment_name

RESUME_SEQUENCE: tuple[ResumeStep, ...] = (
    "validate required existing artifacts",
    "reuse compatible ancestors",
    "identify incompatible or incomplete artifacts",
    "invalidate only their descendants",
    "reconstruct the minimum required subgraph",
    "atomically publish completed outputs",
)


@dataclass(frozen=True)
class PlannedExperiment:
    experiment_name: ExperimentName
    execution_role: ExecutionRole
    seed_count: SeedCount
    state: ExperimentState


def plan_experiments(loaded: LoadedScientificConfiguration) -> tuple[PlannedExperiment, ...]:
    planned: list[PlannedExperiment] = []
    for experiment_name, role, seed_count in enumerate_experiment_plan(loaded.values):
        planned.append(
            PlannedExperiment(
                experiment_name=experiment_name,
                execution_role=role,
                seed_count=seed_count,
                state=ExperimentState.NOT_STARTED,
            )
        )
    return tuple(planned)


def resolve_requested_experiment(name: ArtifactFilename) -> ExperimentName:
    return resolve_experiment_name(name)
