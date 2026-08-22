import pytest

from fedcampaign_emhi.comparators.composition import (
    CompositionSelectionInputs,
    composition_seed_count,
    null_standard_deviation_is_usable,
    select_strongest_comparator,
    selection_rule_identity,
    standardized_estimation_error,
)
from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import MethodName


def build_inputs() -> CompositionSelectionInputs:
    loaded = load_production_configuration()
    challenge = loaded.values.experiments.strong_comparator_composition_challenge
    sample_sizes = loaded.values.synthetic.sample_sizes
    return CompositionSelectionInputs(
        reference_theta=loaded.values.generators.pure_polynomial.primary_reference_theta,
        error_tie_tolerance=challenge.error_tie_tolerance_standardized_units,
        runtime_tie_tolerance=challenge.runtime_tie_tolerance_seconds,
        calibration_horizons_per_seed=sample_sizes.finite_horizon_calibration_horizons_per_seed,
        heldout_null_horizons_per_seed=sample_sizes.finite_horizon_heldout_null_horizons_per_seed,
        timed_scoring_rows=(
            sample_sizes.pure_order_independent_evaluation_samples_per_condition_seed
        ),
        artifact_filename=challenge.artifact_filename,
    )


def test_selection_inputs_come_from_configuration() -> None:
    loaded = load_production_configuration()
    inputs = build_inputs()
    assert (
        inputs.reference_theta == loaded.values.generators.pure_polynomial.primary_reference_theta
    )
    assert inputs.artifact_filename == "strongest-comparator-composition.json"
    assert inputs.timed_scoring_rows == 10000


def test_estimation_error_is_absolute_distance_from_truth() -> None:
    theta = build_inputs().reference_theta
    assert standardized_estimation_error(theta + 0.05, theta) == pytest.approx(0.05)
    assert standardized_estimation_error(theta - 0.05, theta) == pytest.approx(0.05)
    assert standardized_estimation_error(theta, theta) == 0.0


def test_null_deviation_floor_rejects_degenerate_calibration() -> None:
    loaded = load_production_configuration()
    floor = loaded.values.numerics.metric_denominator_floor
    assert null_standard_deviation_is_usable(1.0, floor) is True
    assert null_standard_deviation_is_usable(floor, floor) is False
    assert null_standard_deviation_is_usable(0.0, floor) is False
    assert null_standard_deviation_is_usable(floor / 2, floor) is False


def test_selection_rule_identity_is_deterministic() -> None:
    first = selection_rule_identity(build_inputs())
    second = selection_rule_identity(build_inputs())
    assert first == second
    assert len(first) == 64


def test_tiebreak_order_error_then_runtime_then_name() -> None:
    error_tol = 1e-9
    runtime_tol = 1e-6
    candidates = (
        MethodName.CONNECTED_INFORMATION_REFERENCE,
        MethodName.D_VINE_CONDITIONAL_REFERENCE,
    )
    selected_by_error = select_strongest_comparator(
        candidates, (0.30, 0.10), (5.0, 5.0), error_tol, runtime_tol
    )
    assert selected_by_error is MethodName.D_VINE_CONDITIONAL_REFERENCE
    selected_by_runtime = select_strongest_comparator(
        candidates, (0.10, 0.10), (2.0, 5.0), error_tol, runtime_tol
    )
    assert selected_by_runtime is MethodName.CONNECTED_INFORMATION_REFERENCE
    selected_by_name = select_strongest_comparator(
        (MethodName.D_VINE_CONDITIONAL_REFERENCE, MethodName.CONNECTED_INFORMATION_REFERENCE),
        (0.10, 0.10),
        (5.0, 5.0),
        error_tol,
        runtime_tol,
    )
    assert selected_by_name is MethodName.CONNECTED_INFORMATION_REFERENCE


def test_no_real_outcome_input_exists_in_selection_signature() -> None:
    import inspect

    signature = inspect.signature(select_strongest_comparator)
    parameter_names = tuple(signature.parameters)
    assert "campaign" not in " ".join(parameter_names)
    assert "real" not in " ".join(parameter_names)


def test_seed_count_matches_development_roots() -> None:
    loaded = load_production_configuration()
    expected = len(loaded.values.randomness.synthetic_development_roots)
    assert composition_seed_count(expected) == expected
