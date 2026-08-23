from dataclasses import dataclass, replace

from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import ExecutionRole, ExperimentName, ExperimentState
from fedcampaign_emhi.domain.types import SeedCount
from fedcampaign_emhi.execution.planning import plan_experiments


@dataclass(frozen=True)
class ExperimentStatus:
    experiment_name: ExperimentName
    state: ExperimentState
    development_seed_count: SeedCount
    confirmatory_seed_count: SeedCount


def project_status(loaded: LoadedScientificConfiguration) -> tuple[ExperimentStatus, ...]:
    statuses: list[ExperimentStatus] = []
    for planned in plan_experiments(loaded):
        existing_index = next(
            (
                index
                for index, item in enumerate(statuses)
                if item.experiment_name is planned.experiment_name
            ),
            None,
        )
        if existing_index is None:
            development = planned.seed_count
            confirmatory = 0
            if planned.execution_role is ExecutionRole.CONFIRMATORY:
                development = 0
                confirmatory = planned.seed_count
            statuses.append(
                ExperimentStatus(
                    experiment_name=planned.experiment_name,
                    state=planned.state,
                    development_seed_count=development,
                    confirmatory_seed_count=confirmatory,
                )
            )
            continue
        current = statuses[existing_index]
        if planned.execution_role is ExecutionRole.CONFIRMATORY:
            statuses[existing_index] = replace(current, confirmatory_seed_count=planned.seed_count)
        else:
            statuses[existing_index] = replace(
                current,
                development_seed_count=max(current.development_seed_count, planned.seed_count),
            )
    return tuple(statuses)
