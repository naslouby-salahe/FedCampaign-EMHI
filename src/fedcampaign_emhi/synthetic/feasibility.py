from __future__ import annotations

from collections import UserDict
from dataclasses import dataclass
from math import sqrt

import numpy as np

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    ContextMethodName,
    DatasetName,
    ExecutionRole,
    LatentMarkovState,
)
from fedcampaign_emhi.domain.types import (
    BasisSize,
    BinIndex,
    Boolean,
    CellCount,
    ClientId,
    ComponentName,
    ContextCoverage,
    EffectCoefficient,
    EstimatorSupportLevel,
    GramConditionNumber,
    HistogramBinMass,
    InnovationCoordinate,
    NumericalFloor,
    Probability,
    ProjectionNrmse,
    RankEstimationError,
    RankReference,
    RankValue,
    RidgePenalty,
    SeedCoordinate,
    SeedDerivationIdentity,
    SeedValue,
    StandardizedNullBias,
)
from fedcampaign_emhi.emhi.calibration import calibrate_innovations_on_nuisance_fit
from fedcampaign_emhi.emhi.contexts import (
    assign_context_cell,
    context_cluster_identity,
    fit_context_centroids,
    outside_context_histogram,
)
from fedcampaign_emhi.emhi.evidence import euclidean_norm
from fedcampaign_emhi.emhi.innovations import center_and_scale_atom, projection_residual
from fedcampaign_emhi.emhi.projection import (
    proper_subset_design_row,
    unregularized_gram_condition_number,
)
from fedcampaign_emhi.emhi.structure import (
    coalition_conditioned_residual_rank,
    shifted_legendre_phi_one,
    tensor_representation,
)
from fedcampaign_emhi.runtime import derive_component_seed, thirty_two_bit_seed


@dataclass(frozen=True)
class EstimatorFeasibilityMetrics:
    conditional_rank_mae: RankEstimationError
    projection_nrmse: ProjectionNrmse
    standardized_null_bias: StandardizedNullBias
    context_coverage: ContextCoverage
    abstention_rate: Probability
    condition_number: GramConditionNumber | None
    numerical_failure: Boolean


@dataclass(frozen=True)
class EstimatorFeasibilityCondition:
    identifier: ComponentName
    order: CoalitionOrder
    support_per_context: EstimatorSupportLevel
    basis_size: BasisSize
    cell_count: CellCount
    ridge_candidates: tuple[RidgePenalty, ...] | None
    forced_no_abstention: Boolean


@dataclass(frozen=True)
class EstimatorFeasibilityEvaluation:
    condition: EstimatorFeasibilityCondition
    metrics: EstimatorFeasibilityMetrics


def feasibility_conditions(
    config: ScientificConfig, execution_role: ExecutionRole
) -> tuple[EstimatorFeasibilityCondition, ...]:
    primary_support = config.context.minimum_support_epochs.order_three
    primary = EstimatorFeasibilityCondition(
        "primary-order-three",
        CoalitionOrder.THREE,
        primary_support,
        config.basis.primary_size,
        config.context.primary_cell_count,
        None,
        False,
    )
    if execution_role is ExecutionRole.CONFIRMATORY:
        return (primary,)
    conditions: list[EstimatorFeasibilityCondition] = [primary]
    for order in CoalitionOrder:
        for support in config.support_grids.estimator_samples_per_context:
            conditions.append(
                EstimatorFeasibilityCondition(
                    f"primary-support-order-{int(order)}-n-{support}",
                    order,
                    support,
                    config.basis.primary_size,
                    config.context.primary_cell_count,
                    None,
                    False,
                )
            )
    for support in config.support_grids.estimator_one_factor_sensitivity_samples_per_context:
        for basis_size in config.basis.sensitivity_sizes:
            conditions.append(
                EstimatorFeasibilityCondition(
                    f"basis-sensitivity-{basis_size}-n-{support}",
                    CoalitionOrder.THREE,
                    support,
                    basis_size,
                    config.context.primary_cell_count,
                    None,
                    False,
                )
            )
        for cell_count in config.context.cell_count_sensitivity:
            conditions.append(
                EstimatorFeasibilityCondition(
                    f"context-sensitivity-{cell_count}-n-{support}",
                    CoalitionOrder.THREE,
                    support,
                    config.basis.primary_size,
                    cell_count,
                    None,
                    False,
                )
            )
        conditions.append(
            EstimatorFeasibilityCondition(
                f"forced-ridge-n-{support}",
                CoalitionOrder.THREE,
                support,
                config.basis.primary_size,
                config.context.primary_cell_count,
                (
                    config.experiments.estimator_support_and_context_feasibility.sensitivity.forced_ridge,
                ),
                False,
            )
        )
        conditions.append(
            EstimatorFeasibilityCondition(
                f"forced-no-abstention-n-{support}",
                CoalitionOrder.THREE,
                support,
                config.basis.primary_size,
                config.context.primary_cell_count,
                None,
                config.experiments.estimator_support_and_context_feasibility.sensitivity.forced_no_abstention,
            )
        )
    unique: list[EstimatorFeasibilityCondition] = []
    for condition in conditions:
        if condition not in unique:
            unique.append(condition)
    return tuple(unique)


def evaluate_estimator_feasibility_seed(
    config: ScientificConfig, seed: SeedValue, execution_role: ExecutionRole
) -> tuple[EstimatorFeasibilityEvaluation, ...]:
    return tuple(
        EstimatorFeasibilityEvaluation(
            condition,
            evaluate_estimator_feasibility_condition(
                config,
                seed,
                condition.order,
                condition.support_per_context,
                condition.basis_size,
                condition.cell_count,
                condition.ridge_candidates,
                condition.forced_no_abstention,
            ),
        )
        for condition in feasibility_conditions(config, execution_role)
    )


def _numerical_failure_metrics(
    condition_number: GramConditionNumber | None = None,
) -> EstimatorFeasibilityMetrics:
    return EstimatorFeasibilityMetrics(0.0, 0.0, 0.0, 0.0, 1.0, condition_number, True)


def _component_seed(
    config: ScientificConfig,
    root_seed: SeedValue,
    component: ComponentName,
    order: CoalitionOrder,
    support_per_context: EstimatorSupportLevel,
    basis_size: BasisSize,
    cell_count: CellCount,
) -> SeedValue:
    return derive_component_seed(
        SeedDerivationIdentity(
            base_seed=root_seed,
            component_name=component,
            dataset=config.datasets.primary.name,
            client_ids=(),
            coalition_ids=(),
            condition_coordinates=(
                SeedCoordinate(name="coalition_order", scalar=int(order)),
                SeedCoordinate(name="support_per_context", scalar=support_per_context),
                SeedCoordinate(name="basis_size", scalar=basis_size),
                SeedCoordinate(name="context_cell_count", scalar=cell_count),
            ),
        )
    )


def _conditional_rank_mae(
    estimated_ranks: tuple[RankValue, ...], truth_ranks: tuple[RankValue, ...]
) -> RankEstimationError:
    if len(estimated_ranks) != len(truth_ranks) or not estimated_ranks:
        raise ValueError("conditional-rank MAE requires aligned nonempty samples")
    return sum(
        abs(estimate - truth) for estimate, truth in zip(estimated_ranks, truth_ranks, strict=True)
    ) / len(estimated_ranks)


def _projection_nrmse(
    projections: tuple[tuple[InnovationCoordinate, ...], ...],
    tensor_rows: tuple[tuple[InnovationCoordinate, ...], ...],
    floor: NumericalFloor,
) -> ProjectionNrmse:
    if not projections or len(projections) != len(tensor_rows):
        raise ValueError("projection NRMSE requires aligned nonempty evaluation rows")
    residual = sqrt(sum(euclidean_norm(row) ** 2 for row in projections) / len(projections))
    reference = sqrt(sum(euclidean_norm(row) ** 2 for row in tensor_rows) / len(tensor_rows))
    return residual / (reference + floor)


def _histogram_rows(
    config: ScientificConfig,
    sequence: DeterministicContextSupportSequence,
    order: CoalitionOrder,
) -> tuple[tuple[HistogramBinMass, ...] | None, ...]:
    target = sequence.target_client_ids
    complement = tuple(client for client in sequence.client_ids if client not in target)
    indexes = {client: index for index, client in enumerate(sequence.client_ids)}
    rows: list[tuple[HistogramBinMass, ...] | None] = [None]
    for _ranks in sequence.ranks[1:]:
        previous = sequence.ranks[len(rows) - 1]
        histogram = outside_context_histogram(
            tuple((client, previous[indexes[client]]) for client in complement),
            complement,
            complement,
            config.context.outside_histogram_bin_count,
            config.context.minimum_available_outside_clients,
            config.context.minimum_available_outside_fraction,
        )
        rows.append(None if histogram.abstained else histogram.bin_mass)
    return tuple(rows)


def _centroids(
    config: ScientificConfig,
    sequence: DeterministicContextSupportSequence,
    order: CoalitionOrder,
    cell_count: CellCount,
    histograms: tuple[tuple[HistogramBinMass, ...] | None, ...],
    seed: SeedValue,
) -> tuple[tuple[HistogramBinMass, ...], ...] | None:
    from fedcampaign_emhi.domain.types import ContextTrainingRow

    rows = tuple(
        ContextTrainingRow(
            dataset=DatasetName.TON_IOT_NETWORK,
            coalition_order=order,
            coalition_client_ids=sequence.target_client_ids,
            epoch_index=index,
            histogram=histogram,
        )
        for index, histogram in enumerate(histograms)
        if histogram is not None
    )
    fitted = fit_context_centroids(
        rows,
        context_cluster_identity(
            DatasetName.TON_IOT_NETWORK,
            order,
            ContextMethodName.EXACT_COALITION_EXCLUSION,
            seed,
        ),
        cell_count,
        config.context.kmeans.n_init,
        config.context.kmeans.max_iterations,
        config.context.kmeans.tolerance,
        config.context.kmeans.assignment_tie_tolerance,
        seed,
    )
    return None if fitted is None else fitted.centroids


def _residual_ranks(
    config: ScientificConfig,
    sequence: DeterministicContextSupportSequence,
    histograms: tuple[tuple[HistogramBinMass, ...] | None, ...],
    centroids: tuple[tuple[HistogramBinMass, ...], ...],
) -> tuple[tuple[tuple[RankValue, ...], BinIndex] | None, ...]:
    assignments = tuple(
        None
        if histogram is None
        else assign_context_cell(
            histogram, centroids, config.context.kmeans.assignment_tie_tolerance
        )
        for histogram in histograms
    )
    target_indexes = tuple(
        sequence.client_ids.index(client) for client in sequence.target_client_ids
    )
    references: UserDict[tuple[BinIndex, BinIndex], RankReference] = UserDict()
    for cell in range(len(centroids)):
        for member_index, rank_index in enumerate(target_indexes):
            references[cell, member_index] = RankReference(
                scores=tuple(
                    ranks[rank_index]
                    for ranks, assignment in zip(sequence.ranks, assignments, strict=True)
                    if assignment == cell
                )
            )
    return tuple(
        None
        if assignment is None
        else (
            tuple(
                coalition_conditioned_residual_rank(
                    ranks[rank_index],
                    references[assignment, member_index],
                    config.context.rank_clip_epsilon,
                )
                for member_index, rank_index in enumerate(target_indexes)
            ),
            assignment,
        )
        for ranks, assignment in zip(sequence.ranks, assignments, strict=True)
    )


def evaluate_estimator_feasibility_condition(
    config: ScientificConfig,
    seed: SeedValue,
    order: CoalitionOrder,
    support_per_context: EstimatorSupportLevel,
    basis_size: BasisSize,
    cell_count: CellCount,
    ridge_candidates: tuple[RidgePenalty, ...] | None = None,
    forced_no_abstention: Boolean = False,
) -> EstimatorFeasibilityMetrics:
    client_count = config.experiments.pure_order_separation_validation.primary_client_count
    clients = tuple(f"synthetic-client-{index:02d}" for index in range(client_count))
    nuisance_seed = _component_seed(
        config,
        seed,
        "estimator-feasibility-nuisance",
        order,
        support_per_context,
        basis_size,
        cell_count,
    )
    context_seed = _component_seed(
        config,
        seed,
        "estimator-feasibility-context",
        order,
        support_per_context,
        basis_size,
        cell_count,
    )
    evaluation_seed = _component_seed(
        config,
        seed,
        "estimator-feasibility-evaluation",
        order,
        support_per_context,
        basis_size,
        cell_count,
    )
    nuisance = generate_deterministic_context_support(
        clients, order, cell_count, support_per_context, nuisance_seed
    )
    histograms = _histogram_rows(config, nuisance, order)
    centroids = _centroids(config, nuisance, order, cell_count, histograms, context_seed)
    if centroids is None:
        return _numerical_failure_metrics()
    fitted_ranks = _residual_ranks(config, nuisance, histograms, centroids)
    usable = tuple(item for item in fitted_ranks if item is not None)
    if not usable:
        return _numerical_failure_metrics()
    design_rows = tuple(proper_subset_design_row(item[0], basis_size) for item in usable)
    tensors = tuple(tensor_representation(item[0], basis_size) for item in usable)
    try:
        condition_number = unregularized_gram_condition_number(design_rows)
        calibration = calibrate_innovations_on_nuisance_fit(
            design_rows,
            tensors,
            config.projection.ridge_candidates if ridge_candidates is None else ridge_candidates,
            config.projection.cross_validation.fold_count,
            config.projection.selection_tie_tolerance_mse,
            config.projection.zero_ridge_svd_relative_cutoff,
            config.projection.atom_scale_floor,
        )
    except (ArithmeticError, ValueError):
        return _numerical_failure_metrics()
    if calibration is None or condition_number > config.projection.maximum_gram_condition_number:
        return _numerical_failure_metrics(condition_number)
    evaluation = generate_deterministic_context_support(
        clients,
        order,
        cell_count,
        config.synthetic.sample_sizes.estimator_evaluation_samples_per_context_seed,
        evaluation_seed,
    )
    evaluation_histograms = _histogram_rows(config, evaluation, order)
    evaluation_ranks = _residual_ranks(config, evaluation, evaluation_histograms, centroids)
    supported = tuple(item for item in evaluation_ranks if item is not None)
    if not supported and not forced_no_abstention:
        return _numerical_failure_metrics(condition_number)
    evaluation_design = tuple(proper_subset_design_row(item[0], basis_size) for item in supported)
    evaluation_tensors = tuple(tensor_representation(item[0], basis_size) for item in supported)
    atoms = tuple(
        projection_residual(tensor, calibration.complete_nuisance_coefficients, design)
        for tensor, design in zip(evaluation_tensors, evaluation_design, strict=True)
    )
    standardized = tuple(
        center_and_scale_atom(
            atom,
            calibration.coordinate_means,
            calibration.coordinate_deviations,
            config.projection.atom_scale_floor,
        )
        for atom in atoms
    )
    coordinate_count = len(standardized[0])
    mean_atom = tuple(
        sum(row[coordinate] for row in standardized) / len(standardized)
        for coordinate in range(coordinate_count)
    )
    trace_root = sqrt(
        sum(
            sum((row[coordinate] - mean_atom[coordinate]) ** 2 for row in standardized)
            / len(standardized)
            for coordinate in range(coordinate_count)
        )
    )
    estimated = tuple(rank for item in supported for rank in item[0])
    truth_indexes = tuple(
        evaluation.client_ids.index(client) for client in evaluation.target_client_ids
    )
    truth = tuple(
        ranks[index]
        for ranks, item in zip(evaluation.ranks, evaluation_ranks, strict=True)
        if item is not None
        for index in truth_indexes
    )
    projections = tuple(
        tuple(tensor - atom for tensor, atom in zip(tensor_row, atom_row, strict=True))
        for tensor_row, atom_row in zip(evaluation_tensors, atoms, strict=True)
    )
    coverage = len(supported) / (len(evaluation.ranks) - 1)
    return EstimatorFeasibilityMetrics(
        _conditional_rank_mae(estimated, truth),
        _projection_nrmse(
            projections, evaluation_tensors, config.numerics.metric_denominator_floor
        ),
        euclidean_norm(mean_atom) / max(trace_root, config.numerics.metric_denominator_floor),
        coverage,
        1.0 - coverage,
        condition_number,
        False,
    )


@dataclass(frozen=True)
class DeterministicContextSupportSequence:
    client_ids: tuple[ClientId, ...]
    target_client_ids: tuple[ClientId, ...]
    latent_cell_indexes: tuple[CellCount, ...]
    ranks: tuple[tuple[RankValue, ...], ...]


def generate_deterministic_context_support(
    client_ids: tuple[ClientId, ...],
    target_order: CoalitionOrder,
    context_cell_count: CellCount,
    support_per_context: EstimatorSupportLevel,
    seed: SeedValue,
) -> DeterministicContextSupportSequence:
    ordered_clients = tuple(sorted(client_ids))
    target_client_ids = ordered_clients[: int(target_order)]
    if len(target_client_ids) != int(target_order):
        raise ValueError("target coalition exceeds supplied client IDs")
    if len(ordered_clients) == len(target_client_ids):
        raise ValueError("context-support sequence requires outside clients")
    generator = np.random.default_rng(thirty_two_bit_seed(seed))
    rows: list[tuple[RankValue, ...]] = []
    cells: list[CellCount] = []
    for row_index in range((support_per_context * context_cell_count) + 1):
        cell: CellCount = 0 if row_index == 0 else (row_index - 1) % context_cell_count
        outside_rank: RankValue = (cell + 0.5) / context_cell_count
        row: list[RankValue] = []
        for client_id in ordered_clients:
            if client_id in target_client_ids:
                row.append(float(generator.random()))
            else:
                row.append(outside_rank)
        rows.append(tuple(row))
        cells.append(cell)
    return DeterministicContextSupportSequence(
        client_ids=ordered_clients,
        target_client_ids=target_client_ids,
        latent_cell_indexes=tuple(cells),
        ranks=tuple(rows),
    )


def primary_feasibility_context_support(
    config: ScientificConfig, seed: SeedValue
) -> DeterministicContextSupportSequence:
    client_count = config.experiments.pure_order_separation_validation.primary_client_count
    client_ids = tuple(f"synthetic-client-{index:02d}" for index in range(client_count))
    return generate_deterministic_context_support(
        client_ids,
        CoalitionOrder.THREE,
        config.context.primary_cell_count,
        config.context.minimum_support_epochs.order_three,
        seed,
    )


def initial_markov_state(negative_probability: Probability, seed: SeedValue) -> LatentMarkovState:
    generator = np.random.default_rng(thirty_two_bit_seed(seed))
    if float(generator.random()) < negative_probability:
        return LatentMarkovState.NEGATIVE
    return LatentMarkovState.POSITIVE


def next_markov_state(
    current_state: LatentMarkovState, same_state_probability: Probability, seed: SeedValue
) -> LatentMarkovState:
    generator = np.random.default_rng(thirty_two_bit_seed(seed))
    if float(generator.random()) < same_state_probability:
        return current_state
    return (
        LatentMarkovState.POSITIVE
        if current_state is LatentMarkovState.NEGATIVE
        else LatentMarkovState.NEGATIVE
    )


def outside_rank_from_interval(lower: RankValue, upper: RankValue, seed: SeedValue) -> RankValue:
    generator = np.random.default_rng(thirty_two_bit_seed(seed))
    return float(generator.uniform(lower, upper))


def context_conditional_density(
    ranks: tuple[RankValue, ...], theta: EffectCoefficient, latent_state: LatentMarkovState
) -> InnovationCoordinate:
    product = 1.0
    for rank in ranks:
        product *= shifted_legendre_phi_one(rank)
    return 1.0 + (theta * latent_state * product)
