from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import ExecutionRole, ExperimentName
from fedcampaign_emhi.experiments.registry import experiment_registry


def test_registry_contains_roadmap_experiments() -> None:
    loaded = load_production_configuration()
    names = {contract.experiment_name for contract in experiment_registry(loaded.values)}
    assert names == set(ExperimentName)


def test_strong_comparator_challenge_has_single_development_role() -> None:
    loaded = load_production_configuration()
    contracts = {
        contract.experiment_name: contract for contract in experiment_registry(loaded.values)
    }
    challenge = contracts[ExperimentName.STRONG_COMPARATOR_COMPOSITION_CHALLENGE]
    assert challenge.execution_roles == (ExecutionRole.DEVELOPMENT,)


def test_no_contract_duplicates_development_seed_namespace() -> None:
    loaded = load_production_configuration()
    for contract in experiment_registry(loaded.values):
        if (
            ExecutionRole.DEVELOPMENT in contract.execution_roles
            and ExecutionRole.DEVELOPMENT_ONLY in contract.execution_roles
        ):
            raise AssertionError(
                f"{contract.experiment_name.value} lists both development and "
                "development_only roles that execute the same seed namespace"
            )
