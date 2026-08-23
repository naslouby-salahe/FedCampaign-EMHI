import pytest

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import DatasetName, MethodName
from fedcampaign_emhi.experiments.strong_local import (
    enumerate_strong_local_policy_plan,
    strong_local_directional_margin,
    strong_local_odi_rate_gate,
)


def test_plan_reads_configuration_with_primary_global_method() -> None:
    loaded = load_production_configuration()
    plan = enumerate_strong_local_policy_plan(loaded.values)
    assert plan.dataset_name is DatasetName.TON_IOT_NETWORK
    assert plan.global_method is MethodName.FULL_FEDCAMPAIGN_EMHI
    assert plan.development_seed_count == len(loaded.values.randomness.real_development_roots)
    assert plan.confirmatory_seed_count == len(loaded.values.randomness.real_confirmatory_roots)
    assert plan.minimum_strict_odi_rate == (
        loaded.values.claim_materiality.strong_local.minimum_strict_odi_rate
    )


def test_odi_rate_gate_is_inclusive_at_minimum() -> None:
    loaded = load_production_configuration()
    minimum = loaded.values.claim_materiality.strong_local.minimum_strict_odi_rate
    assert strong_local_odi_rate_gate(minimum, minimum) is True
    assert strong_local_odi_rate_gate(minimum - 0.01, minimum) is False


def test_directional_margin_is_mean_minus_minimum() -> None:
    loaded = load_production_configuration()
    minimum = loaded.values.claim_materiality.strong_local.minimum_strict_odi_rate
    margin = strong_local_directional_margin((minimum + 0.02, minimum + 0.04), minimum)
    assert margin == pytest.approx(0.03)
    with pytest.raises(ValueError):
        strong_local_directional_margin((), minimum)
