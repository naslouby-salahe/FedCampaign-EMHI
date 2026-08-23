from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import ExperimentName
from fedcampaign_emhi.experiments.definitions import experiment_registry


def assert_known_experiment(config: ScientificConfig, experiment_name: ExperimentName) -> None:
    names = {contract.experiment_name for contract in experiment_registry(config)}
    if experiment_name not in names:
        raise ValueError(f"experiment {experiment_name.value} is not in the configured registry")
