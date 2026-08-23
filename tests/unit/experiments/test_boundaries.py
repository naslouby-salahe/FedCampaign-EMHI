import pytest

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import GeneratorName, MethodName
from fedcampaign_emhi.experiments.boundaries import (
    BOUNDARY_GENERATOR,
    BOUNDARY_STUDY_METHOD_BASELINE,
    CONTAMINATION_METRIC_COUNT,
    DROPOUT_METRIC_COUNT,
    enumerate_dropout_boundary_plan,
    enumerate_outside_contamination_plan,
    over_conditioning_drift_indicator,
)


def test_contamination_plan_reads_generator_configuration() -> None:
    loaded = load_production_configuration()
    plan = enumerate_outside_contamination_plan(loaded.values)
    generator = loaded.values.generators.outside_contamination
    assert plan.client_count == generator.client_count
    assert plan.correlated_campaign_fractions == tuple(generator.correlated_campaign_fractions)
    assert plan.target_triple_theta == generator.target_triple_theta
    assert plan.development_seed_count == len(loaded.values.randomness.synthetic_development_roots)
    assert plan.confirmatory_seed_count == len(
        loaded.values.randomness.synthetic_confirmatory_roots
    )


def test_dropout_plan_reads_robustness_configuration() -> None:
    loaded = load_production_configuration()
    plan = enumerate_dropout_boundary_plan(loaded.values)
    dropout = loaded.values.generators.client_dropout
    assert plan.scalability_client_counts == tuple(
        loaded.values.robustness.scalability_client_counts
    )
    assert plan.unavailable_fractions == tuple(dropout.unavailable_fractions)
    assert plan.development_seed_count == len(loaded.values.randomness.synthetic_development_roots)


def test_boundary_scopes_are_restricted() -> None:
    assert BOUNDARY_GENERATOR is GeneratorName.CONTEXT_DEPENDENT_PURE_TRIPLE
    assert BOUNDARY_STUDY_METHOD_BASELINE is MethodName.FULL_FEDCAMPAIGN_EMHI
    assert CONTAMINATION_METRIC_COUNT == 5
    assert DROPOUT_METRIC_COUNT == 5


def test_over_conditioning_drift_indicator() -> None:
    assert over_conditioning_drift_indicator(0.9, 0.7) == pytest.approx(-0.2)
    assert over_conditioning_drift_indicator(0.5, 0.5) == 0.0
