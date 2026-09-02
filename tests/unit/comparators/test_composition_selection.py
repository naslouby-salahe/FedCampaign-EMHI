from pathlib import Path

import pytest

from fedcampaign_emhi.comparators.contracts import native_target_order
from fedcampaign_emhi.comparators.fusion import (
    CompositionCandidateResult,
    CompositionSelectionInputs,
    build_composition_selection_record,
    candidate_is_eligible,
    materialize_composition_record,
    mean_standardized_error,
    median_runtime_seconds,
)
from fedcampaign_emhi.comparators.runtime import resolve_comparator_scoring_method
from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import CoalitionOrder, ExperimentName, MethodName
from fedcampaign_emhi.domain.types import Boolean
from fedcampaign_emhi.experiments.registry import (
    experiment_registry,
    resolve_experiment_name,
)


def test_native_target_order_mapping_is_locked() -> None:
    assert native_target_order_is(MethodName.CONDITIONAL_PAIR_DEPENDENCE, CoalitionOrder.TWO)
    assert native_target_order_is(
        MethodName.EXCLUSION_MATCHED_LANCASTER_TRIPLE, CoalitionOrder.THREE
    )
    assert native_target_order_is(MethodName.CONNECTED_INFORMATION_REFERENCE, CoalitionOrder.THREE)
    assert native_target_order_is(MethodName.D_VINE_CONDITIONAL_REFERENCE, CoalitionOrder.THREE)
    assert native_target_order_is(MethodName.CONDITIONAL_LOG_LINEAR_REFERENCE, CoalitionOrder.THREE)


def native_target_order_is(method: MethodName, order_value: CoalitionOrder) -> Boolean:
    order = native_target_order(method)
    return order is order_value


def test_eligibility_requires_all_three_conditions() -> None:
    loaded = load_production_configuration()
    finite_horizon = loaded.values.evidence.calibrated_finite_horizon
    passing = CompositionCandidateResult(
        method_name=MethodName.D_VINE_CONDITIONAL_REFERENCE,
        invariants_pass=True,
        calibration_succeeded=True,
        heldout_false_stops=0,
        heldout_horizons=59,
        mean_standardized_error=0.2,
        median_runtime_seconds=1.0,
    )
    assert candidate_is_eligible(
        passing, finite_horizon.calibration_confidence, finite_horizon.target_pfa
    )
    failed_invariants = CompositionCandidateResult(
        method_name=MethodName.D_VINE_CONDITIONAL_REFERENCE,
        invariants_pass=False,
        calibration_succeeded=True,
        heldout_false_stops=0,
        heldout_horizons=59,
        mean_standardized_error=0.2,
        median_runtime_seconds=1.0,
    )
    assert not candidate_is_eligible(
        failed_invariants, finite_horizon.calibration_confidence, finite_horizon.target_pfa
    )
    failed_calibration = CompositionCandidateResult(
        method_name=MethodName.D_VINE_CONDITIONAL_REFERENCE,
        invariants_pass=True,
        calibration_succeeded=False,
        heldout_false_stops=0,
        heldout_horizons=59,
        mean_standardized_error=0.2,
        median_runtime_seconds=1.0,
    )
    assert not candidate_is_eligible(
        failed_calibration, finite_horizon.calibration_confidence, finite_horizon.target_pfa
    )


def test_eligibility_rejects_pfa_above_target() -> None:
    loaded = load_production_configuration()
    finite_horizon = loaded.values.evidence.calibrated_finite_horizon
    too_many_stops = CompositionCandidateResult(
        method_name=MethodName.D_VINE_CONDITIONAL_REFERENCE,
        invariants_pass=True,
        calibration_succeeded=True,
        heldout_false_stops=1,
        heldout_horizons=59,
        mean_standardized_error=0.2,
        median_runtime_seconds=1.0,
    )
    assert not candidate_is_eligible(
        too_many_stops, finite_horizon.calibration_confidence, finite_horizon.target_pfa
    )


def test_mean_error_and_median_runtime_aggregation() -> None:
    assert mean_standardized_error((0.2, 0.4, 0.6)) == pytest.approx(0.4)
    assert median_runtime_seconds((3.0, 1.0, 2.0)) == 2.0
    assert median_runtime_seconds((4.0, 1.0, 2.0, 3.0)) == 2.5
    with pytest.raises(ValueError):
        mean_standardized_error(())
    with pytest.raises(ValueError):
        median_runtime_seconds(())


def test_selection_ignores_real_outcomes_and_uses_development_seeds() -> None:
    loaded = load_production_configuration()
    challenge = loaded.values.experiments.strong_comparator_composition_challenge
    registry = {c.experiment_name: c for c in experiment_registry(loaded.values)}
    contract = registry[ExperimentName.STRONG_COMPARATOR_COMPOSITION_CHALLENGE]
    assert contract.execution_roles == (loaded.profile.value,) or contract.execution_roles
    assert contract.methods == challenge.candidates
    assert contract.uses_real_seeds is False
    assert contract.uses_synthetic_seeds is True


def test_composition_record_materialization() -> None:
    loaded = load_production_configuration()
    filename = loaded.values.experiments.strong_comparator_composition_challenge.artifact_filename
    assert filename == "strongest-comparator-composition.json"
    record = materialize_composition_record(MethodName.D_VINE_CONDITIONAL_REFERENCE, filename)
    assert record.selected_method is MethodName.D_VINE_CONDITIONAL_REFERENCE
    assert record.native_target_order == CoalitionOrder.THREE
    assert record.artifact_filename == filename
    unscoped = materialize_composition_record(MethodName.RAW_MEAN_RANK_FUSION, filename)
    assert unscoped.native_target_order is None


def test_selection_artifact_contains_all_required_candidate_evidence() -> None:
    loaded = load_production_configuration()
    challenge = loaded.values.experiments.strong_comparator_composition_challenge
    samples = loaded.values.synthetic.sample_sizes
    finite_horizon = loaded.values.evidence.calibrated_finite_horizon
    inputs = CompositionSelectionInputs(
        reference_theta=loaded.values.generators.pure_polynomial.primary_reference_theta,
        error_tie_tolerance=challenge.error_tie_tolerance_standardized_units,
        runtime_tie_tolerance=challenge.runtime_tie_tolerance_seconds,
        calibration_horizons_per_seed=samples.finite_horizon_calibration_horizons_per_seed,
        heldout_null_horizons_per_seed=samples.finite_horizon_heldout_null_horizons_per_seed,
        timed_scoring_rows=samples.pure_order_independent_evaluation_samples_per_condition_seed,
        artifact_filename=challenge.artifact_filename,
    )
    candidates = (
        CompositionCandidateResult(
            MethodName.CONDITIONAL_PAIR_DEPENDENCE, True, True, 0, 59, 0.2, 2.0
        ),
        CompositionCandidateResult(
            MethodName.D_VINE_CONDITIONAL_REFERENCE, True, True, 0, 59, 0.1, 3.0
        ),
    )

    artifact = build_composition_selection_record(
        candidates,
        inputs,
        finite_horizon.calibration_confidence,
        finite_horizon.target_pfa,
        loaded.material_digest,
        (loaded.material_digest,),
    )

    assert artifact.selected_method is MethodName.D_VINE_CONDITIONAL_REFERENCE
    assert artifact.selected_native_order is CoalitionOrder.THREE
    assert artifact.eligible_candidates == tuple(candidate.method_name for candidate in candidates)
    assert len(artifact.null_pfa_results) == len(candidates)
    assert len(artifact.target_error_results) == len(candidates)
    assert len(artifact.runtime_tiebreak_results) == len(candidates)


def test_selected_comparator_cannot_fall_back_to_the_first_configured_candidate(
    tmp_path: Path,
) -> None:
    loaded = load_production_configuration()

    with pytest.raises(ValueError, match="validated composition artifact"):
        resolve_comparator_scoring_method(
            loaded, tmp_path, MethodName.SELECTED_STRONG_COMPARATOR_COMPOSITION
        )


def test_experiment_slugs_are_descriptive_kebab_case() -> None:
    for experiment in ExperimentName:
        slug = resolve_experiment_name(experiment.value)
        assert slug is experiment
        assert experiment.value == experiment.value.lower()
        assert " " not in experiment.value
        assert all(part.isalnum() for part in experiment.value.split("-"))
        assert not experiment.value[0].isdigit()


def test_condition_grids_live_in_registry_not_operator_supplied() -> None:
    loaded = load_production_configuration()
    registry_names = {c.experiment_name for c in experiment_registry(loaded.values)}
    assert registry_names == set(ExperimentName)
