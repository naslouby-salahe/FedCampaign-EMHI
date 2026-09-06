from dataclasses import dataclass

from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.domain.types import (
    Boolean,
    ClientId,
    EpochIndexValue,
    EvidenceFactor,
    LocalPolicyArtifact,
    Probability,
    RecordCount,
    ThresholdValue,
)


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
