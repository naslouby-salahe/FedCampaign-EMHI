import pytest

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.experiments.benign_robustness import (
    enumerate_benign_common_mode_plan,
    false_campaign_suppression_gate,
    paired_false_campaign_difference,
    power_loss_gate,
    seed_level_power_loss,
    select_top_event_count_windows,
    synthetic_count_stress_multiplier,
)


def test_plan_reads_authoritative_configuration() -> None:
    loaded = load_production_configuration()
    plan = enumerate_benign_common_mode_plan(loaded.values)
    robustness = loaded.values.experiments.benign_common_mode_robustness
    assert plan.dataset_name is loaded.values.datasets.primary.name
    assert plan.methods == tuple(robustness.methods)
    assert plan.stress_stride_epochs == robustness.native_high_volume_window.stride_epochs
    assert plan.top_event_count_fraction == (
        robustness.native_high_volume_window.top_event_count_fraction
    )


def test_top_event_count_selection_retains_boundary_ties() -> None:
    counts = (100, 90, 90, 80, 70)
    selected = select_top_event_count_windows(counts, 0.4)
    assert selected == (100, 90, 90)
    single = select_top_event_count_windows((5,), 0.5)
    assert single == (5,)
    with pytest.raises(ValueError):
        select_top_event_count_windows(counts, 0.0)
    with pytest.raises(ValueError):
        select_top_event_count_windows((), 0.5)


def test_synthetic_count_stress_preserves_proportions_and_entropy() -> None:
    buckets = (10, 30, 60)
    doubled = synthetic_count_stress_multiplier(buckets, 2.0)
    total_original = sum(buckets)
    total_doubled = sum(doubled)
    for original, stressed in zip(buckets, doubled, strict=True):
        assert stressed / total_doubled == pytest.approx(original / total_original)
    with pytest.raises(ValueError):
        synthetic_count_stress_multiplier(buckets, -1.0)


def test_seed_level_power_loss_is_no_outside_minus_emhi() -> None:
    assert seed_level_power_loss(0.8, 0.9) == pytest.approx(-0.1)
    assert seed_level_power_loss(0.9, 0.8) == pytest.approx(0.1)


def test_support_gates_are_inclusive_at_materiality_bounds() -> None:
    loaded = load_production_configuration()
    materiality = loaded.values.claim_materiality.benign_common_mode
    minimum = materiality.minimum_false_campaign_suppression
    maximum = materiality.maximum_detection_rate_loss
    assert false_campaign_suppression_gate(minimum, minimum) is True
    assert false_campaign_suppression_gate(minimum - 0.01, minimum) is False
    assert power_loss_gate(maximum, maximum) is True
    assert power_loss_gate(maximum + 0.01, maximum) is False


def test_paired_false_campaign_difference_direction() -> None:
    assert paired_false_campaign_difference(0.3, 0.1) == pytest.approx(0.2)
    assert paired_false_campaign_difference(0.1, 0.3) == pytest.approx(-0.2)
