import pytest

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import ExperimentName
from fedcampaign_emhi.experiments.registry import (
    FullMethodSupportInputs,
    evaluate_full_method_support,
    experiment_registry,
    matched_operating_point_requirement,
    median_of,
)


def test_registry_contains_roadmap_experiments() -> None:
    loaded = load_production_configuration()
    names = {contract.experiment_name for contract in experiment_registry(loaded.values)}
    assert names == set(ExperimentName)


def test_evaluate_full_method_support_passes_when_every_criterion_holds() -> None:
    result = evaluate_full_method_support(
        FullMethodSupportInputs(
            heldout_pfa_upper_bound=0.01,
            target_pfa=0.05,
            mean_strict_odi_rate=0.4,
            minimum_strict_odi_rate=0.2,
            paired_odi_advantage=0.1,
            minimum_odi_advantage=0.05,
            median_lead_among_successes=3.0,
            minimum_median_lead=2.0,
            directional_adjusted_p_value=0.01,
            nominal_alpha=0.05,
            full_operating_point_available=True,
            comparator_operating_point_available=True,
        )
    )
    assert result.all_criteria_pass is True
    assert result.pfa_criterion_satisfied is True


def test_evaluate_full_method_support_fails_when_heldout_pfa_exceeds_target() -> None:
    result = evaluate_full_method_support(
        FullMethodSupportInputs(
            heldout_pfa_upper_bound=0.06,
            target_pfa=0.05,
            mean_strict_odi_rate=0.4,
            minimum_strict_odi_rate=0.2,
            paired_odi_advantage=0.1,
            minimum_odi_advantage=0.05,
            median_lead_among_successes=3.0,
            minimum_median_lead=2.0,
            directional_adjusted_p_value=0.01,
            nominal_alpha=0.05,
            full_operating_point_available=True,
            comparator_operating_point_available=True,
        )
    )
    assert result.all_criteria_pass is False
    assert result.pfa_criterion_satisfied is False


def test_median_of_rejects_empty_values() -> None:
    with pytest.raises(ValueError):
        median_of(())


def test_matched_operating_point_requirement_requires_both_methods() -> None:
    assert matched_operating_point_requirement(True, True) is True
    assert matched_operating_point_requirement(True, False) is False
    assert matched_operating_point_requirement(False, True) is False
    assert matched_operating_point_requirement(False, False) is False
