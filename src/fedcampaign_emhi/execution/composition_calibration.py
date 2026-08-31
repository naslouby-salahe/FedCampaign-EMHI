from dataclasses import dataclass
from time import perf_counter

from fedcampaign_emhi.comparators.contracts import native_target_order
from fedcampaign_emhi.comparators.runtime import score_comparator_ranks
from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.detection.local_policy import score_exceeds_threshold
from fedcampaign_emhi.domain.enums import CoalitionOrder, MethodName
from fedcampaign_emhi.domain.types import (
    Boolean,
    ClientCount,
    FiniteFloat,
    RecordCount,
    RuntimeSeconds,
    SeedValue,
    ThresholdValue,
)
from fedcampaign_emhi.emhi.thresholds import select_calibrated_threshold
from fedcampaign_emhi.experiments.producers import (
    composition_reference_cell,
    composition_reference_rows,
)
from fedcampaign_emhi.synthetic.pure_order import sample_independent_uniform_ranks


@dataclass(frozen=True)
class CompositionCandidateSeedMetrics:
    calibrated_threshold: ThresholdValue | None
    calibration_horizon_count: RecordCount
    heldout_horizon_count: RecordCount
    heldout_false_stop_count: RecordCount
    scoring_runtime_seconds: RuntimeSeconds


def _horizon_scores(
    method_name: MethodName,
    order: CoalitionOrder,
    client_count: ClientCount,
    config: ScientificConfig,
    horizon_epoch_seeds: tuple[SeedValue, ...],
) -> tuple[FiniteFloat, ...]:
    cusum_state: tuple[FiniteFloat, ...] = ()
    scores: list[FiniteFloat] = []
    for epoch_seed in horizon_epoch_seeds:
        row = sample_independent_uniform_ranks(client_count, epoch_seed)
        score, cusum_state = score_comparator_ranks(
            method_name, row[: int(order)], config, cusum_state
        )
        scores.append(score)
    return tuple(scores)


def _horizon_stop_indicators(
    scores: tuple[FiniteFloat, ...], thresholds: tuple[ThresholdValue, ...]
) -> tuple[Boolean, ...]:
    return tuple(
        any(score_exceeds_threshold(score, threshold) for score in scores)
        for threshold in thresholds
    )


def evaluate_composition_candidate_seed(
    config: ScientificConfig, method_name: MethodName, seed: SeedValue
) -> CompositionCandidateSeedMetrics:
    order = native_target_order(method_name)
    if order is None:
        raise ValueError("composition calibration requires a native-order candidate")
    client_count = config.experiments.pure_order_separation_validation.primary_client_count
    sample_count = (
        config.synthetic.sample_sizes.pure_order_independent_evaluation_samples_per_condition_seed
    )
    horizon_length = config.campaign.evaluation_horizon_epochs
    calibration_horizon_count = (
        config.synthetic.sample_sizes.finite_horizon_calibration_horizons_per_seed
    )
    heldout_horizon_count = (
        config.synthetic.sample_sizes.finite_horizon_heldout_null_horizons_per_seed
    )
    thresholds = config.evidence.calibrated_finite_horizon.threshold_candidates
    epoch_offset = 2 * sample_count
    calibration_scores = tuple(
        _horizon_scores(
            method_name,
            order,
            client_count,
            config,
            tuple(
                seed + epoch_offset + horizon_index * horizon_length + epoch_index
                for epoch_index in range(horizon_length)
            ),
        )
        for horizon_index in range(calibration_horizon_count)
    )
    epoch_offset += calibration_horizon_count * horizon_length
    calibration_stop_counts = [0 for _ in thresholds]
    for horizon_scores in calibration_scores:
        for index, stopped in enumerate(_horizon_stop_indicators(horizon_scores, thresholds)):
            if stopped:
                calibration_stop_counts[index] += 1
    selected = select_calibrated_threshold(
        thresholds,
        tuple(calibration_stop_counts),
        calibration_horizon_count,
        config.evidence.calibrated_finite_horizon.calibration_confidence,
        config.evidence.calibrated_finite_horizon.target_pfa,
    )
    heldout_false_stop_count: RecordCount = 0
    if selected is not None:
        for horizon_index in range(heldout_horizon_count):
            horizon_scores = _horizon_scores(
                method_name,
                order,
                client_count,
                config,
                tuple(
                    seed + epoch_offset + horizon_index * horizon_length + epoch_index
                    for epoch_index in range(horizon_length)
                ),
            )
            if any(score_exceeds_threshold(score, selected) for score in horizon_scores):
                heldout_false_stop_count += 1
    reference_cell = composition_reference_cell(method_name, order, config)
    reference_rows = composition_reference_rows(reference_cell, client_count, seed, sample_count)
    for row in reference_rows:
        score_comparator_ranks(method_name, row[: int(order)], config)
    started = perf_counter()
    for row in reference_rows:
        score_comparator_ranks(method_name, row[: int(order)], config)
    elapsed = perf_counter() - started
    return CompositionCandidateSeedMetrics(
        calibrated_threshold=selected,
        calibration_horizon_count=calibration_horizon_count,
        heldout_horizon_count=heldout_horizon_count,
        heldout_false_stop_count=heldout_false_stop_count,
        scoring_runtime_seconds=elapsed,
    )
