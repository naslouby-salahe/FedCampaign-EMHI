from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.types import FiniteFloat, Probability
from fedcampaign_emhi.experiments.primary_odi import (
    FullMethodSupportInputs,
    evaluate_full_method_support,
)


def build_inputs(
    heldout_pfa_upper_bound: Probability | None = None,
    mean_strict_odi_rate: Probability | None = None,
    paired_odi_advantage: FiniteFloat | None = None,
    median_lead_among_successes: FiniteFloat | None = None,
    directional_adjusted_p_value: Probability | None = None,
    full_operating_point_available: bool = True,
    comparator_operating_point_available: bool = True,
) -> FullMethodSupportInputs:
    loaded = load_production_configuration()
    finite_horizon = loaded.values.evidence.calibrated_finite_horizon
    materiality = loaded.values.claim_materiality.primary_real
    alpha = loaded.values.statistics.nominal_significance_alpha
    return FullMethodSupportInputs(
        heldout_pfa_upper_bound=(
            heldout_pfa_upper_bound
            if heldout_pfa_upper_bound is not None
            else finite_horizon.target_pfa
        ),
        target_pfa=finite_horizon.target_pfa,
        mean_strict_odi_rate=(
            mean_strict_odi_rate
            if mean_strict_odi_rate is not None
            else materiality.minimum_strict_odi_rate + 0.05
        ),
        minimum_strict_odi_rate=materiality.minimum_strict_odi_rate,
        paired_odi_advantage=(
            paired_odi_advantage
            if paired_odi_advantage is not None
            else materiality.minimum_odi_rate_advantage_over_order_at_most_two
        ),
        minimum_odi_advantage=materiality.minimum_odi_rate_advantage_over_order_at_most_two,
        median_lead_among_successes=(
            median_lead_among_successes
            if median_lead_among_successes is not None
            else materiality.minimum_median_operational_lead_epochs
        ),
        minimum_median_lead=materiality.minimum_median_operational_lead_epochs,
        directional_adjusted_p_value=(
            directional_adjusted_p_value if directional_adjusted_p_value is not None else alpha / 2
        ),
        nominal_alpha=alpha,
        full_operating_point_available=full_operating_point_available,
        comparator_operating_point_available=comparator_operating_point_available,
    )


def test_all_passing_inputs_yield_full_support() -> None:
    result = evaluate_full_method_support(build_inputs())
    assert result.all_criteria_pass
    assert result.failed_criteria == ()


def test_each_failed_criterion_is_reported_individually() -> None:
    finite_horizon = load_production_configuration().values.evidence.calibrated_finite_horizon
    pfa_fail = evaluate_full_method_support(
        build_inputs(heldout_pfa_upper_bound=finite_horizon.target_pfa + 0.01)
    )
    assert pfa_fail.failed_criteria == ("heldout_pfa",)
    rate_fail = evaluate_full_method_support(build_inputs(mean_strict_odi_rate=0.0))
    assert "strict_odi_rate" in rate_fail.failed_criteria
    advantage_fail = evaluate_full_method_support(build_inputs(paired_odi_advantage=-1.0))
    assert advantage_fail.failed_criteria == ("paired_odi_advantage",)
    lead_fail = evaluate_full_method_support(build_inputs(median_lead_among_successes=-5.0))
    assert lead_fail.failed_criteria == ("median_operational_lead",)


def test_directional_gate_uses_holm_adjusted_p_against_nominal_alpha() -> None:
    loaded = load_production_configuration()
    alpha = loaded.values.statistics.nominal_significance_alpha
    passing = evaluate_full_method_support(build_inputs(directional_adjusted_p_value=alpha - 0.001))
    assert passing.directional_gate_passes
    failing = evaluate_full_method_support(build_inputs(directional_adjusted_p_value=alpha))
    assert failing.directional_gate_passes is False


def test_missing_comparator_operating_point_blocks_support() -> None:
    result = evaluate_full_method_support(build_inputs(comparator_operating_point_available=False))
    assert result.all_criteria_pass is False
    assert result.failed_criteria == ("matched_operating_point",)


def test_multiple_failures_accumulate() -> None:
    result = evaluate_full_method_support(
        build_inputs(
            mean_strict_odi_rate=0.0,
            paired_odi_advantage=-1.0,
            full_operating_point_available=False,
        )
    )
    assert set(result.failed_criteria) == {
        "strict_odi_rate",
        "paired_odi_advantage",
        "matched_operating_point",
    }
