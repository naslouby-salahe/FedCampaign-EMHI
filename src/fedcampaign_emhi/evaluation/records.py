from dataclasses import dataclass

from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    DatasetName,
    ExecutionRole,
    ExperimentName,
    MethodName,
    PartitionRole,
)
from fedcampaign_emhi.domain.types import (
    ClientId,
    EpochIndexValue,
    LatencySeconds,
    OdiIndicator,
    Probability,
    RecordCount,
    SeedValue,
    StrictOdiOutcome,
    ThresholdValue,
)
from fedcampaign_emhi.evaluation.metrics import strict_odi_outcome


@dataclass(frozen=True)
class CampaignEvaluationRecord:
    experiment_name: ExperimentName
    execution_role: ExecutionRole
    dataset_name: DatasetName
    method_name: MethodName
    seed: SeedValue
    start_epoch: EpochIndexValue
    end_epoch: EpochIndexValue
    participating_clients: tuple[ClientId, ...]
    global_stop_epoch: EpochIndexValue | None
    local_min_stop_epoch: EpochIndexValue | None
    strict_odi: OdiIndicator
    statistical_lead_epochs: EpochIndexValue | None
    operational_lead_epochs: EpochIndexValue | None
    global_detected_within_horizon: OdiIndicator
    local_detected_within_horizon: OdiIndicator
    decisive_order: CoalitionOrder | None
    context_coverage: Probability
    abstention_rate: Probability
    server_latency_seconds: LatencySeconds
    end_to_end_latency_seconds: LatencySeconds


@dataclass(frozen=True)
class BenignHorizonEvaluationRecord:
    experiment_name: ExperimentName
    execution_role: ExecutionRole
    dataset_name: DatasetName
    method_name: MethodName
    seed: SeedValue
    split_role: PartitionRole
    horizon_index: RecordCount
    threshold: ThresholdValue
    false_campaign: OdiIndicator
    first_stop_epoch: EpochIndexValue | None
    context_coverage: Probability
    abstention_rate: Probability


def odi_evaluation_record(
    global_stop_epoch: EpochIndexValue | None,
    local_stop_epochs: tuple[EpochIndexValue | None, ...],
) -> StrictOdiOutcome:
    return strict_odi_outcome(global_stop_epoch, local_stop_epochs)


def global_detection_without_odi(outcome: StrictOdiOutcome) -> bool:
    return outcome.global_detection_indicator == 1 and outcome.indicator == 0
