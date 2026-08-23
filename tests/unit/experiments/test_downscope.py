import pytest

from fedcampaign_emhi.experiments.downscope import (
    failure_does_not_raise_thresholds,
    margin_preserved,
    no_post_hoc_grid_expansion,
    null_order_three_material_claim_state,
    order_three_estimator_failure_scope,
    primary_threshold_absent_state,
    secondary_ineligibility_contribution_state,
)


def test_order_three_feasibility_failure_downscopes_and_requires_statement() -> None:
    state = order_three_estimator_failure_scope(feasibility_passed=False, materiality_met=False)
    assert state.is_supported is False
    assert state.limitation_statement_required is True


def test_order_three_materiality_failure_is_not_tested_not_failed() -> None:
    state = order_three_estimator_failure_scope(feasibility_passed=True, materiality_met=False)
    assert state.is_supported is False
    assert state.is_not_tested is True
    assert state.limitation_statement_required is False


def test_order_three_full_support() -> None:
    state = order_three_estimator_failure_scope(feasibility_passed=True, materiality_met=True)
    assert state.is_supported is True


def test_primary_threshold_absence_makes_strict_odi_not_tested() -> None:
    state = primary_threshold_absent_state(has_eligible_threshold=False)
    assert state.is_not_tested is True
    assert state.is_supported is False
    with pytest.raises(ValueError):
        primary_threshold_absent_state(has_eligible_threshold=True)


def test_no_post_hoc_grid_expansion() -> None:
    original = 20
    assert no_post_hoc_grid_expansion(original, original) is True
    assert no_post_hoc_grid_expansion(original, 21) is False


def test_secondary_ineligibility_blocks_contribution_expansion() -> None:
    state = secondary_ineligibility_contribution_state(
        minimum_clients_met=False, minimum_benign_epochs_met=True
    )
    assert state.is_supported is False
    with pytest.raises(ValueError):
        secondary_ineligibility_contribution_state(
            minimum_clients_met=True, minimum_benign_epochs_met=True
        )


def test_null_real_order_three_contribution_forbids_material_claim() -> None:
    state = null_order_three_material_claim_state(True, 0.0)
    assert state.is_supported is False
    assert state.limitation_statement_required is True
    with pytest.raises(ValueError):
        null_order_three_material_claim_state(True, 0.01)


def test_failure_never_raises_thresholds_or_removes_difficulty() -> None:
    assert failure_does_not_raise_thresholds(0.5, 0.5) is True
    assert failure_does_not_raise_thresholds(0.5, 0.6) is False
    assert margin_preserved(0.2, 0.2) is True
    assert margin_preserved(0.2, 0.1) is False
