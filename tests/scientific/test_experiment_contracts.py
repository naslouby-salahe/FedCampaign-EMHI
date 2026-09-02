from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.experiments.registry import enumerate_experiment_plan


def test_plan_is_derived_from_registry_and_seeds() -> None:
    loaded = load_production_configuration()
    planned = enumerate_experiment_plan(loaded.values)
    assert planned
    assert all(seed_count >= 0 for _name, _role, seed_count in planned)
