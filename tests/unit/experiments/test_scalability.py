import pytest

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.experiments.scalability import (
    common_mode_loading,
    derived_coalition_count,
    enumerate_scalability_plan,
    latency_gate,
    scalability_numerical_failure_gate,
    synthetic_workload_feature_dimension,
)


def test_plan_reads_configuration_and_enables_all_orders() -> None:
    loaded = load_production_configuration()
    plan = enumerate_scalability_plan(loaded.values)
    assert plan.client_counts == tuple(loaded.values.robustness.scalability_client_counts)
    assert plan.development_seed_count == len(loaded.values.randomness.real_development_roots)
    assert plan.confirmatory_seed_count == len(loaded.values.randomness.real_confirmatory_roots)
    maximum_order = int(loaded.values.study.maximum_coalition_order)
    assert plan.enabled_orders == tuple(
        CoalitionOrder(order) for order in range(1, maximum_order + 1)
    )


def test_workload_feature_dimension_is_hash_buckets_plus_two() -> None:
    loaded = load_production_configuration()
    bucket_count = loaded.values.datasets.preprocessing.event_type_hash_bucket_count
    assert synthetic_workload_feature_dimension(bucket_count) == bucket_count + 2
    with pytest.raises(ValueError):
        synthetic_workload_feature_dimension(0)


def test_common_mode_loading_interpolates_linearly() -> None:
    loaded = load_production_configuration()
    common_mode = loaded.values.generators.common_mode
    low = common_mode.client_loading_minimum
    high = common_mode.client_loading_maximum
    k = 5
    assert common_mode_loading(0, k, low, high) == pytest.approx(low)
    assert common_mode_loading(k - 1, k, low, high) == pytest.approx(high)
    middle = common_mode_loading(2, k, low, high)
    assert middle == pytest.approx(low + (2 / (k - 1)) * (high - low))
    assert common_mode_loading(0, 1, low, high) == low
    with pytest.raises(ValueError):
        common_mode_loading(7, k, low, high)


def test_derived_coalition_count_matches_hand_computed_values() -> None:
    loaded = load_production_configuration()
    maximum_order = int(loaded.values.study.maximum_coalition_order)
    assert derived_coalition_count(3, 3) == 7
    from math import comb

    total = 0
    for order in range(1, maximum_order + 1):
        total += comb(10, order)
    assert derived_coalition_count(10, maximum_order) == total


def test_scalability_support_gates() -> None:
    loaded = load_production_configuration()
    materiality = loaded.values.claim_materiality
    maximum_latency = materiality.reference_harness.p95_latency_maximum_seconds
    assert latency_gate(maximum_latency, maximum_latency) is True
    assert latency_gate(maximum_latency + 0.01, maximum_latency) is False
    failure_maximum = materiality.maximum_pooled_numerical_failure_rate
    passing = scalability_numerical_failure_gate(0, 100, failure_maximum)
    assert passing is True
    failing = scalability_numerical_failure_gate(100, 100, failure_maximum)
    assert failing is False
    with pytest.raises(ValueError):
        scalability_numerical_failure_gate(0, 0, failure_maximum)
