from dataclasses import dataclass
from itertools import combinations
from math import sqrt

from fedcampaign_emhi.artifacts.records import (
    ClientDetectorScoreStream,
    DatasetSplitRecord,
    DetectorScoreArtifactRecord,
)
from fedcampaign_emhi.comparators.contracts import native_target_order
from fedcampaign_emhi.comparators.runtime import score_comparator_ranks
from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import (
    ClaimState,
    CoalitionOrder,
    ContextMethodName,
    DatasetName,
    DetectorFamily,
    MethodName,
)
from fedcampaign_emhi.domain.types import ClientId, FiniteFloat, SeedValue
from fedcampaign_emhi.emhi.innovation_calibration import build_emhi_fit_artifact
from fedcampaign_emhi.emhi.ranks import build_marginal_rank_artifact
from fedcampaign_emhi.evaluation.campaign_replay import coalition_evidence_at_epoch
from fedcampaign_emhi.runtime.determinism import deterministic_digest
from fedcampaign_emhi.synthetic.pure_order import (
    PureOrderCell,
    PureOrderDriftMetrics,
    sample_generator_row,
    sample_independent_uniform_ranks,
)


@dataclass(frozen=True)
class FittedPureOrderResult:
    metrics: PureOrderDriftMetrics
    artifact_path_complete: bool


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
    null_scores = tuple(
        score_comparator_ranks(cell.method, row[: int(cell.target_order)], config)[0]
        for row in null_rows
    )
    alternative_scores = tuple(
        score_comparator_ranks(cell.method, row[: int(cell.target_order)], config)[0]
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
) -> tuple[ContextMethodName, CoalitionOrder, bool] | None:
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
        claim_state=ClaimState.SUPPORTED,
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

    def standardized_drift(coalition_ids: tuple[ClientId, ...]) -> FiniteFloat | None:
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
        return (sum(resolved_alternative) / len(resolved_alternative) - mean) / max(
            deviation, config.numerics.metric_denominator_floor
        )

    target_ids = client_ids[: int(cell.target_order)]
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
        PureOrderDriftMetrics(max(abs(drift) for drift in subset_drifts), target_drift, True),
        True,
    )
