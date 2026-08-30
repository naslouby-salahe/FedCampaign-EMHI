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
    Boolean,
    ClientId,
    EpochIndexValue,
    EvidenceFactor,
    LatencySeconds,
    LocalPolicyArtifact,
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


@dataclass(frozen=True)
class CoalitionEpochEvidence:
    coalition_client_ids: tuple[ClientId, ...]
    coalition_order: CoalitionOrder
    evidence_factor: EvidenceFactor


@dataclass(frozen=True)
class EpochOperationalEvidence:
    epoch_index: EpochIndexValue
    global_evidence_factor: EvidenceFactor
    order_factors: tuple[tuple[CoalitionOrder, EvidenceFactor], ...]
    coalition_factors: tuple[CoalitionEpochEvidence, ...]
    materially_active_client_ids: tuple[ClientId, ...]
    scored_coalition_count: RecordCount
    eligible_coalition_count: RecordCount


@dataclass(frozen=True)
class SequentialTrajectory:
    epochs: tuple[EpochOperationalEvidence, ...]
    support_predicates: tuple[Boolean, ...]


@dataclass(frozen=True)
class CalibratedGlobalOperatingPoint:
    threshold: ThresholdValue | None
    calibration_false_stop_counts: tuple[RecordCount, ...]
    calibration_horizon_count: RecordCount
    heldout_false_stop_count: RecordCount
    heldout_horizon_count: RecordCount
    heldout_upper_pfa: Probability | None


@dataclass(frozen=True)
class ClientLocalOperatingPoint:
    client_id: ClientId
    policy: LocalPolicyArtifact | None
    calibration_false_stop_count: RecordCount | None
    heldout_false_stop_count: RecordCount | None
    heldout_horizon_count: RecordCount
    heldout_upper_pfa: Probability | None


@dataclass(frozen=True)
class OperationalCalibration:
    global_operating_point: CalibratedGlobalOperatingPoint
    local_operating_points: tuple[ClientLocalOperatingPoint, ...]


def odi_evaluation_record(
    global_stop_epoch: EpochIndexValue | None,
    local_stop_epochs: tuple[EpochIndexValue | None, ...],
) -> StrictOdiOutcome:
    return strict_odi_outcome(global_stop_epoch, local_stop_epochs)


def global_detection_without_odi(outcome: StrictOdiOutcome) -> Boolean:
    return outcome.global_detection_indicator == 1 and outcome.indicator == 0
