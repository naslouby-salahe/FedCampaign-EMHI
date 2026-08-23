from math import isfinite

from fedcampaign_emhi.domain.enums import ExperimentState
from fedcampaign_emhi.domain.types import BenignHorizon, FiniteFloat, RecordCount
from fedcampaign_emhi.evaluation.benign_horizons import horizons_are_nonoverlapping
from fedcampaign_emhi.evaluation.campaign_replay import CampaignReplayPlan
from fedcampaign_emhi.evaluation.records import (
    BenignHorizonEvaluationRecord,
    CampaignEvaluationRecord,
)


def campaign_record_state(record: CampaignEvaluationRecord) -> ExperimentState:
    if record.end_epoch < record.start_epoch:
        return ExperimentState.INVALID
    if not record.participating_clients:
        return ExperimentState.INVALID
    finite_values = (
        record.context_coverage,
        record.abstention_rate,
        record.server_latency_seconds,
        record.end_to_end_latency_seconds,
    )
    if not all(isfinite(value) for value in finite_values):
        return ExperimentState.INVALID
    return ExperimentState.COMPLETED


def benign_horizon_record_state(
    record: BenignHorizonEvaluationRecord,
) -> ExperimentState:
    finite_values = (record.threshold, record.context_coverage, record.abstention_rate)
    if not all(isfinite(value) for value in finite_values):
        return ExperimentState.INVALID
    return ExperimentState.COMPLETED


def required_record_completeness(
    observed_count: RecordCount, expected_count: RecordCount
) -> ExperimentState:
    if observed_count != expected_count:
        return ExperimentState.INVALID
    return ExperimentState.COMPLETED


def claim_metric_is_finite(value: FiniteFloat) -> ExperimentState:
    return ExperimentState.COMPLETED if isfinite(value) else ExperimentState.INVALID


def replay_plan_state(plan: CampaignReplayPlan) -> ExperimentState:
    if not plan.global_state_reset or not plan.local_persistence_reset:
        return ExperimentState.INVALID
    if not plan.campaign_epochs:
        return ExperimentState.INVALID
    return ExperimentState.COMPLETED


def benign_horizon_records_state(
    horizons: tuple[BenignHorizonEvaluationRecord, ...],
) -> ExperimentState:
    if not horizons:
        return ExperimentState.INVALID
    if any(benign_horizon_record_state(record) is ExperimentState.INVALID for record in horizons):
        return ExperimentState.INVALID
    return ExperimentState.COMPLETED


def no_imputation(values: tuple[FiniteFloat | None, ...]) -> ExperimentState:
    if any(value is None for value in values):
        return ExperimentState.INVALID
    return ExperimentState.COMPLETED


def nonoverlapping_horizon_state(
    horizons: tuple[BenignHorizon, ...],
) -> ExperimentState:
    return (
        ExperimentState.COMPLETED
        if horizons_are_nonoverlapping(horizons)
        else ExperimentState.INVALID
    )
