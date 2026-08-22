import pytest

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.experiments.sequential_evidence import (
    aggregate_feasibility,
    calibrated_route_heldout_pfa_gate,
    deterministic_outside_midpoint,
    enumerate_feasibility_plan,
    latent_support_cell,
    restricted_arl,
    restricted_arl_lower_bound_passes,
    support_rows_for_requested_count,
    theorem_route_assumption_checks,
)


def test_feasibility_plan_reads_authoritative_configuration() -> None:
    loaded = load_production_configuration()
    plan = enumerate_feasibility_plan(loaded.values)
    assert plan.primary_client_count == (
        loaded.values.experiments.pure_order_separation_validation.primary_client_count
    )
    assert plan.maximum_coalition_order == int(loaded.values.study.maximum_coalition_order)
    assert plan.support_sweep == loaded.values.support_grids.estimator_samples_per_context
    assert plan.evaluation_samples_per_context_seed == (
        loaded.values.synthetic.sample_sizes.estimator_evaluation_samples_per_context_seed
    )
    assert (
        plan.order_three_minimum_support == loaded.values.context.minimum_support_epochs.order_three
    )


def test_support_rows_generate_exact_usable_observations() -> None:
    assert support_rows_for_requested_count(100, 4) == 401
    assert support_rows_for_requested_count(400, 8) == 3201


def test_latent_support_cells_cycle_without_labeling_estimation() -> None:
    assert latent_support_cell(0, 4) == 0
    assert latent_support_cell(5, 4) == 1
    assert latent_support_cell(9, 4) == 1


def test_deterministic_outside_midpoints_are_distinct_per_cell() -> None:
    midpoints = [deterministic_outside_midpoint(cell, 4) for cell in range(4)]
    assert len(set(midpoints)) == 4
    for cell in range(4):
        assert midpoints[cell] == pytest.approx((cell + 0.5) / 4)
    with pytest.raises(ValueError):
        deterministic_outside_midpoint(4, 4)


def test_feasibility_aggregation_matches_hand_computed_values() -> None:
    aggregate = aggregate_feasibility(
        seed_coverages=(0.8, 0.9),
        seed_projection_nrmse=(0.02, 0.04),
        seed_null_bias=(0.03, 0.05),
        failure_counts=(1, 3),
        attempted_counts=(100, 100),
    )
    assert aggregate.mean_coverage == pytest.approx(0.85)
    assert aggregate.mean_projection_nrmse == pytest.approx(0.03)
    assert aggregate.mean_standardized_null_bias == pytest.approx(0.04)
    assert aggregate.pooled_numerical_failure_rate == pytest.approx(0.02)


def test_restricted_arl_caps_nonstopping_trajectories_at_maximum() -> None:
    arl = restricted_arl((50, 60, 10000), 200)
    assert arl == pytest.approx((50 + 60 + 200) / 3)
    with pytest.raises(ValueError):
        restricted_arl((), 100)


def test_restricted_arl_lower_bound_gate() -> None:
    loaded = load_production_configuration()
    minimum = loaded.values.experiments.sequential_evidence_validation.signed_theorem.restricted_arl_bootstrap_lower_bound_minimum_epochs
    assert restricted_arl_lower_bound_passes(minimum, minimum) is True
    assert restricted_arl_lower_bound_passes(minimum - 1, minimum) is False


def test_theorem_route_assumption_checks() -> None:
    loaded = load_production_configuration()
    evidence = loaded.values.evidence
    factors_ok = theorem_route_assumption_checks(
        clip_bound=evidence.clip_bound,
        bet_lambda=evidence.bet_lambda,
        configured_arl_alpha=evidence.signed_theorem_sequential.arl_alpha,
        expected_compensator_tolerance=1e-15,
        observed_factors=(1.0, 0.5),
    )
    assert factors_ok is True
    broken = theorem_route_assumption_checks(
        clip_bound=evidence.clip_bound,
        bet_lambda=0.7,
        configured_arl_alpha=evidence.signed_theorem_sequential.arl_alpha,
        expected_compensator_tolerance=1e-15,
        observed_factors=(1.0,),
    )
    assert broken is False


def test_calibrated_route_heldout_pfa_gate() -> None:
    loaded = load_production_configuration()
    finite_horizon = loaded.values.evidence.calibrated_finite_horizon
    horizons = loaded.values.synthetic.sample_sizes.finite_horizon_heldout_null_horizons_per_seed
    passing = calibrated_route_heldout_pfa_gate(
        0, horizons, finite_horizon.calibration_confidence, finite_horizon.target_pfa
    )
    assert passing is True
    failing = calibrated_route_heldout_pfa_gate(
        horizons, horizons, finite_horizon.calibration_confidence, finite_horizon.target_pfa
    )
    assert failing is False
