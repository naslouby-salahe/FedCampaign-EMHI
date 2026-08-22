from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import ExecutionRole, ExperimentName
from fedcampaign_emhi.domain.types import SeedCount
from fedcampaign_emhi.experiments.definitions import ExperimentContract, experiment_registry


def planned_seed_count(
    config: ScientificConfig, contract: ExperimentContract, role: ExecutionRole
) -> SeedCount:
    if contract.experiment_name is ExperimentName.SYNTHETIC_MODULE_VALIDATION:
        return 1
    if role is ExecutionRole.CONFIRMATORY:
        if contract.uses_synthetic_seeds:
            return len(config.randomness.synthetic_confirmatory_roots)
        if contract.uses_real_seeds:
            return len(config.randomness.real_confirmatory_roots)
        return 0
    if contract.uses_synthetic_seeds:
        return len(config.randomness.synthetic_development_roots)
    if contract.uses_real_seeds:
        return len(config.randomness.real_development_roots)
    return 0


def enumerate_experiment_plan(
    config: ScientificConfig,
) -> tuple[tuple[ExperimentName, ExecutionRole, SeedCount], ...]:
    planned: list[tuple[ExperimentName, ExecutionRole, SeedCount]] = []
    for contract in experiment_registry(config):
        for role in contract.execution_roles:
            planned.append(
                (contract.experiment_name, role, planned_seed_count(config, contract, role))
            )
    return tuple(planned)
