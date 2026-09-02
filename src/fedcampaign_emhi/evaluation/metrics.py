from math import log, sqrt
from typing import cast

from sklearn import metrics as sklearn_metrics

from fedcampaign_emhi.domain.types import (
    Attenuation,
    AttenuationDifference,
    Boolean,
    CensoredPlotEpoch,
    ClientCount,
    CoalitionCount,
    CoalitionOrder,
    CommonModeSuppression,
    CosineSimilarity,
    DetectionRateLoss,
    DetectorScore,
    EffectCoefficient,
    EpochIndexValue,
    EvidenceFactor,
    EvidenceShare,
    InnovationCoordinate,
    InnovationMean,
    LogEvidenceGrowth,
    MaybeDefinedMetric,
    MetricRate,
    NumericalFloor,
    NumericalTolerance,
    OdiIndicator,
    PositiveEpochCount,
    Probability,
    ProjectionNrmse,
    RankEstimationError,
    RankValue,
    RecordCount,
    RuntimeSeconds,
    StandardDeviation,
    StandardizedAtomCoordinate,
    StandardizedDrift,
    StandardizedNullBias,
    StoppingTimeDifference,
    StrictOdiOutcome,
    ThroughputPerSecond,
)
from fedcampaign_emhi.emhi.structure import coalition_count


def earliest_local_stop(
    local_stop_epochs: tuple[EpochIndexValue | None, ...],
) -> EpochIndexValue | None:
    finite_local = [epoch for epoch in local_stop_epochs if epoch is not None]
    if not finite_local:
        return None
    return min(finite_local)


def strict_odi_outcome(
    global_stop_epoch: EpochIndexValue | None,
    local_stop_epochs: tuple[EpochIndexValue | None, ...],
) -> StrictOdiOutcome:
    earliest_local = earliest_local_stop(local_stop_epochs)
    global_detection = 0 if global_stop_epoch is None else 1
    if global_stop_epoch is None or earliest_local is None:
        indicator = 0
    else:
        indicator = int(global_stop_epoch < earliest_local)
    return StrictOdiOutcome(
        global_stop_epoch=global_stop_epoch,
        earliest_local_stop_epoch=earliest_local,
        indicator=indicator,
        global_detection_indicator=global_detection,
    )


def censored_plot_value(
    horizon_epochs: PositiveEpochCount, no_stop_plot_offset_epochs: PositiveEpochCount
) -> CensoredPlotEpoch:
    return horizon_epochs + no_stop_plot_offset_epochs


def seed_level_odi_rate(odi_indicators: tuple[OdiIndicator, ...]) -> Probability:
    if not odi_indicators:
        raise ValueError("seed-level ODI rate requires at least one campaign")
    return sum(odi_indicators) / len(odi_indicators)


def campaign_detection_rate(
    global_stop_epochs: tuple[EpochIndexValue | None, ...], horizon_epochs: PositiveEpochCount
) -> Probability:
    if not global_stop_epochs:
        raise ValueError("campaign detection rate requires the complete campaign registry")
    return sum(
        1 for epoch in global_stop_epochs if epoch is not None and epoch <= horizon_epochs
    ) / len(global_stop_epochs)


def finite_horizon_pfa_point_estimate(
    false_stop_count: RecordCount, benign_horizon_count: RecordCount
) -> Probability:
    if benign_horizon_count <= 0:
        raise ValueError("finite-horizon PFA requires at least one benign horizon")
    return false_stop_count / benign_horizon_count


FALSE_CAMPAIGN_RATE_EPOCH_SCALE = 10 * 1000


def false_campaigns_per_ten_thousand_benign_epochs(
    false_declarations: RecordCount, benign_epochs: RecordCount
) -> MetricRate:
    if benign_epochs <= 0:
        raise ValueError("false campaigns per 10k requires at least one benign epoch")
    return FALSE_CAMPAIGN_RATE_EPOCH_SCALE * false_declarations / benign_epochs


def self_explanation_attenuation(
    residual_derivative: EffectCoefficient,
    direct_derivative: EffectCoefficient,
    metric_denominator_floor: NumericalFloor,
) -> Attenuation:
    denominator = abs(direct_derivative) + metric_denominator_floor
    return 1.0 - abs(residual_derivative) / denominator


def self_explanation_material_contrast(
    inclusive_attenuation: Attenuation, exact_attenuation: Attenuation
) -> AttenuationDifference:
    return inclusive_attenuation - exact_attenuation


def mean_log_evidence_growth(
    log_evidence_factors: tuple[LogEvidenceGrowth, ...],
) -> LogEvidenceGrowth:
    if not log_evidence_factors:
        raise ValueError("mean log-evidence growth requires an attack interval")
    return sum(log_evidence_factors) / len(log_evidence_factors)


def proper_subset_drift(
    mean_under_alternative: tuple[InnovationMean, ...],
    mean_under_null: tuple[InnovationMean, ...],
    null_trace_sqrt: StandardDeviation,
    metric_denominator_floor: NumericalFloor,
) -> StandardizedDrift:
    if len(mean_under_alternative) != len(mean_under_null):
        raise ValueError("proper-subset drift means must be aligned")
    squared = sum(
        (alternative - null) ** 2
        for alternative, null in zip(mean_under_alternative, mean_under_null, strict=True)
    )
    denominator = max(null_trace_sqrt, metric_denominator_floor)
    return sqrt(squared) / denominator


def maximal_proper_subset_drift(subset_drifts: tuple[StandardizedDrift, ...]) -> StandardizedDrift:
    if not subset_drifts:
        raise ValueError("maximal proper-subset drift requires at least one proper subset")
    return max(subset_drifts)


def target_order_drift(
    alternative_mean: InnovationMean,
    null_mean: InnovationMean,
    null_deviation: StandardDeviation,
    metric_denominator_floor: NumericalFloor,
) -> StandardizedDrift:
    return (alternative_mean - null_mean) / max(null_deviation, metric_denominator_floor)


def order_evidence_share(
    order_factor: EvidenceFactor,
    all_order_factors: tuple[EvidenceFactor, ...],
    metric_denominator_floor: NumericalFloor,
) -> EvidenceShare:
    return order_factor / (sum(all_order_factors) + metric_denominator_floor)


def decisive_order(
    stop_epoch_factors: tuple[tuple[CoalitionOrder, EvidenceFactor], ...],
    deterministic_comparison_tolerance: NumericalTolerance,
) -> CoalitionOrder | None:
    eligible = [(order, factor) for order, factor in stop_epoch_factors if factor > 1.0]
    if not eligible:
        return None
    best = max(eligible, key=lambda pair: pair[1])
    best_log = log(best[1])
    tied = [
        order
        for order, factor in eligible
        if abs(log(factor) - best_log) <= deterministic_comparison_tolerance
    ]
    return min(tied)


def atom_nrmse(
    emhi_atoms: tuple[tuple[StandardizedAtomCoordinate, ...], ...],
    hofd_atoms: tuple[tuple[StandardizedAtomCoordinate, ...], ...],
    metric_denominator_floor: NumericalFloor,
) -> ProjectionNrmse:
    from fedcampaign_emhi.emhi.evidence import euclidean_norm

    if len(emhi_atoms) != len(hofd_atoms) or not emhi_atoms:
        raise ValueError("atom NRMSE requires aligned nonempty atoms")
    difference = sqrt(
        sum(
            euclidean_norm(tuple(left - right for left, right in zip(emhi, hofd, strict=True))) ** 2
            for emhi, hofd in zip(emhi_atoms, hofd_atoms, strict=True)
        )
        / len(emhi_atoms)
    )
    reference = sqrt(sum(euclidean_norm(atom) ** 2 for atom in emhi_atoms) / len(emhi_atoms))
    return difference / max(reference, metric_denominator_floor)


def atom_cosine_similarity(
    emhi_atoms: tuple[tuple[StandardizedAtomCoordinate, ...], ...],
    hofd_atoms: tuple[tuple[StandardizedAtomCoordinate, ...], ...],
    metric_denominator_floor: NumericalFloor,
) -> CosineSimilarity:
    from fedcampaign_emhi.emhi.evidence import euclidean_norm

    if len(emhi_atoms) != len(hofd_atoms) or not emhi_atoms:
        raise ValueError("atom cosine similarity requires aligned nonempty atoms")
    inner = sum(
        sum(left * right for left, right in zip(emhi, hofd, strict=True))
        for emhi, hofd in zip(emhi_atoms, hofd_atoms, strict=True)
    )
    return inner / max(
        sqrt(sum(euclidean_norm(atom) ** 2 for atom in emhi_atoms))
        * sqrt(sum(euclidean_norm(atom) ** 2 for atom in hofd_atoms)),
        metric_denominator_floor,
    )


def paired_stopping_time_difference(
    emhi_stop: EpochIndexValue, comparison_stop: EpochIndexValue
) -> StoppingTimeDifference:
    return emhi_stop - comparison_stop


def paired_detection_indicator_difference(
    emhi_detected: Boolean, comparison_detected: Boolean
) -> OdiIndicator:
    return int(emhi_detected) - int(comparison_detected)


def pfa_difference(emhi_pfa: Probability, comparison_pfa: Probability) -> MetricRate:
    return emhi_pfa - comparison_pfa


def conditional_rank_mae(
    estimated_ranks: tuple[RankValue, ...], truth_ranks: tuple[RankValue, ...]
) -> RankEstimationError:
    if len(estimated_ranks) != len(truth_ranks):
        raise ValueError("conditional-rank MAE requires aligned rank samples")
    if not estimated_ranks:
        raise ValueError("conditional-rank MAE requires at least one sample")
    absolute = sum(
        abs(estimate - truth) for estimate, truth in zip(estimated_ranks, truth_ranks, strict=True)
    )
    return absolute / len(estimated_ranks)


def projection_nrmse(
    fitted_projections: tuple[tuple[InnovationCoordinate, ...], ...],
    population_projections: tuple[tuple[InnovationCoordinate, ...], ...],
    tensor_rows: tuple[tuple[InnovationCoordinate, ...], ...],
    metric_denominator_floor: NumericalFloor,
) -> ProjectionNrmse:
    from fedcampaign_emhi.emhi.evidence import euclidean_norm

    lengths = {len(fitted_projections), len(population_projections), len(tensor_rows)}
    if len(lengths) != 1:
        raise ValueError("projection NRMSE requires the same independent evaluation rows")
    row_count = len(tensor_rows)
    if row_count == 0:
        raise ValueError("projection NRMSE requires at least one evaluation row")
    residual = sqrt(
        sum(
            euclidean_norm(tuple(fitted - truth for fitted, truth in zip(fit, pop, strict=True)))
            ** 2
            for fit, pop in zip(fitted_projections, population_projections, strict=True)
        )
        / row_count
    )
    reference = sqrt(sum(euclidean_norm(row) ** 2 for row in tensor_rows) / row_count)
    return residual / (reference + metric_denominator_floor)


def standardized_null_bias(
    mean_atom: tuple[InnovationMean, ...],
    covariance_trace_sqrt: StandardDeviation,
    metric_denominator_floor: NumericalFloor,
) -> StandardizedNullBias:
    from fedcampaign_emhi.emhi.evidence import euclidean_norm

    return euclidean_norm(mean_atom) / max(covariance_trace_sqrt, metric_denominator_floor)


def context_coverage(
    supported_coalition_epochs: RecordCount, eligible_coalition_epochs: RecordCount
) -> Probability:
    if eligible_coalition_epochs <= 0:
        raise ValueError("context coverage requires at least one eligible coalition-epoch")
    return supported_coalition_epochs / eligible_coalition_epochs


def abstention_rate(context_coverage_value: Probability) -> Probability:
    return 1.0 - context_coverage_value


def numerical_failure_rate(failing_fits: RecordCount, attempted_fits: RecordCount) -> Probability:
    if attempted_fits <= 0:
        raise ValueError("numerical failure rate requires at least one attempted fit")
    return failing_fits / attempted_fits


def common_mode_suppression(
    emhi_pfa: Probability,
    raw_mean_pfa: Probability,
    metric_denominator_floor: NumericalFloor,
) -> CommonModeSuppression:
    return 1.0 - emhi_pfa / (raw_mean_pfa + metric_denominator_floor)


def outside_conditioning_power_loss(
    no_outside_context_detection_rate: Probability, emhi_detection_rate: Probability
) -> DetectionRateLoss:
    return no_outside_context_detection_rate - emhi_detection_rate


def auroc(scores: tuple[DetectorScore, ...], labels: tuple[Boolean, ...]) -> MaybeDefinedMetric:
    if len(scores) != len(labels):
        raise ValueError("AUROC requires aligned scores and labels")
    positives = sum(labels)
    if positives == 0 or positives == len(labels):
        return MaybeDefinedMetric.not_defined()
    return MaybeDefinedMetric.defined(
        float(cast(float, sklearn_metrics.roc_auc_score(list(labels), list(scores))))
    )


def auprc(scores: tuple[DetectorScore, ...], labels: tuple[Boolean, ...]) -> MaybeDefinedMetric:
    if len(scores) != len(labels):
        raise ValueError("AUPRC requires aligned scores and labels")
    positives = sum(labels)
    if positives == 0 or positives == len(labels):
        return MaybeDefinedMetric.not_defined()
    return MaybeDefinedMetric.defined(
        float(cast(float, sklearn_metrics.average_precision_score(list(labels), list(scores))))
    )


def registry_coalition_count(
    client_count: ClientCount, maximum_order: CoalitionOrder
) -> CoalitionCount:
    return coalition_count(client_count, maximum_order)


APPLICATION_PAYLOAD_BYTES_PER_CLIENT_PER_EPOCH = 20


def application_payload_bytes_per_epoch(client_count: ClientCount) -> RecordCount:
    return APPLICATION_PAYLOAD_BYTES_PER_CLIENT_PER_EPOCH * client_count


def throughput(
    coalitions_scored: RecordCount, server_compute_seconds: RuntimeSeconds
) -> ThroughputPerSecond:
    if server_compute_seconds <= 0.0:
        raise ValueError("throughput requires a positive server compute time")
    return coalitions_scored / server_compute_seconds
