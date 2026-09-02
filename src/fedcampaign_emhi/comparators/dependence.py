from dataclasses import dataclass
from math import sqrt

import numpy as np
from scipy.stats import norm

from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.domain.types import (
    BasisCoordinate,
    BasisSize,
    BinCount,
    Boolean,
    ClientCount,
    ClientId,
    Correlation,
    CosineSimilarity,
    DependenceMoment,
    DesignColumnCount,
    FactorRank,
    GaussianCoordinate,
    InnovationCoordinate,
    IpfIterationLimit,
    JeffreysPseudocount,
    NonconformityScore,
    NumericalFloor,
    NumericalTolerance,
    Probability,
    ProbabilityMass,
    ProjectionNrmse,
    RankValue,
    RecordCount,
    RidgePenalty,
    SingularValue,
    StandardDeviation,
    StandardizedAtomCoordinate,
    StoppingTimeDifferenceEpochs,
)
from fedcampaign_emhi.emhi.innovations import centered_scaled_coordinate, projection_residual
from fedcampaign_emhi.emhi.projection import (
    proper_subset_design_column_count,
    ridge_coefficient_matrix,
)
from fedcampaign_emhi.emhi.structure import standard_normal_cdf


def hofd_atom_rows(
    tensor_rows: tuple[tuple[InnovationCoordinate, ...], ...],
    design_rows: tuple[tuple[BasisCoordinate, ...], ...],
    ridge_penalty: RidgePenalty,
    relative_singular_cutoff: NumericalFloor,
) -> tuple[tuple[InnovationCoordinate, ...], ...]:
    coefficients = ridge_coefficient_matrix(
        design_rows, tensor_rows, ridge_penalty, relative_singular_cutoff
    )
    residuals: list[tuple[InnovationCoordinate, ...]] = []
    for tensor_row, design_row in zip(tensor_rows, design_rows, strict=True):
        residuals.append(projection_residual(tensor_row, coefficients, design_row))
    return tuple(residuals)


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


def maximum_ipf_iterations_bound(configured_limit: IpfIterationLimit) -> IpfIterationLimit:
    return configured_limit


def log_linear_includes_intercept() -> Boolean:
    return True


def log_linear_includes_singletons() -> Boolean:
    return True


def log_linear_includes_pairs() -> Boolean:
    return True


def log_linear_includes_triple() -> Boolean:
    return False


def log_linear_design_column_count(basis_size: BasisSize) -> DesignColumnCount:
    return proper_subset_design_column_count(CoalitionOrder.THREE, basis_size)


def lexicographic_vine_order(client_ids: tuple[ClientId, ...]) -> tuple[ClientId, ...]:
    if len(client_ids) != 3:
        raise ValueError("D-vine triples must contain exactly three clients")
    ordered = tuple(sorted(client_ids))
    return ordered


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


def global_factor_residual_scores(
    rank_matrix: tuple[tuple[RankValue, ...], ...],
    factor_rank: FactorRank,
) -> tuple[NonconformityScore, ...]:
    matrix = np.asarray(rank_matrix, dtype=np.float64)
    if matrix.ndim != 2:
        raise ValueError("rank_matrix must be two-dimensional")
    centered = matrix - matrix.mean(axis=0, keepdims=True)
    _left, _singular, right = np.linalg.svd(centered, full_matrices=False)
    factors = right[:factor_rank].T
    reconstruction = centered @ factors @ factors.T
    residual = centered - reconstruction
    norms = np.linalg.norm(residual, axis=1)
    return tuple(float(norm) for norm in norms)


@dataclass(frozen=True)
class PairedAtomMetrics:
    nrmse: ProjectionNrmse
    cosine_similarity: CosineSimilarity


def paired_atom_metrics(
    emhi_atoms: tuple[tuple[StandardizedAtomCoordinate, ...], ...],
    hofd_atoms: tuple[tuple[StandardizedAtomCoordinate, ...], ...],
    denominator_floor: NumericalFloor,
) -> PairedAtomMetrics:
    if not emhi_atoms or len(emhi_atoms) != len(hofd_atoms):
        raise ValueError("paired atom metrics require aligned nonempty rows")
    if any(len(emhi) != len(hofd) for emhi, hofd in zip(emhi_atoms, hofd_atoms, strict=True)):
        raise ValueError("paired atom vectors must have equal dimensions")
    squared_error = sum(
        sum((emhi - hofd) ** 2 for emhi, hofd in zip(left, right, strict=True))
        for left, right in zip(emhi_atoms, hofd_atoms, strict=True)
    )
    squared_reference = sum(sum(value * value for value in row) for row in emhi_atoms)
    inner_product = sum(
        sum(emhi * hofd for emhi, hofd in zip(left, right, strict=True))
        for left, right in zip(emhi_atoms, hofd_atoms, strict=True)
    )
    squared_hofd = sum(sum(value * value for value in row) for row in hofd_atoms)
    return PairedAtomMetrics(
        nrmse=sqrt(squared_error / len(emhi_atoms))
        / max(sqrt(squared_reference / len(emhi_atoms)), denominator_floor),
        cosine_similarity=inner_product
        / max(sqrt(squared_reference) * sqrt(squared_hofd), denominator_floor),
    )


def target_coalition_for_order(order: CoalitionOrder, client_count: ClientCount) -> RecordCount:
    order_size = int(order)
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
