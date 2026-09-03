from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import sqrt
from pathlib import Path
from time import perf_counter

from fedcampaign_emhi.artifacts.records import (
    BenignHorizonRecord,
    BenignPartitionRecord,
    ClientDetectorScoreStream,
    DatasetSplitRecord,
    DetectorScoreArtifactRecord,
)
from fedcampaign_emhi.comparators.contracts import native_target_order
from fedcampaign_emhi.comparators.runtime import (
    ComparatorFittedState,
    fit_comparator_state,
    score_comparator_ranks,
)
from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.detection import score_exceeds_threshold
from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    ContextMethodName,
    DatasetName,
    DetectorFamily,
    ExecutionRole,
    MethodName,
    SupportState,
)
from fedcampaign_emhi.domain.types import (
    Boolean,
    ClientCount,
    ClientId,
    ComponentName,
    CusumState,
    DetectorScore,
    FalseAlarmRate,
    PositiveEpochCount,
    RecordCount,
    RuntimeSeconds,
    SeedCoordinate,
    SeedDerivationIdentity,
    SeedValue,
    StandardizedDrift,
    StandardizedError,
    ThresholdValue,
)
from fedcampaign_emhi.emhi.calibration import build_emhi_fit_artifact
from fedcampaign_emhi.emhi.structure import build_marginal_rank_artifact
from fedcampaign_emhi.emhi.thresholds import select_calibrated_threshold
from fedcampaign_emhi.evaluation.metrics import (
    maximal_proper_subset_drift,
    proper_subset_drift,
    target_order_drift,
)
from fedcampaign_emhi.evaluation.sequential import (
    calibrate_global_operating_point,
    coalition_evidence_at_epoch,
)
from fedcampaign_emhi.experiments.synthetic import (
    composition_reference_cell,
    composition_reference_rows,
)
from fedcampaign_emhi.runtime import derive_component_seed, deterministic_digest
from fedcampaign_emhi.synthetic.generators import (
    equally_spaced_loadings,
    generate_common_mode_scores,
    generate_unit_variance_autoregressive_latent,
)
from fedcampaign_emhi.synthetic.pure_order import (
    PureOrderCell,
    PureOrderDriftMetrics,
    sample_generator_row,
    sample_independent_uniform_ranks,
)
from fedcampaign_emhi.synthetic.sequential import SignedTheoremSeedMetrics


@dataclass(frozen=True)
class FiniteHorizonSeedMetrics:
    calibrated_threshold: ThresholdValue | None
    calibration_horizon_count: RecordCount
    heldout_horizon_count: RecordCount
    heldout_false_stop_count: RecordCount
    heldout_upper_pfa: FalseAlarmRate | None


@dataclass(frozen=True)
class FiniteHorizonSeedResult:
    metrics: FiniteHorizonSeedMetrics
    assumptions_hold: Boolean


@dataclass(frozen=True)
class SignedTheoremObservation:
    execution_role: ExecutionRole
    seed: SeedValue
    metric: SignedTheoremSeedMetrics
    diagnostic_path: Path


@dataclass(frozen=True)
class FiniteHorizonObservation:
    execution_role: ExecutionRole
    seed: SeedValue
    metric: FiniteHorizonSeedMetrics
    diagnostic_path: Path


@dataclass(frozen=True)
class CompositionCandidateObservation:
    method_name: MethodName
    seed: SeedValue
    standardized_target_order_error: StandardizedError
    metric: CompositionCandidateSeedMetrics
    diagnostic_path: Path


def _seed(seed: SeedValue, component: ComponentName, horizon: SeedValue) -> SeedValue:
    return derive_component_seed(
        SeedDerivationIdentity(
            base_seed=seed,
            component_name=component,
            dataset=None,
            client_ids=(),
            coalition_ids=(),
            condition_coordinates=(SeedCoordinate(name="horizon", scalar=horizon),),
        )
    )


def _block(
    config: ScientificConfig,
    client_count: ClientCount,
    epoch_count: PositiveEpochCount,
    seed: SeedValue,
) -> tuple[tuple[DetectorScore, ...], ...]:
    latent = generate_unit_variance_autoregressive_latent(
        epoch_count, config.generators.common_mode.latent_ar_coefficient, _seed(seed, "latent", 0)
    )
    return generate_common_mode_scores(
        latent,
        equally_spaced_loadings(
            client_count,
            config.generators.common_mode.client_loading_minimum,
            config.generators.common_mode.client_loading_maximum,
        ),
        config.generators.common_mode.client_noise_standard_deviation,
        _seed(seed, "noise", 0),
    )


def evaluate_finite_horizon_common_mode_seed(
    config: ScientificConfig, seed: SeedValue
) -> FiniteHorizonSeedResult:
    client_count = config.experiments.pure_order_separation_validation.primary_client_count
    client_ids: tuple[ClientId, ...] = tuple(
        f"synthetic-common-mode-client-{index}" for index in range(client_count)
    )
    nuisance_count = config.synthetic.sample_sizes.generic_nuisance_fit_epochs
    warmup, length = (
        config.campaign.prestart_warmup_epochs,
        config.campaign.evaluation_horizon_epochs,
    )
    calibration_count = config.synthetic.sample_sizes.finite_horizon_calibration_horizons_per_seed
    heldout_count = config.synthetic.sample_sizes.finite_horizon_heldout_null_horizons_per_seed
    specifications = tuple((True, index) for index in range(calibration_count)) + tuple(
        (False, index) for index in range(heldout_count)
    )
    blocks = [_block(config, client_count, nuisance_count, _seed(seed, "nuisance", 0))]
    blocks.extend(
        _block(
            config,
            client_count,
            warmup + length,
            _seed(seed, "calibration" if calibration else "heldout", index),
        )
        for calibration, index in specifications
    )
    rows = tuple(row for block in blocks for row in block)
    indexes = tuple(range(len(rows)))
    fingerprint = deterministic_digest(
        {"producer": "finite-horizon-common-mode", "seed": seed, "client_count": client_count}
    )
    scores = DetectorScoreArtifactRecord(
        dataset_name=DatasetName.TON_IOT_NETWORK,
        root_seed=seed,
        selected_client_ids=client_ids,
        client_streams=tuple(
            ClientDetectorScoreStream(
                client_id=client_id,
                detector_family=DetectorFamily.ISOLATION_FOREST,
                detector_seed=seed,
                epoch_indexes=indexes,
                scores=tuple(row[index] for row in rows),
            )
            for index, client_id in enumerate(client_ids)
        ),
        dependency_fingerprint=fingerprint,
    )
    nuisance_epochs = tuple(range(nuisance_count))
    split = DatasetSplitRecord(
        dataset_name=DatasetName.TON_IOT_NETWORK,
        selected_client_ids=client_ids,
        eligible_client_ids=client_ids,
        support_state=SupportState.SUPPORTED,
        detector_fit_epochs=nuisance_epochs,
        nuisance_fit_epochs=nuisance_epochs,
        threshold_calibration_epochs=(),
        heldout_benign_epochs=(),
    )
    ranks = build_marginal_rank_artifact(
        scores, nuisance_epochs, config.context.rank_clip_epsilon, fingerprint
    )
    fit = build_emhi_fit_artifact(
        config,
        scores,
        ranks,
        split,
        MethodName.FULL_FEDCAMPAIGN_EMHI,
        ContextMethodName.EXACT_COALITION_EXCLUSION,
        CoalitionOrder(config.study.maximum_coalition_order),
        config.basis.primary_size,
        config.context.primary_cell_count,
        True,
        False,
        fingerprint,
    )
    offset = nuisance_count
    calibration_horizons: list[BenignHorizonRecord] = []
    heldout_horizons: list[BenignHorizonRecord] = []
    for calibration, _index in specifications:
        scored = tuple(range(offset + warmup, offset + warmup + length))
        (calibration_horizons if calibration else heldout_horizons).append(
            BenignHorizonRecord(start_epoch=scored[0], epoch_indexes=scored)
        )
        offset += warmup + length
    operating = calibrate_global_operating_point(
        config,
        ranks,
        fit,
        BenignPartitionRecord(
            dataset_name=DatasetName.TON_IOT_NETWORK,
            calibration_horizons=tuple(calibration_horizons),
            heldout_horizons=tuple(heldout_horizons),
        ),
    )
    metrics = FiniteHorizonSeedMetrics(
        calibrated_threshold=operating.threshold,
        calibration_horizon_count=operating.calibration_horizon_count,
        heldout_horizon_count=operating.heldout_horizon_count,
        heldout_false_stop_count=operating.heldout_false_stop_count,
        heldout_upper_pfa=operating.heldout_upper_pfa,
    )
    return FiniteHorizonSeedResult(
        metrics=metrics,
        assumptions_hold=(
            metrics.calibration_horizon_count == calibration_count
            and metrics.heldout_horizon_count == heldout_count
            and (metrics.calibrated_threshold is None or metrics.heldout_upper_pfa is not None)
        ),
    )


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
    fitted_state: ComparatorFittedState | None,
) -> tuple[DetectorScore, ...]:
    cusum_state: tuple[CusumState, ...] = ()
    scores: list[DetectorScore] = []
    for epoch_seed in horizon_epoch_seeds:
        row = sample_independent_uniform_ranks(client_count, epoch_seed)
        score, cusum_state = score_comparator_ranks(
            method_name, row[:order], config, cusum_state, fitted_state
        )
        scores.append(score)
    return tuple(scores)


def _horizon_stop_indicators(
    scores: tuple[DetectorScore, ...], thresholds: tuple[ThresholdValue, ...]
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
    nuisance_rows = tuple(
        sample_independent_uniform_ranks(client_count, seed + index)[:order]
        for index in range(sample_count)
    )
    fitted_state = fit_comparator_state(method_name, nuisance_rows, config)
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
            fitted_state,
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
                fitted_state,
            )
            if any(score_exceeds_threshold(score, selected) for score in horizon_scores):
                heldout_false_stop_count += 1
    reference_cell = composition_reference_cell(method_name, order, config)
    reference_rows = composition_reference_rows(reference_cell, client_count, seed, sample_count)
    for row in reference_rows:
        score_comparator_ranks(method_name, row[:order], config, (), fitted_state)
    started = perf_counter()
    for row in reference_rows:
        score_comparator_ranks(method_name, row[:order], config, (), fitted_state)
    elapsed = perf_counter() - started
    return CompositionCandidateSeedMetrics(
        calibrated_threshold=selected,
        calibration_horizon_count=calibration_horizon_count,
        heldout_horizon_count=heldout_horizon_count,
        heldout_false_stop_count=heldout_false_stop_count,
        scoring_runtime_seconds=elapsed,
    )


@dataclass(frozen=True)
class FittedPureOrderResult:
    metrics: PureOrderDriftMetrics
    artifact_path_complete: Boolean


def evaluate_comparator_pure_order_cell(
    config: ScientificConfig, cell: PureOrderCell, seed: SeedValue
) -> PureOrderDriftMetrics | None:
    if emhi_method_settings(cell.method) is not None:
        return None
    native_order = native_target_order(cell.method)
    if native_order is not None and native_order is not cell.target_order:
        return None
    client_count = config.experiments.pure_order_separation_validation.primary_client_count
    count = (
        config.synthetic.sample_sizes.pure_order_independent_evaluation_samples_per_condition_seed
    )
    null_rows = tuple(
        sample_independent_uniform_ranks(client_count, seed + index) for index in range(count)
    )
    alternative_rows = tuple(
        sample_generator_row(cell, client_count, seed + count + index) for index in range(count)
    )
    fitted_state = fit_comparator_state(
        cell.method,
        tuple(row[: cell.target_order] for row in null_rows),
        config,
    )
    null_scores = tuple(
        score_comparator_ranks(cell.method, row[: cell.target_order], config, (), fitted_state)[0]
        for row in null_rows
    )
    alternative_scores = tuple(
        score_comparator_ranks(cell.method, row[: cell.target_order], config, (), fitted_state)[0]
        for row in alternative_rows
    )
    null_mean = sum(null_scores) / len(null_scores)
    null_deviation = sqrt(sum((value - null_mean) ** 2 for value in null_scores) / len(null_scores))
    return PureOrderDriftMetrics(
        maximum_proper_subset_standardized_drift=0.0,
        target_order_standardized_drift=(
            sum(alternative_scores) / len(alternative_scores) - null_mean
        )
        / max(null_deviation, config.numerics.metric_denominator_floor),
        proper_subset_scoring_available=False,
    )


def emhi_method_settings(
    method: MethodName,
) -> tuple[ContextMethodName, CoalitionOrder, Boolean] | None:
    if method is MethodName.FULL_FEDCAMPAIGN_EMHI:
        return ContextMethodName.EXACT_COALITION_EXCLUSION, CoalitionOrder.THREE, True
    if method is MethodName.EXCLUSION_MATCHED_ORDER_ONE_EMHI:
        return ContextMethodName.EXACT_COALITION_EXCLUSION, CoalitionOrder.ONE, True
    if method is MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI:
        return ContextMethodName.EXACT_COALITION_EXCLUSION, CoalitionOrder.TWO, True
    if method is MethodName.INCLUSIVE_CONTEXT_FULL_HIERARCHY:
        return ContextMethodName.INCLUSIVE_CONTEXT, CoalitionOrder.THREE, True
    if method is MethodName.LEAVE_ONE_OUT_INSUFFICIENT_EXCLUSION:
        return ContextMethodName.LEAVE_ONE_OUT_INSUFFICIENT_EXCLUSION, CoalitionOrder.THREE, True
    if method is MethodName.PARTIAL_COALITION_EXCLUSION:
        return ContextMethodName.PARTIAL_COALITION_EXCLUSION, CoalitionOrder.THREE, True
    if method is MethodName.NO_PROPER_SUBSET_PURIFICATION:
        return ContextMethodName.EXACT_COALITION_EXCLUSION, CoalitionOrder.THREE, False
    if method is MethodName.NO_OUTSIDE_CONTEXT_FULL_HIERARCHY:
        return ContextMethodName.NO_OUTSIDE_CONTEXT, CoalitionOrder.THREE, True
    return None


def evaluate_fitted_pure_order_cell(
    config: ScientificConfig, cell: PureOrderCell, seed: SeedValue
) -> FittedPureOrderResult | None:
    settings = emhi_method_settings(cell.method)
    if settings is None:
        return None
    context_method, maximum_order, purification = settings
    if cell.target_order > maximum_order:
        return FittedPureOrderResult(PureOrderDriftMetrics(0.0, 0.0, True), True)
    client_count = config.experiments.pure_order_separation_validation.primary_client_count
    nuisance_count = config.synthetic.sample_sizes.generic_nuisance_fit_epochs
    evaluation_count = (
        config.synthetic.sample_sizes.pure_order_independent_evaluation_samples_per_condition_seed
    )
    null_evaluation = tuple(
        sample_independent_uniform_ranks(client_count, seed + nuisance_count + index)
        for index in range(evaluation_count)
    )
    alternative = tuple(
        sample_generator_row(cell, client_count, seed + nuisance_count + evaluation_count + index)
        for index in range(evaluation_count)
    )
    rows = (
        tuple(
            sample_independent_uniform_ranks(client_count, seed + index)
            for index in range(nuisance_count)
        )
        + null_evaluation
        + alternative
    )
    client_ids: tuple[ClientId, ...] = tuple(
        f"synthetic-pure-order-{index}" for index in range(client_count)
    )
    epochs = tuple(range(len(rows)))
    fingerprint = deterministic_digest(
        {"producer": "pure-order-artifact", "seed": seed, "method": cell.method.value}
    )
    scores = DetectorScoreArtifactRecord(
        dataset_name=DatasetName.TON_IOT_NETWORK,
        root_seed=seed,
        selected_client_ids=client_ids,
        client_streams=tuple(
            ClientDetectorScoreStream(
                client_id=client_id,
                detector_family=DetectorFamily.ISOLATION_FOREST,
                detector_seed=seed,
                epoch_indexes=epochs,
                scores=tuple(row[index] for row in rows),
            )
            for index, client_id in enumerate(client_ids)
        ),
        dependency_fingerprint=fingerprint,
    )
    nuisance_epochs = tuple(range(nuisance_count))
    split = DatasetSplitRecord(
        dataset_name=DatasetName.TON_IOT_NETWORK,
        selected_client_ids=client_ids,
        eligible_client_ids=client_ids,
        support_state=SupportState.SUPPORTED,
        detector_fit_epochs=nuisance_epochs,
        nuisance_fit_epochs=nuisance_epochs,
        threshold_calibration_epochs=(),
        heldout_benign_epochs=(),
    )
    ranks = build_marginal_rank_artifact(
        scores, nuisance_epochs, config.context.rank_clip_epsilon, fingerprint
    )
    fit = build_emhi_fit_artifact(
        config,
        scores,
        ranks,
        split,
        cell.method,
        context_method,
        maximum_order,
        config.basis.primary_size,
        config.context.primary_cell_count,
        purification,
        False,
        fingerprint,
    )

    def standardized_drift(coalition_ids: tuple[ClientId, ...]) -> StandardizedDrift | None:
        coalition_fit = next(
            (
                candidate
                for candidate in fit.coalition_fits
                if candidate.coalition_client_ids == coalition_ids
            ),
            None,
        )
        if coalition_fit is None:
            return None
        null_scores = tuple(
            coalition_evidence_at_epoch(config, ranks, fit, coalition_fit, epoch)
            for epoch in range(nuisance_count, nuisance_count + evaluation_count)
        )
        alternative_scores = tuple(
            coalition_evidence_at_epoch(config, ranks, fit, coalition_fit, epoch)
            for epoch in range(nuisance_count + evaluation_count, len(rows))
        )
        if any(value is None for value in (*null_scores, *alternative_scores)):
            return None
        resolved_null = tuple(value for value in null_scores if value is not None)
        resolved_alternative = tuple(value for value in alternative_scores if value is not None)
        mean = sum(resolved_null) / len(resolved_null)
        deviation = sqrt(sum((value - mean) ** 2 for value in resolved_null) / len(resolved_null))
        return target_order_drift(
            sum(resolved_alternative) / len(resolved_alternative),
            mean,
            deviation,
            config.numerics.metric_denominator_floor,
        )

    target_ids = client_ids[: cell.target_order]
    target_drift = standardized_drift(target_ids)
    subset_drifts = tuple(
        drift
        for size in range(1, len(target_ids))
        for subset in combinations(target_ids, size)
        for drift in (standardized_drift(subset),)
        if drift is not None
    )
    expected_subset_count = (2 ** len(target_ids)) - 2
    if target_drift is None or len(subset_drifts) != expected_subset_count:
        return FittedPureOrderResult(PureOrderDriftMetrics(0.0, 0.0, False), False)
    return FittedPureOrderResult(
        PureOrderDriftMetrics(
            maximal_proper_subset_drift(
                tuple(
                    proper_subset_drift(
                        (drift,),
                        (0.0,),
                        1.0,
                        config.numerics.metric_denominator_floor,
                    )
                    for drift in subset_drifts
                )
            ),
            target_drift,
            True,
        ),
        True,
    )
