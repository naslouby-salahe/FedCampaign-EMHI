from dataclasses import dataclass

from fedcampaign_emhi.domain.types import ComponentName, FiniteFloat, Probability, RecordCount


@dataclass(frozen=True)
class ClaimState:
    claim_name: ComponentName
    is_supported: bool
    is_not_tested: bool
    limitation_statement_required: bool


def order_three_estimator_failure_scope(
    feasibility_passed: bool, materiality_met: bool
) -> ClaimState:
    if not feasibility_passed:
        return ClaimState(
            claim_name="Order-Three Scope",
            is_supported=False,
            is_not_tested=False,
            limitation_statement_required=True,
        )
    if not materiality_met:
        return ClaimState(
            claim_name="Order-Three Scope",
            is_supported=False,
            is_not_tested=True,
            limitation_statement_required=False,
        )
    return ClaimState(
        claim_name="Order-Three Scope",
        is_supported=True,
        is_not_tested=False,
        limitation_statement_required=False,
    )


def primary_threshold_absent_state(has_eligible_threshold: bool) -> ClaimState:
    if has_eligible_threshold:
        raise ValueError("threshold-absence state requires an absent eligible threshold")
    return ClaimState(
        claim_name="Strict ODI on TON_IoT Network",
        is_supported=False,
        is_not_tested=True,
        limitation_statement_required=False,
    )


def no_post_hoc_grid_expansion(
    original_grid_size: RecordCount, attempted_grid_size: RecordCount
) -> bool:
    return attempted_grid_size <= original_grid_size


def secondary_ineligibility_contribution_state(
    minimum_clients_met: bool, minimum_benign_epochs_met: bool
) -> ClaimState:
    if minimum_clients_met and minimum_benign_epochs_met:
        raise ValueError("contribution-expansion block requires unmet secondary requirements")
    return ClaimState(
        claim_name="Secondary Controlled-Trace Generalization",
        is_supported=False,
        is_not_tested=False,
        limitation_statement_required=False,
    )


def null_order_three_material_claim_state(
    synthetic_evidence_passes: bool, real_contribution: Probability
) -> ClaimState:
    del synthetic_evidence_passes
    if real_contribution > 0.0:
        raise ValueError("null-contribution state requires a non-positive real contribution")
    return ClaimState(
        claim_name="Real Order-3 Material Contribution",
        is_supported=False,
        is_not_tested=False,
        limitation_statement_required=True,
    )


def failure_does_not_raise_thresholds(
    original_minimum: Probability, post_failure_minimum: Probability
) -> bool:
    return post_failure_minimum <= original_minimum


def margin_preserved(pre_failure_margin: FiniteFloat, post_failure_margin: FiniteFloat) -> bool:
    return post_failure_margin >= pre_failure_margin
