import pytest

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import DatasetName, MethodName
from fedcampaign_emhi.experiments.primary_odi import (
    PRIMARY_CAUSAL_COMPARATOR,
    campaign_evaluation_universe,
    campaign_registry_universe_size,
    enumerate_primary_strict_odi_plan,
    matched_operating_point_requirement,
    median_of,
    median_operational_lead_gate,
    paired_odi_advantage_gate,
    strict_odi_rate_gate,
)


def test_plan_reads_authoritative_configuration() -> None:
    loaded = load_production_configuration()
    plan = enumerate_primary_strict_odi_plan(loaded.values)
    assert plan.dataset_name is DatasetName.TON_IOT_NETWORK
    assert plan.methods == tuple(loaded.values.experiments.primary_strict_odi_evaluation.methods)
    assert plan.development_seed_count == len(loaded.values.randomness.real_development_roots)
    assert plan.confirmatory_seed_count == len(loaded.values.randomness.real_confirmatory_roots)
    materiality = loaded.values.claim_materiality.primary_real
    assert plan.minimum_strict_odi_rate == materiality.minimum_strict_odi_rate
    assert plan.minimum_odi_advantage == (
        materiality.minimum_odi_rate_advantage_over_order_at_most_two
    )
    assert plan.minimum_median_operational_lead_epochs == (
        materiality.minimum_median_operational_lead_epochs
    )


def test_primary_causal_comparator_is_locked() -> None:
    assert PRIMARY_CAUSAL_COMPARATOR is MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI


def test_strict_odi_rate_gate_inclusive_at_minimum() -> None:
    loaded = load_production_configuration()
    minimum = loaded.values.claim_materiality.primary_real.minimum_strict_odi_rate
    assert strict_odi_rate_gate(minimum, minimum) is True
    assert strict_odi_rate_gate(minimum - 0.01, minimum) is False


def test_paired_advantage_gate_uses_difference() -> None:
    loaded = load_production_configuration()
    minimum = loaded.values.claim_materiality.primary_real.minimum_odi_rate_advantage_over_order_at_most_two
    assert paired_odi_advantage_gate(minimum, 0.0, minimum) is True
    assert paired_odi_advantage_gate(0.5, 0.5 + minimum + 0.01, minimum) is False


def test_median_lead_gate_and_median_computation() -> None:
    loaded = load_production_configuration()
    minimum = loaded.values.claim_materiality.primary_real.minimum_median_operational_lead_epochs
    odd = (1.0, 5.0, 3.0)
    even = (4.0, 2.0)
    assert median_of(odd) == 3.0
    assert median_of(even) == 3.0
    assert median_operational_lead_gate(median_of((minimum, 9.0, 12.0)), minimum) is True
    assert median_operational_lead_gate(median_of((1.0, minimum - 1.0, 1.5)), minimum) is False
    with pytest.raises(ValueError):
        median_of(())


def test_matched_operating_point_requirement() -> None:
    assert matched_operating_point_requirement(True, True) is True
    assert matched_operating_point_requirement(True, False) is False
    assert matched_operating_point_requirement(False, True) is False


def test_campaign_universe_never_drops_eligible_campaigns() -> None:
    clients = (("a", "b"), ("c",), ("d", "e"))
    assert campaign_registry_universe_size(clients, 2) == 2
    assert campaign_evaluation_universe(2) == 2
    with pytest.raises(ValueError):
        campaign_evaluation_universe(0)
