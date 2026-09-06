from dataclasses import dataclass
from math import log, pi, sin, sqrt

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm

from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.domain.types import (
    BinCount,
    Boolean,
    ClientCount,
    Correlation,
    CosineSimilarity,
    DependenceMoment,
    FactorRank,
    GaussianCoordinate,
    JeffreysPseudocount,
    LogDensity,
    NonconformityScore,
    NumericalFloor,
    NumericalTolerance,
    Probability,
    ProbabilityMass,
    ProjectionNrmse,
    RankValue,
    RecordCount,
    SingularValue,
    SolverIterationLimit,
    StandardDeviation,
    StoppingTimeDifferenceEpochs,
)
from fedcampaign_emhi.emhi.innovations import (
    centered_scaled_coordinate,
    sample_mean,
    sample_standard_deviation,
)
from fedcampaign_emhi.emhi.structure import standard_normal_cdf
from fedcampaign_emhi.runtime import log_stage


def pair_dependence_moment(left_rank: RankValue, right_rank: RankValue) -> DependenceMoment:
    return ((2.0 * left_rank) - 1.0) * ((2.0 * right_rank) - 1.0)


def pair_dependence_nonconformity(
    moment: DependenceMoment,
    benign_mean: DependenceMoment,
    benign_deviation: StandardDeviation,
    scale_floor: NumericalFloor,
) -> NonconformityScore:
    standardized = centered_scaled_coordinate(moment, benign_mean, benign_deviation, scale_floor)
    if standardized < 0.0:
        return -standardized
    return standardized


def lancaster_triple_moment(
    first_rank: RankValue, second_rank: RankValue, third_rank: RankValue
) -> DependenceMoment:
    return ((2.0 * first_rank) - 1.0) * ((2.0 * second_rank) - 1.0) * ((2.0 * third_rank) - 1.0)


def lancaster_triple_nonconformity(
    moment: DependenceMoment,
    benign_mean: DependenceMoment,
    benign_deviation: StandardDeviation,
    scale_floor: NumericalFloor,
) -> NonconformityScore:
    standardized = centered_scaled_coordinate(moment, benign_mean, benign_deviation, scale_floor)
    if standardized < 0.0:
        return -standardized
    return standardized


@log_stage("comparators.dependence")
def fit_pair_dependence_reference(
    nuisance_pairs: tuple[tuple[RankValue, RankValue], ...],
) -> tuple[DependenceMoment, StandardDeviation]:
    if not nuisance_pairs:
        raise ValueError("pair-dependence reference requires nuisance-fit pairs")
    moments = tuple(pair_dependence_moment(left, right) for left, right in nuisance_pairs)
    return sample_mean(moments), sample_standard_deviation(moments)


@log_stage("comparators.dependence")
def fit_lancaster_triple_reference(
    nuisance_triples: tuple[tuple[RankValue, RankValue, RankValue], ...],
) -> tuple[DependenceMoment, StandardDeviation]:
    if not nuisance_triples:
        raise ValueError("Lancaster-triple reference requires nuisance-fit triples")
    moments = tuple(
        lancaster_triple_moment(first, second, third) for first, second, third in nuisance_triples
    )
    return sample_mean(moments), sample_standard_deviation(moments)


def uniform_probability_table(
    bin_count: BinCount,
) -> tuple[tuple[tuple[ProbabilityMass, ...], ...], ...]:
    cell = 1.0 / (bin_count**3)
    return tuple(
        tuple(tuple(cell for _i in range(bin_count)) for _j in range(bin_count))
        for _k in range(bin_count)
    )


def jeffreys_smoothed_probabilities(
    counts: tuple[tuple[tuple[ProbabilityMass, ...], ...], ...],
    pseudocount: JeffreysPseudocount,
) -> tuple[tuple[tuple[ProbabilityMass, ...], ...], ...]:
    total = 0.0
    smoothed: list[tuple[tuple[ProbabilityMass, ...], ...]] = []
    for first in counts:
        first_rows: list[tuple[ProbabilityMass, ...]] = []
        for second in first:
            row = tuple(cell + pseudocount for cell in second)
            first_rows.append(row)
            total += sum(row)
        smoothed.append(tuple(first_rows))
    if total <= 0.0:
        raise ValueError("Jeffreys-smoothed table mass must be positive")
    return tuple(tuple(tuple(cell / total for cell in row) for row in layer) for layer in smoothed)


def floored_probability_table(
    counts: tuple[tuple[tuple[ProbabilityMass, ...], ...], ...],
    probability_floor: NumericalFloor,
) -> tuple[tuple[tuple[ProbabilityMass, ...], ...], ...]:
    total = sum(sum(sum(row) for row in layer) for layer in counts)
    if total <= 0.0:
        raise ValueError("floored probability table requires positive total mass")
    floored: list[tuple[tuple[ProbabilityMass, ...], ...]] = []
    for layer in counts:
        floored_layer: list[tuple[ProbabilityMass, ...]] = []
        for row in layer:
            floored_layer.append(tuple(max(cell / total, probability_floor) for cell in row))
        floored.append(tuple(floored_layer))
    renormalize_total = sum(sum(sum(row) for row in layer) for layer in floored)
    return tuple(
        tuple(tuple(cell / renormalize_total for cell in row) for row in layer) for layer in floored
    )


def iterative_proportional_fitting_step(
    table: tuple[tuple[tuple[ProbabilityMass, ...], ...], ...],
    target_pair_ij: tuple[tuple[ProbabilityMass, ...], ...],
) -> tuple[tuple[tuple[ProbabilityMass, ...], ...], ...]:
    bin_count = len(table)
    updated = [[list(row) for row in layer] for layer in table]
    for i_index in range(bin_count):
        for j_index in range(bin_count):
            current = sum(updated[i_index][j_index][k_index] for k_index in range(bin_count))
            if current <= 0.0:
                continue
            scale = target_pair_ij[i_index][j_index] / current
            for k_index in range(bin_count):
                updated[i_index][j_index][k_index] *= scale
    return tuple(tuple(tuple(row) for row in layer) for layer in updated)


def _fit_ik_margin_step(
    table: tuple[tuple[tuple[ProbabilityMass, ...], ...], ...],
    target_pair_ik: tuple[tuple[ProbabilityMass, ...], ...],
) -> tuple[tuple[tuple[ProbabilityMass, ...], ...], ...]:
    bin_count = len(table)
    updated = [[list(row) for row in layer] for layer in table]
    for i_index in range(bin_count):
        for k_index in range(bin_count):
            current = sum(updated[i_index][j_index][k_index] for j_index in range(bin_count))
            if current <= 0.0:
                continue
            scale = target_pair_ik[i_index][k_index] / current
            for j_index in range(bin_count):
                updated[i_index][j_index][k_index] *= scale
    return tuple(tuple(tuple(row) for row in layer) for layer in updated)


def _fit_jk_margin_step(
    table: tuple[tuple[tuple[ProbabilityMass, ...], ...], ...],
    target_pair_jk: tuple[tuple[ProbabilityMass, ...], ...],
) -> tuple[tuple[tuple[ProbabilityMass, ...], ...], ...]:
    bin_count = len(table)
    updated = [[list(row) for row in layer] for layer in table]
    for j_index in range(bin_count):
        for k_index in range(bin_count):
            current = sum(updated[i_index][j_index][k_index] for i_index in range(bin_count))
            if current <= 0.0:
                continue
            scale = target_pair_jk[j_index][k_index] / current
            for i_index in range(bin_count):
                updated[i_index][j_index][k_index] *= scale
    return tuple(tuple(tuple(row) for row in layer) for layer in updated)


def ipf_converged(
    table: tuple[tuple[tuple[ProbabilityMass, ...], ...], ...],
    target_pair_ij: tuple[tuple[ProbabilityMass, ...], ...],
    maximum_marginal_absolute_error: NumericalTolerance,
) -> Boolean:
    bin_count = len(table)
    for i_index in range(bin_count):
        for j_index in range(bin_count):
            current = sum(table[i_index][j_index][k_index] for k_index in range(bin_count))
            if abs(current - target_pair_ij[i_index][j_index]) > maximum_marginal_absolute_error:
                return False
    return True


def _ik_margin_converged(
    table: tuple[tuple[tuple[ProbabilityMass, ...], ...], ...],
    target_pair_ik: tuple[tuple[ProbabilityMass, ...], ...],
    maximum_marginal_absolute_error: NumericalTolerance,
) -> Boolean:
    bin_count = len(table)
    for i_index in range(bin_count):
        for k_index in range(bin_count):
            current = sum(table[i_index][j_index][k_index] for j_index in range(bin_count))
            if abs(current - target_pair_ik[i_index][k_index]) > maximum_marginal_absolute_error:
                return False
    return True


def _jk_margin_converged(
    table: tuple[tuple[tuple[ProbabilityMass, ...], ...], ...],
    target_pair_jk: tuple[tuple[ProbabilityMass, ...], ...],
    maximum_marginal_absolute_error: NumericalTolerance,
) -> Boolean:
    bin_count = len(table)
    for j_index in range(bin_count):
        for k_index in range(bin_count):
            current = sum(table[i_index][j_index][k_index] for i_index in range(bin_count))
            if abs(current - target_pair_jk[j_index][k_index]) > maximum_marginal_absolute_error:
                return False
    return True


def pairwise_marginals(
    table: tuple[tuple[tuple[ProbabilityMass, ...], ...], ...],
) -> tuple[
    tuple[tuple[ProbabilityMass, ...], ...],
    tuple[tuple[ProbabilityMass, ...], ...],
    tuple[tuple[ProbabilityMass, ...], ...],
]:
    bin_count = len(table)
    target_ij = tuple(
        tuple(
            sum(table[i_index][j_index][k_index] for k_index in range(bin_count))
            for j_index in range(bin_count)
        )
        for i_index in range(bin_count)
    )
    target_ik = tuple(
        tuple(
            sum(table[i_index][j_index][k_index] for j_index in range(bin_count))
            for k_index in range(bin_count)
        )
        for i_index in range(bin_count)
    )
    target_jk = tuple(
        tuple(
            sum(table[i_index][j_index][k_index] for i_index in range(bin_count))
            for k_index in range(bin_count)
        )
        for j_index in range(bin_count)
    )
    return target_ij, target_ik, target_jk


@log_stage("comparators.dependence")
def fit_pairwise_maxent_table(
    empirical_joint: tuple[tuple[tuple[ProbabilityMass, ...], ...], ...],
    maximum_iterations: SolverIterationLimit,
    maximum_marginal_absolute_error: NumericalTolerance,
) -> tuple[tuple[tuple[ProbabilityMass, ...], ...], ...]:
    bin_count = len(empirical_joint)
    target_ij, target_ik, target_jk = pairwise_marginals(empirical_joint)
    table = uniform_probability_table(bin_count)
    for _iteration in range(maximum_iterations):
        table = iterative_proportional_fitting_step(table, target_ij)
        table = _fit_ik_margin_step(table, target_ik)
        table = _fit_jk_margin_step(table, target_jk)
        if (
            ipf_converged(table, target_ij, maximum_marginal_absolute_error)
            and _ik_margin_converged(table, target_ik, maximum_marginal_absolute_error)
            and _jk_margin_converged(table, target_jk, maximum_marginal_absolute_error)
        ):
            return table
    raise ValueError("pairwise maximum-entropy IPF did not converge within configured iterations")


def empirical_triple_joint_counts(
    triples: tuple[tuple[RankValue, RankValue, RankValue], ...],
    bin_count: BinCount,
) -> tuple[tuple[tuple[ProbabilityMass, ...], ...], ...]:
    if not triples:
        raise ValueError("empirical joint counts require nuisance-fit triples")
    counts = [
        [[0.0 for _k in range(bin_count)] for _j in range(bin_count)] for _i in range(bin_count)
    ]
    for left, middle, right in triples:
        i_index = min(int(left * bin_count), bin_count - 1)
        j_index = min(int(middle * bin_count), bin_count - 1)
        k_index = min(int(right * bin_count), bin_count - 1)
        counts[i_index][j_index][k_index] += 1.0
    return tuple(tuple(tuple(row) for row in layer) for layer in counts)


def standard_normal_quantile(
    rank: RankValue, rank_clip_epsilon: NumericalFloor
) -> GaussianCoordinate:
    lower = rank_clip_epsilon
    upper = 1.0 - rank_clip_epsilon
    clipped = min(max(rank, lower), upper)
    return float(norm.ppf(clipped))


def gaussian_h_function(
    left_rank: RankValue,
    conditioning_rank: RankValue,
    correlation: Correlation,
    rank_clip_epsilon: NumericalFloor,
) -> RankValue:
    left = standard_normal_quantile(left_rank, rank_clip_epsilon)
    conditioned = standard_normal_quantile(conditioning_rank, rank_clip_epsilon)
    residual_scale = sqrt(1.0 - (correlation**2))
    return standard_normal_cdf((left - (correlation * conditioned)) / residual_scale)


def kendall_tau_b(
    left_series: tuple[RankValue, ...], right_series: tuple[RankValue, ...]
) -> Correlation:
    if len(left_series) != len(right_series) or len(left_series) < 2:
        raise ValueError("Kendall's tau requires two aligned series of at least two observations")
    left = np.asarray(left_series, dtype=np.float64)
    right = np.asarray(right_series, dtype=np.float64)
    observation_count = left.shape[0]
    concordant = 0
    discordant = 0
    tied_left_only = 0
    tied_right_only = 0
    for index in range(observation_count - 1):
        left_delta: NDArray[np.float64] = left[index + 1 :] - left[index]
        right_delta: NDArray[np.float64] = right[index + 1 :] - right[index]
        sign_product: NDArray[np.float64] = np.sign(left_delta) * np.sign(right_delta)
        left_tied: NDArray[np.bool_] = np.isclose(left_delta, 0.0, rtol=0.0, atol=0.0)
        right_tied: NDArray[np.bool_] = np.isclose(right_delta, 0.0, rtol=0.0, atol=0.0)
        concordant += int(np.sum(sign_product > 0.0))
        discordant += int(np.sum(sign_product < 0.0))
        tied_left_only += int(np.sum(np.logical_and(left_tied, np.logical_not(right_tied))))
        tied_right_only += int(np.sum(np.logical_and(right_tied, np.logical_not(left_tied))))
    total_pairs = observation_count * (observation_count - 1) // 2
    denominator = sqrt(float(total_pairs - tied_left_only) * float(total_pairs - tied_right_only))
    if denominator <= 0.0:
        return 0.0
    tau = (concordant - discordant) / denominator
    return max(-1.0, min(1.0, tau))


def kendall_tau_correlation(
    left_series: tuple[RankValue, ...], right_series: tuple[RankValue, ...]
) -> Correlation:
    tau = kendall_tau_b(left_series, right_series)
    rho = sin((pi / 2.0) * tau)
    return max(-1.0, min(1.0, rho))


def gaussian_copula_log_density(
    left_rank: RankValue,
    right_rank: RankValue,
    correlation: Correlation,
    rank_clip_epsilon: NumericalFloor,
) -> LogDensity:
    left = standard_normal_quantile(left_rank, rank_clip_epsilon)
    right = standard_normal_quantile(right_rank, rank_clip_epsilon)
    one_minus_rho_squared = 1.0 - (correlation**2)
    quadratic = (
        (correlation**2) * ((left**2) + (right**2)) - (2.0 * correlation * left * right)
    ) / (2.0 * one_minus_rho_squared)
    return (-0.5 * log(one_minus_rho_squared)) - quadratic


@dataclass(frozen=True)
class DVineFittedCorrelations:
    left_conditioning_correlation: Correlation
    right_conditioning_correlation: Correlation
    second_tree_correlation: Correlation


@log_stage("comparators.dependence")
def fit_d_vine_correlations(
    nuisance_triples: tuple[tuple[RankValue, RankValue, RankValue], ...],
    rank_clip_epsilon: NumericalFloor,
) -> DVineFittedCorrelations:
    if not nuisance_triples:
        raise ValueError("D-vine reference requires nuisance-fit triples")
    left = tuple(triple[0] for triple in nuisance_triples)
    middle = tuple(triple[1] for triple in nuisance_triples)
    right = tuple(triple[2] for triple in nuisance_triples)
    rho_left = kendall_tau_correlation(left, middle)
    rho_right = kendall_tau_correlation(middle, right)
    left_pseudo = tuple(
        gaussian_h_function(value, condition, rho_left, rank_clip_epsilon)
        for value, condition in zip(left, middle, strict=True)
    )
    right_pseudo = tuple(
        gaussian_h_function(value, condition, rho_right, rank_clip_epsilon)
        for value, condition in zip(right, middle, strict=True)
    )
    rho_second_tree = kendall_tau_correlation(left_pseudo, right_pseudo)
    return DVineFittedCorrelations(
        left_conditioning_correlation=rho_left,
        right_conditioning_correlation=rho_right,
        second_tree_correlation=rho_second_tree,
    )


def d_vine_conditional_reference_score(
    triple: tuple[RankValue, RankValue, RankValue],
    fitted: DVineFittedCorrelations,
    rank_clip_epsilon: NumericalFloor,
) -> NonconformityScore:
    left, middle, right = triple
    left_pseudo = gaussian_h_function(
        left, middle, fitted.left_conditioning_correlation, rank_clip_epsilon
    )
    right_pseudo = gaussian_h_function(
        right, middle, fitted.right_conditioning_correlation, rank_clip_epsilon
    )
    density = gaussian_copula_log_density(
        left_pseudo, right_pseudo, fitted.second_tree_correlation, rank_clip_epsilon
    )
    return abs(density)


def selected_factor_rank(
    singular_values: tuple[SingularValue, ...],
    cumulative_variance_target: Probability,
    fallback_rank: FactorRank,
    candidate_ranks: tuple[FactorRank, ...],
) -> FactorRank:
    total = sum(value * value for value in singular_values)
    if total <= 0.0:
        return fallback_rank
    cumulative = 0.0
    for rank, value in enumerate(singular_values, start=1):
        cumulative += (value * value) / total
        if rank in candidate_ranks and cumulative >= cumulative_variance_target:
            return rank
    if fallback_rank in candidate_ranks:
        return fallback_rank
    return candidate_ranks[-1]


@dataclass(frozen=True)
class GlobalFactorFittedBasis:
    client_means: tuple[RankValue, ...]
    factor_loadings: tuple[tuple[RankValue, ...], ...]


@log_stage("comparators.dependence")
def fit_global_factor_basis(
    nuisance_rank_matrix: tuple[tuple[RankValue, ...], ...],
    cumulative_variance_target: Probability,
    fallback_rank: FactorRank,
    candidate_ranks: tuple[FactorRank, ...],
) -> GlobalFactorFittedBasis:
    matrix = np.asarray(nuisance_rank_matrix, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] < 2:
        raise ValueError("global factor basis requires a two-dimensional nuisance-fit panel")
    means = matrix.mean(axis=0, keepdims=True)
    centered = matrix - means
    _left, singular, right = np.linalg.svd(centered, full_matrices=False)
    factor_rank = selected_factor_rank(
        tuple(float(value) for value in singular),
        cumulative_variance_target,
        fallback_rank,
        candidate_ranks,
    )
    factors = right[:factor_rank]
    return GlobalFactorFittedBasis(
        client_means=tuple(float(value) for value in means[0]),
        factor_loadings=tuple(tuple(float(value) for value in row) for row in factors),
    )


def global_factor_residual_score(
    row: tuple[RankValue, ...],
    fitted: GlobalFactorFittedBasis,
) -> NonconformityScore:
    if len(row) != len(fitted.client_means):
        raise ValueError("scored row must match the fitted global factor client dimension")
    centered = np.asarray(row, dtype=np.float64) - np.asarray(fitted.client_means, dtype=np.float64)
    factors = np.asarray(fitted.factor_loadings, dtype=np.float64)
    projection = centered @ factors.T @ factors
    residual = centered - projection
    return float(np.linalg.norm(residual))


def target_coalition_for_order(order: CoalitionOrder, client_count: ClientCount) -> RecordCount:
    order_size = order
    if order_size > client_count:
        raise ValueError("target coalition exceeds the selected client count")
    target: RecordCount = order_size
    return target


def nrmse_equivalence_criterion(nrmse_upper: ProjectionNrmse, margin: ProjectionNrmse) -> Boolean:
    return nrmse_upper < margin


def cosine_equivalence_criterion(
    mean_cosine: CosineSimilarity, minimum: CosineSimilarity
) -> Boolean:
    return mean_cosine >= minimum


def stopping_time_equivalence_criterion(
    ci_lower: StoppingTimeDifferenceEpochs,
    ci_upper: StoppingTimeDifferenceEpochs,
    interval_lower: StoppingTimeDifferenceEpochs,
    interval_upper: StoppingTimeDifferenceEpochs,
) -> Boolean:
    return ci_lower >= interval_lower and ci_upper <= interval_upper


def pfa_prerequisite_criterion(null_pfa_upper: Probability, target_pfa: Probability) -> Boolean:
    return null_pfa_upper <= target_pfa
