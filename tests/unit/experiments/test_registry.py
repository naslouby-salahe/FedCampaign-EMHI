from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import ExperimentName
from fedcampaign_emhi.experiments.registry import experiment_registry


def test_registry_contains_roadmap_experiments() -> None:
    loaded = load_production_configuration()
    names = {contract.experiment_name for contract in experiment_registry(loaded.values)}
    assert ExperimentName.PRIMARY_STRICT_ODI_EVALUATION in names
    assert ExperimentName.SYNTHETIC_MODULE_VALIDATION in names
