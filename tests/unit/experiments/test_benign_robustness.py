import pytest

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.types import BenignHorizon
from fedcampaign_emhi.evaluation.metrics import (
    common_mode_suppression,
    outside_conditioning_power_loss,
)
from fedcampaign_emhi.experiments.robustness import (
    EpochEventVolume,
    detection_rate_loss_within_maximum,
    enumerate_benign_common_mode_plan,
    false_campaign_suppression_meets_minimum,
    federation_wide_epoch_event_counts,
    paired_false_campaign_difference,
    rolling_benign_horizons,
    select_high_volume_windows,
    synthetic_count_stress_multiplier,
    window_event_counts,
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


def test_paired_false_campaign_difference_direction() -> None:
    assert paired_false_campaign_difference(0.3, 0.1) == pytest.approx(0.2)
    assert paired_false_campaign_difference(0.1, 0.3) == pytest.approx(-0.2)


def test_rolling_benign_horizons_overlap_by_stride() -> None:
    epochs = (10, 11, 12, 13, 14, 15)
    horizons = rolling_benign_horizons(epochs, horizon_length=3, stride=1)
    assert horizons == (
        BenignHorizon(start_epoch=10, epoch_indexes=(10, 11, 12)),
        BenignHorizon(start_epoch=11, epoch_indexes=(11, 12, 13)),
        BenignHorizon(start_epoch=12, epoch_indexes=(12, 13, 14)),
        BenignHorizon(start_epoch=13, epoch_indexes=(13, 14, 15)),
    )


def test_rolling_benign_horizons_respects_larger_stride() -> None:
    epochs = (0, 1, 2, 3, 4, 5, 6)
    horizons = rolling_benign_horizons(epochs, horizon_length=2, stride=3)
    assert horizons == (
        BenignHorizon(start_epoch=0, epoch_indexes=(0, 1)),
        BenignHorizon(start_epoch=3, epoch_indexes=(3, 4)),
    )


def test_rolling_benign_horizons_rejects_nonpositive_parameters() -> None:
    with pytest.raises(ValueError):
        rolling_benign_horizons((0, 1, 2), horizon_length=0, stride=1)
    with pytest.raises(ValueError):
        rolling_benign_horizons((0, 1, 2), horizon_length=1, stride=0)


def test_federation_wide_epoch_event_counts_sums_selected_clients_only() -> None:
    epochs = (
        EpochEventVolume(client_id="client-1", epoch_index=0, raw_event_count=10),
        EpochEventVolume(client_id="client-2", epoch_index=0, raw_event_count=5),
        EpochEventVolume(client_id="client-3", epoch_index=0, raw_event_count=99),
    )
    totals = federation_wide_epoch_event_counts(
        epochs, selected_client_ids=("client-1", "client-2")
    )
    assert totals == ((0, 15),)


def test_window_event_counts_and_selection() -> None:
    windows = (
        BenignHorizon(start_epoch=0, epoch_indexes=(0, 1)),
        BenignHorizon(start_epoch=1, epoch_indexes=(1, 2)),
        BenignHorizon(start_epoch=2, epoch_indexes=(2, 3)),
    )
    totals = ((0, 10), (1, 20), (2, 30), (3, 5))
    counts = window_event_counts(windows, totals)
    assert counts == (30, 50, 35)
    selected = select_high_volume_windows(windows, counts, 0.5)
    assert selected == (windows[1],)


def test_select_high_volume_windows_retains_boundary_ties() -> None:
    windows = (
        BenignHorizon(start_epoch=0, epoch_indexes=(0,)),
        BenignHorizon(start_epoch=1, epoch_indexes=(1,)),
        BenignHorizon(start_epoch=2, epoch_indexes=(2,)),
        BenignHorizon(start_epoch=3, epoch_indexes=(3,)),
        BenignHorizon(start_epoch=4, epoch_indexes=(4,)),
    )
    counts = (100, 90, 90, 80, 70)
    selected = select_high_volume_windows(windows, counts, 0.4)
    assert selected == (windows[0], windows[1], windows[2])
    with pytest.raises(ValueError):
        select_high_volume_windows(windows, counts, 0.0)
    with pytest.raises(ValueError):
        select_high_volume_windows((), (), 0.5)
    with pytest.raises(ValueError):
        select_high_volume_windows(windows, counts[:-1], 0.5)


def test_synthetic_count_stress_preserves_bucket_proportions() -> None:
    buckets = (10.0, 30.0, 60.0)
    doubled = synthetic_count_stress_multiplier(buckets, 2.0)
    assert doubled == (20.0, 60.0, 120.0)
    total_original = sum(buckets)
    total_doubled = sum(doubled)
    for original, stressed in zip(buckets, doubled, strict=True):
        assert stressed / total_doubled == pytest.approx(original / total_original)
    with pytest.raises(ValueError):
        synthetic_count_stress_multiplier(buckets, -1.0)
    with pytest.raises(ValueError):
        synthetic_count_stress_multiplier((), 2.0)


def test_seed_level_power_loss_is_no_outside_minus_emhi() -> None:
    assert outside_conditioning_power_loss(0.8, 0.9) == pytest.approx(-0.1)
    assert outside_conditioning_power_loss(0.9, 0.8) == pytest.approx(0.1)


def test_common_mode_suppression_uses_denominator_floor() -> None:
    assert common_mode_suppression(0.0, 0.0, 1e-12) == pytest.approx(1.0)
    assert common_mode_suppression(0.1, 0.2, 1e-12) == pytest.approx(1.0 - 0.1 / 0.2, rel=1e-6)


def test_support_conditions_are_inclusive_at_materiality_bounds() -> None:
    loaded = load_production_configuration()
    materiality = loaded.values.materiality.benign_common_mode
    minimum = materiality.minimum_false_campaign_suppression
    maximum = materiality.maximum_detection_rate_loss
    assert false_campaign_suppression_meets_minimum(minimum, minimum) is True
    assert false_campaign_suppression_meets_minimum(minimum - 0.01, minimum) is False
    assert detection_rate_loss_within_maximum(maximum, maximum) is True
    assert detection_rate_loss_within_maximum(maximum + 0.01, maximum) is False
