from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.experiments.secondary_generalization import (
    enumerate_secondary_generalization_plan,
    secondary_interpretation_is_validation_only,
)


def test_plan_reads_secondary_dataset_and_methods() -> None:
    loaded = load_production_configuration()
    plan = enumerate_secondary_generalization_plan(loaded.values)
    experiment = loaded.values.experiments.secondary_controlled_trace_generalization
    assert plan.dataset_name is loaded.values.datasets.secondary.name
    assert plan.methods == tuple(experiment.methods)
    assert plan.development_seed_count == len(loaded.values.randomness.real_development_roots)
    assert plan.confirmatory_seed_count == len(loaded.values.randomness.real_confirmatory_roots)


def test_interpretation_is_restricted_to_validation() -> None:
    loaded = load_production_configuration()
    plan = enumerate_secondary_generalization_plan(loaded.values)
    assert secondary_interpretation_is_validation_only(plan) is True
