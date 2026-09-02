from dataclasses import dataclass
from math import isfinite

import numpy as np

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.types import (
    BettingLambda,
    Boolean,
    CompensatorValue,
    ESrThreshold,
    EvidenceClipBound,
    EvidenceFactor,
    PositiveEpochCount,
    RankValue,
    RecordCount,
    RestrictedAverageRunLength,
    SeedValue,
    SignedTheoremCoordinate,
)
from fedcampaign_emhi.emhi.evidence import (
    clip_statistic,
    signed_evidence_factor,
    signed_theorem_compensator,
)
from fedcampaign_emhi.emhi.sequential import next_global_state
from fedcampaign_emhi.emhi.structure import shifted_legendre_phi_one
from fedcampaign_emhi.emhi.thresholds import esr_threshold_from_arl_alpha
from fedcampaign_emhi.runtime import thirty_two_bit_seed


@dataclass(frozen=True)
class SignedTheoremSeedMetrics:
    restricted_arl: RestrictedAverageRunLength
    stopped_trajectory_count: RecordCount
    trajectory_count: RecordCount
    maximum_trajectory_epochs: PositiveEpochCount
    threshold: ESrThreshold
    compensator: CompensatorValue


@dataclass(frozen=True)
class SignedTheoremSeedResult:
    metrics: SignedTheoremSeedMetrics
    assumptions_hold: Boolean


def signed_theorem_coordinate(
    ranks: tuple[RankValue, RankValue, RankValue],
) -> SignedTheoremCoordinate:
    coordinate = 1.0
    for rank in ranks:
        coordinate *= shifted_legendre_phi_one(rank)
    return coordinate


def _trajectory_restricted_stop(
    generator: np.random.Generator,
    maximum_epochs: PositiveEpochCount,
    clip_bound: EvidenceClipBound,
    bet_lambda: BettingLambda,
    threshold: ESrThreshold,
) -> tuple[RecordCount, Boolean, Boolean]:
    state = 0.0
    assumptions_hold = True
    for epoch in range(maximum_epochs):
        ranks = (
            float(generator.random()),
            float(generator.random()),
            float(generator.random()),
        )
        coordinate = signed_theorem_coordinate(ranks)
        clipped = clip_statistic(coordinate, clip_bound)
        factor: EvidenceFactor = signed_evidence_factor(clipped, clip_bound, bet_lambda)
        assumptions_hold = assumptions_hold and (
            isfinite(coordinate)
            and isfinite(clipped)
            and -clip_bound <= clipped <= clip_bound
            and isfinite(factor)
            and factor >= 0.0
        )
        state = next_global_state(state, factor)
        if state >= threshold:
            return epoch + 1, True, assumptions_hold
    return maximum_epochs, False, assumptions_hold


def evaluate_signed_theorem_seed(
    config: ScientificConfig, seed: SeedValue
) -> SignedTheoremSeedResult:
    experiment = config.experiments.sequential_evidence_validation.signed_theorem
    evidence = config.evidence
    threshold = esr_threshold_from_arl_alpha(evidence.signed_theorem_sequential.arl_alpha)
    generator = np.random.default_rng(thirty_two_bit_seed(seed))
    restricted_stops: list[RecordCount] = []
    stopped: RecordCount = 0
    assumptions_hold = experiment.null_theta == 0.0
    compensator = signed_theorem_compensator(evidence.clip_bound, evidence.bet_lambda)
    for _trajectory in range(experiment.trajectories_per_seed):
        stop, did_stop, trajectory_assumptions_hold = _trajectory_restricted_stop(
            generator,
            experiment.maximum_trajectory_epochs,
            evidence.clip_bound,
            evidence.bet_lambda,
            threshold,
        )
        restricted_stops.append(stop)
        stopped += int(did_stop)
        assumptions_hold = assumptions_hold and trajectory_assumptions_hold
    return SignedTheoremSeedResult(
        metrics=SignedTheoremSeedMetrics(
            restricted_arl=sum(restricted_stops) / len(restricted_stops),
            stopped_trajectory_count=stopped,
            trajectory_count=experiment.trajectories_per_seed,
            maximum_trajectory_epochs=experiment.maximum_trajectory_epochs,
            threshold=threshold,
            compensator=compensator,
        ),
        assumptions_hold=assumptions_hold,
    )
