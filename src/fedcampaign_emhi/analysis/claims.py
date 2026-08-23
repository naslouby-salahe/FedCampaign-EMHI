from dataclasses import dataclass

from fedcampaign_emhi.domain.enums import ClaimIdentifier, ClaimState, OperatingPointState
from fedcampaign_emhi.domain.types import ComponentName, FiniteFloat, Probability
from fedcampaign_emhi.experiments.ablations import order_three_scope_gate
from fedcampaign_emhi.experiments.benign_robustness import (
    false_campaign_suppression_gate,
    power_loss_gate,
)
from fedcampaign_emhi.experiments.downscope import order_three_estimator_failure_scope
from fedcampaign_emhi.experiments.sequential_evidence import arl_zero_theorem_gate
from fedcampaign_emhi.experiments.strong_local import strong_local_odi_rate_gate


@dataclass(frozen=True)
class ClaimEvaluation:
    claim_identifier: ClaimIdentifier
    state: ClaimState
    state_reason: ComponentName


def evaluate_order_three_scope(
    estimator_feasibility_state: ClaimState,
    material_contribution: FiniteFloat,
    minimum_material_contribution: Probability,
) -> ClaimEvaluation:
    feasibility_passed = estimator_feasibility_state is ClaimState.SUPPORTED
    materiality_met = order_three_scope_gate(
        material_contribution, minimum_material_contribution
    )
    scope = order_three_estimator_failure_scope(feasibility_passed, materiality_met)
    if scope.is_supported:
        state = ClaimState.SUPPORTED
        reason = "estimator feasibility and real order-three materiality gates passed"
    elif not feasibility_passed:
        state = ClaimState.NOT_SUPPORTED
        reason = "order-three estimator feasibility gate failed"
    else:
        state = ClaimState.MECHANISM_ONLY
        reason = "controlled order-three mechanism passed without material real contribution"
    return ClaimEvaluation(
        claim_identifier=ClaimIdentifier.CLAIM_ORDER_THREE_SCOPE,
        state=state,
        state_reason=reason,
    )


def evaluate_strict_odi(
    operating_point_state: OperatingPointState,
    mean_strict_odi_rate: Probability,
    minimum_strict_odi_rate: Probability,
) -> ClaimEvaluation:
    if operating_point_state is OperatingPointState.UNAVAILABLE:
        return ClaimEvaluation(
            claim_identifier=ClaimIdentifier.CLAIM_STRICT_ODI,
            state=ClaimState.NOT_SUPPORTED,
            state_reason="no eligible calibrated finite-horizon operating point",
        )
    state = (
        ClaimState.SUPPORTED
        if mean_strict_odi_rate >= minimum_strict_odi_rate
        else ClaimState.NOT_SUPPORTED
    )
    return ClaimEvaluation(
        claim_identifier=ClaimIdentifier.CLAIM_STRICT_ODI,
        state=state,
        state_reason="strict ODI rate evaluated at an eligible calibrated operating point",
    )


def evaluate_strong_local_scope(
    mean_strict_odi_rate: Probability, minimum_strict_odi_rate: Probability
) -> ClaimEvaluation:
    supported = strong_local_odi_rate_gate(mean_strict_odi_rate, minimum_strict_odi_rate)
    return ClaimEvaluation(
        claim_identifier=ClaimIdentifier.CLAIM_STRICT_ODI,
        state=ClaimState.SUPPORTED if supported else ClaimState.NOT_SUPPORTED,
        state_reason="strong-local strict ODI materiality gate evaluated",
    )


def evaluate_operational_feasibility(
    false_campaign_suppression: Probability,
    minimum_false_campaign_suppression: Probability,
    power_loss: FiniteFloat,
    maximum_power_loss: Probability,
) -> ClaimEvaluation:
    suppression_passed = false_campaign_suppression_gate(
        false_campaign_suppression, minimum_false_campaign_suppression
    )
    power_passed = power_loss_gate(power_loss, maximum_power_loss)
    state = ClaimState.SUPPORTED if suppression_passed and power_passed else ClaimState.NOT_SUPPORTED
    return ClaimEvaluation(
        claim_identifier=ClaimIdentifier.CLAIM_OPERATIONAL_FEASIBILITY,
        state=state,
        state_reason="false-campaign suppression and detection-power gates evaluated jointly",
    )


def evaluate_sequential_consequence(
    observed_threshold: FiniteFloat,
    lower_theorem_bound: FiniteFloat,
) -> ClaimEvaluation:
    supported = arl_zero_theorem_gate(observed_threshold, lower_theorem_bound)
    return ClaimEvaluation(
        claim_identifier=ClaimIdentifier.CLAIM_SEQUENTIAL_CONSEQUENCE,
        state=ClaimState.SUPPORTED if supported else ClaimState.NOT_SUPPORTED,
        state_reason="sequential evidence lower-bound gate evaluated",
    )
