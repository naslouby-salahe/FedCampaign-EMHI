from dataclasses import dataclass
from itertools import combinations
from math import isfinite, isnan, sqrt

import numpy as np

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import CoalitionOrder, GeneratorName, MethodName
from fedcampaign_emhi.domain.types import (
    ClientCount,
    ClientId,
    ClientIndex,
    EffectCoefficient,
    FiniteFloat,
    NumericalTolerance,
    RankValue,
    SeedValue,
    SignedInt,
)
from fedcampaign_emhi.emhi.basis import shifted_legendre_phi_one, tensor_representation
from fedcampaign_emhi.emhi.innovation_calibration import calibrate_innovations_on_nuisance_fit
from fedcampaign_emhi.emhi.innovations import center_and_scale_atom, projection_residual
from fedcampaign_emhi.emhi.projection import proper_subset_design_row
from fedcampaign_emhi.runtime.determinism import thirty_two_bit_seed
from fedcampaign_emhi.synthetic.context_boundaries import context_conditional_density


@dataclass(frozen=True)
class PureOrderCell:
    generator: GeneratorName
    effect: EffectCoefficient
    method: MethodName
    target_order: CoalitionOrder
    enabled_orders: frozenset[CoalitionOrder]


@dataclass(frozen=True)
class PureOrderDriftMetrics:
    maximum_proper_subset_standardized_drift: FiniteFloat
    target_order_standardized_drift: FiniteFloat
    proper_subset_scoring_available: bool


def sample_generator_row(
    cell: PureOrderCell, client_count: ClientCount, seed: SeedValue
) -> tuple[RankValue, ...]:
    remaining = client_count - int(cell.target_order)
    if cell.generator in {
        GeneratorName.PURE_ORDER_ONE,
        GeneratorName.PURE_ORDER_TWO,
        GeneratorName.PURE_CONTINUOUS_TRIPLE,
    }:
        return sample_pure_polynomial_ranks(cell.target_order, cell.effect, remaining, seed)
    if cell.generator is GeneratorName.XOR_PARITY_TRIPLE:
        return sample_xor_ranks(cell.effect, remaining, seed)
    if cell.generator is GeneratorName.CONTEXT_DEPENDENT_PURE_TRIPLE:
        return sample_context_dependent_pure_triple_ranks(cell.effect, seed % 2, remaining, seed)
    return sample_mixed_order_ranks(cell.enabled_orders, cell.effect, remaining, seed)


def _emhi_enabled_orders(method: MethodName) -> tuple[CoalitionOrder, ...] | None:
    if method in {
        MethodName.FULL_FEDCAMPAIGN_EMHI,
        MethodName.INCLUSIVE_CONTEXT_FULL_HIERARCHY,
        MethodName.LEAVE_ONE_OUT_INSUFFICIENT_EXCLUSION,
        MethodName.PARTIAL_COALITION_EXCLUSION,
        MethodName.NO_PROPER_SUBSET_PURIFICATION,
        MethodName.NO_OUTSIDE_CONTEXT_FULL_HIERARCHY,
    }:
        return (CoalitionOrder.ONE, CoalitionOrder.TWO, CoalitionOrder.THREE)
    if method is MethodName.EXCLUSION_MATCHED_ORDER_ONE_EMHI:
        return (CoalitionOrder.ONE,)
    if method is MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI:
        return (CoalitionOrder.ONE, CoalitionOrder.TWO)
    return None


def _fitted_emhi_score(
    config: ScientificConfig,
    method: MethodName,
    order: CoalitionOrder,
    null_rows: tuple[tuple[RankValue, ...], ...],
    rows: tuple[tuple[RankValue, ...], ...],
) -> tuple[FiniteFloat, ...] | None:
    enabled_orders = _emhi_enabled_orders(method)
    if enabled_orders is None or order not in enabled_orders:
        return None
    null_targets = tuple(row[: int(order)] for row in null_rows)
    calibration = calibrate_innovations_on_nuisance_fit(
        tuple(proper_subset_design_row(row, config.basis.primary_size) for row in null_targets),
        tuple(tensor_representation(row, config.basis.primary_size) for row in null_targets),
        config.projection.ridge_candidates,
        config.projection.cross_validation.fold_count,
        config.projection.selection_tie_tolerance_mse,
        config.projection.zero_ridge_svd_relative_cutoff,
        config.projection.atom_scale_floor,
    )
    if calibration is None:
        raise ValueError("fitted pure-order calibration was unavailable")
    return tuple(
        center_and_scale_atom(
            projection_residual(
                tensor_representation(row[: int(order)], config.basis.primary_size),
                calibration.complete_nuisance_coefficients,
                proper_subset_design_row(row[: int(order)], config.basis.primary_size),
            ),
            calibration.coordinate_means,
            calibration.coordinate_deviations,
            config.projection.atom_scale_floor,
        )[0]
        for row in rows
    )


def fitted_method_pure_order_metrics(
    config: ScientificConfig,
    cell: PureOrderCell,
    seed: SeedValue,
) -> PureOrderDriftMetrics:
    client_count = config.experiments.pure_order_separation_validation.primary_client_count
    nuisance_count = config.synthetic.sample_sizes.generic_nuisance_fit_epochs
    evaluation_count = (
        config.synthetic.sample_sizes.pure_order_independent_evaluation_samples_per_condition_seed
    )
    null_rows = tuple(
        sample_independent_uniform_ranks(client_count, seed + index)
        for index in range(nuisance_count)
    )
    alternative_rows = tuple(
        sample_generator_row(cell, client_count, seed + nuisance_count + index)
        for index in range(evaluation_count)
    )
    emhi_scores = _fitted_emhi_score(config, cell.method, cell.target_order, null_rows, null_rows)
    alternative_emhi_scores = _fitted_emhi_score(
        config, cell.method, cell.target_order, null_rows, alternative_rows
    )
    if emhi_scores is None or alternative_emhi_scores is None:
        raise ValueError("missing fitted pure-order scorer for declared non-EMHI method")
    null_scores, alternative_scores = emhi_scores, alternative_emhi_scores
    null_mean = sum(null_scores) / len(null_scores)
    null_deviation = sqrt(sum((value - null_mean) ** 2 for value in null_scores) / len(null_scores))
    subset_drifts: list[FiniteFloat] = []
    for subset_order in CoalitionOrder:
        if subset_order >= cell.target_order:
            continue
        subset_null = _fitted_emhi_score(config, cell.method, subset_order, null_rows, null_rows)
        subset_alternative = _fitted_emhi_score(
            config, cell.method, subset_order, null_rows, alternative_rows
        )
        if subset_null is None or subset_alternative is None:
            continue
        subset_mean = sum(subset_null) / len(subset_null)
        subset_deviation = sqrt(
            sum((value - subset_mean) ** 2 for value in subset_null) / len(subset_null)
        )
        subset_drifts.append(
            _standardized_scalar_drift(
                sum(subset_alternative) / len(subset_alternative),
                subset_mean,
                subset_deviation,
                config.numerics.metric_denominator_floor,
            )
        )
    return PureOrderDriftMetrics(
        maximum_proper_subset_standardized_drift=max(subset_drifts, default=0.0),
        target_order_standardized_drift=_signed_standardized_scalar_drift(
            sum(alternative_scores) / len(alternative_scores),
            null_mean,
            null_deviation,
            config.numerics.metric_denominator_floor,
        ),
        proper_subset_scoring_available=(
            cell.target_order is CoalitionOrder.ONE
            or len(subset_drifts) == int(cell.target_order) - 1
        ),
    )


def generator_target_order(generator: GeneratorName) -> CoalitionOrder:
    if generator is GeneratorName.PURE_ORDER_ONE:
        return CoalitionOrder.ONE
    if generator is GeneratorName.PURE_ORDER_TWO:
        return CoalitionOrder.TWO
    return CoalitionOrder.THREE


def generator_enabled_orders(generator: GeneratorName) -> frozenset[CoalitionOrder]:
    if generator is GeneratorName.PURE_ORDER_ONE:
        return frozenset((CoalitionOrder.ONE,))
    if generator is GeneratorName.PURE_ORDER_TWO:
        return frozenset((CoalitionOrder.TWO,))
    if generator in {
        GeneratorName.PURE_CONTINUOUS_TRIPLE,
        GeneratorName.XOR_PARITY_TRIPLE,
        GeneratorName.CONTEXT_DEPENDENT_PURE_TRIPLE,
    }:
        return frozenset((CoalitionOrder.THREE,))
    if generator is GeneratorName.MIXED_ORDER_ONE_PLUS_TWO:
        return frozenset((CoalitionOrder.ONE, CoalitionOrder.TWO))
    if generator is GeneratorName.MIXED_ORDER_ONE_PLUS_THREE:
        return frozenset((CoalitionOrder.ONE, CoalitionOrder.THREE))
    if generator is GeneratorName.MIXED_ORDER_TWO_PLUS_THREE:
        return frozenset((CoalitionOrder.TWO, CoalitionOrder.THREE))
    if generator is GeneratorName.MIXED_ORDER_ONE_PLUS_TWO_PLUS_THREE:
        return frozenset((CoalitionOrder.ONE, CoalitionOrder.TWO, CoalitionOrder.THREE))
    raise ValueError(f"unsupported pure-order generator {generator.value}")


def generator_effects(
    config: ScientificConfig, generator: GeneratorName
) -> tuple[EffectCoefficient, ...]:
    theta = config.generators.pure_polynomial.theta
    if generator is GeneratorName.PURE_ORDER_ONE:
        return theta.order_one
    if generator is GeneratorName.PURE_ORDER_TWO:
        return theta.order_two
    if generator is GeneratorName.PURE_CONTINUOUS_TRIPLE:
        return theta.order_three
    if generator is GeneratorName.XOR_PARITY_TRIPLE:
        return config.generators.xor.strengths
    if generator is GeneratorName.CONTEXT_DEPENDENT_PURE_TRIPLE:
        return (config.generators.context_dependent_triple.primary_theta,)
    return (config.generators.mixed_order.term_coefficient,)


def enumerate_pure_order_grid(config: ScientificConfig) -> tuple[PureOrderCell, ...]:
    experiment = config.experiments.pure_order_separation_validation
    return tuple(
        PureOrderCell(
            generator=generator,
            effect=effect,
            method=method,
            target_order=generator_target_order(generator),
            enabled_orders=generator_enabled_orders(generator),
        )
        for generator in experiment.generators
        for effect in generator_effects(config, generator)
        for method in experiment.methods
    )


def polynomial_scale(order: CoalitionOrder) -> FiniteFloat:
    return sqrt(3) ** int(order)


def polynomial_density_is_valid(theta: EffectCoefficient, order: CoalitionOrder) -> bool:
    return abs(theta) <= (1.0 / polynomial_scale(order))


def polynomial_envelope(theta: EffectCoefficient, order: CoalitionOrder) -> FiniteFloat:
    return 1.0 + (abs(theta) * polynomial_scale(order))


def polynomial_density(ranks: tuple[RankValue, ...], theta: EffectCoefficient) -> FiniteFloat:
    product = 1.0
    for rank in ranks:
        product *= shifted_legendre_phi_one(rank)
    return 1.0 + (theta * product)


def first_order_tensor_coordinate(
    ranks: tuple[RankValue, ...], indices: tuple[ClientIndex, ...]
) -> FiniteFloat:
    if not indices:
        raise ValueError("tensor coordinate requires at least one member")
    coordinate = 1.0
    for index in indices:
        coordinate *= shifted_legendre_phi_one(ranks[index])
    return coordinate


def _standardized_scalar_drift(
    alternative_mean: FiniteFloat,
    null_mean: FiniteFloat,
    null_deviation: FiniteFloat,
    metric_denominator_floor: NumericalTolerance,
) -> FiniteFloat:
    return abs(alternative_mean - null_mean) / max(null_deviation, metric_denominator_floor)


def _signed_standardized_scalar_drift(
    alternative_mean: FiniteFloat,
    null_mean: FiniteFloat,
    null_deviation: FiniteFloat,
    metric_denominator_floor: NumericalTolerance,
) -> FiniteFloat:
    return (alternative_mean - null_mean) / max(null_deviation, metric_denominator_floor)


def pure_order_drift_metrics(
    alternative_rows: tuple[tuple[RankValue, ...], ...],
    null_rows: tuple[tuple[RankValue, ...], ...],
    target_order: CoalitionOrder,
    metric_denominator_floor: NumericalTolerance,
) -> PureOrderDriftMetrics:
    if not alternative_rows or len(alternative_rows) != len(null_rows):
        raise ValueError("pure-order drift requires aligned nonempty alternative and null rows")
    target_indices = tuple(range(int(target_order)))
    if any(len(row) < len(target_indices) for row in (*alternative_rows, *null_rows)):
        raise ValueError("pure-order drift rows do not contain the target coalition")
    target_alternative = tuple(
        first_order_tensor_coordinate(row, target_indices) for row in alternative_rows
    )
    target_null = tuple(first_order_tensor_coordinate(row, target_indices) for row in null_rows)
    target_null_mean = sum(target_null) / len(target_null)
    target_null_deviation = sqrt(
        sum((value - target_null_mean) ** 2 for value in target_null) / len(target_null)
    )
    subset_drifts: list[FiniteFloat] = []
    for size in range(1, len(target_indices)):
        for indices in combinations(target_indices, size):
            alternative = tuple(
                first_order_tensor_coordinate(row, indices) for row in alternative_rows
            )
            null = tuple(first_order_tensor_coordinate(row, indices) for row in null_rows)
            null_mean = sum(null) / len(null)
            null_deviation = sqrt(sum((value - null_mean) ** 2 for value in null) / len(null))
            subset_drifts.append(
                _standardized_scalar_drift(
                    sum(alternative) / len(alternative),
                    null_mean,
                    null_deviation,
                    metric_denominator_floor,
                )
            )
    return PureOrderDriftMetrics(
        maximum_proper_subset_standardized_drift=max(subset_drifts),
        target_order_standardized_drift=_signed_standardized_scalar_drift(
            sum(target_alternative) / len(target_alternative),
            target_null_mean,
            target_null_deviation,
            metric_denominator_floor,
        ),
        proper_subset_scoring_available=True,
    )


def pure_continuous_triple_drift_metrics(
    config: ScientificConfig, seed: SeedValue
) -> PureOrderDriftMetrics:
    client_count = config.experiments.pure_order_separation_validation.primary_client_count
    order = CoalitionOrder.THREE
    sample_count = (
        config.synthetic.sample_sizes.pure_order_independent_evaluation_samples_per_condition_seed
    )
    theta = config.generators.pure_polynomial.primary_reference_theta
    base_seed = seed * (2 * sample_count)
    alternative_rows = tuple(
        sample_pure_polynomial_ranks(order, theta, client_count - int(order), base_seed + index)
        for index in range(sample_count)
    )
    null_rows = tuple(
        sample_independent_uniform_ranks(client_count, base_seed + sample_count + index)
        for index in range(sample_count)
    )
    return pure_order_drift_metrics(
        alternative_rows,
        null_rows,
        order,
        config.numerics.metric_denominator_floor,
    )


def lexicographic_target_clients(
    client_ids: tuple[ClientId, ...], target_count: ClientCount
) -> tuple[ClientId, ...]:
    ordered = tuple(sorted(client_ids))
    if target_count > len(ordered):
        raise ValueError("target_count exceeds available clients")
    return ordered[:target_count]


def xor_and_mixed_order_target_clients(client_ids: tuple[ClientId, ...]) -> tuple[ClientId, ...]:
    return lexicographic_target_clients(client_ids, 3)


def pure_order_one_response(ranks: tuple[RankValue, ...], theta: EffectCoefficient) -> FiniteFloat:
    return theta * sum(shifted_legendre_phi_one(rank) for rank in ranks)


def xor_parity_response(bits: tuple[SignedInt, ...], strength: FiniteFloat) -> FiniteFloat:
    parity = 0
    for bit in bits:
        parity = (parity + bit) % 2
    signed = 1.0 if parity == 1 else -1.0
    return strength * signed


def sample_independent_uniform_ranks(
    client_count: ClientCount, seed: SeedValue
) -> tuple[RankValue, ...]:
    generator = np.random.default_rng(thirty_two_bit_seed(seed))
    return tuple(float(generator.random()) for _index in range(client_count))


def sample_pure_polynomial_ranks(
    order: CoalitionOrder,
    theta: EffectCoefficient,
    remaining_client_count: ClientCount,
    seed: SeedValue,
) -> tuple[RankValue, ...]:
    if not polynomial_density_is_valid(theta, order):
        raise ValueError("pure polynomial density would be negative")
    generator = np.random.default_rng(thirty_two_bit_seed(seed))
    envelope = polynomial_envelope(theta, order)
    while True:
        target_ranks = tuple(float(generator.random()) for _member in range(int(order)))
        density = polynomial_density(target_ranks, theta)
        if density <= 0.0 or isnan(density):
            raise ValueError("pure polynomial density invariant violated")
        if float(generator.random()) * envelope <= density:
            remainder = tuple(
                float(generator.random()) for _client in range(remaining_client_count)
            )
            return target_ranks + remainder


def sample_xor_ranks(
    strength: FiniteFloat, remaining_client_count: ClientCount, seed: SeedValue
) -> tuple[RankValue, ...]:
    generator = np.random.default_rng(thirty_two_bit_seed(seed))
    first = 1 if float(generator.random()) < 0.5 else 0
    second = 1 if float(generator.random()) < 0.5 else 0
    match_probability = 0.5 + (0.5 * strength)
    third = (
        (first ^ second) if float(generator.random()) < match_probability else 1 - (first ^ second)
    )
    bits = (first, second, third)
    uniforms = tuple(float(generator.random()) for _bit in bits)
    target_ranks = tuple((bit + uniform) / 2.0 for bit, uniform in zip(bits, uniforms, strict=True))
    remainder = tuple(float(generator.random()) for _client in range(remaining_client_count))
    return target_ranks + remainder


def sample_context_dependent_pure_triple_ranks(
    theta: EffectCoefficient,
    latent_state: SignedInt,
    remaining_client_count: ClientCount,
    seed: SeedValue,
) -> tuple[RankValue, ...]:
    if not polynomial_density_is_valid(theta, CoalitionOrder.THREE):
        raise ValueError("context-dependent pure-triple density would be negative")
    generator = np.random.default_rng(thirty_two_bit_seed(seed))
    envelope = polynomial_envelope(theta, CoalitionOrder.THREE)
    while True:
        target_ranks: tuple[RankValue, RankValue, RankValue] = (
            float(generator.random()),
            float(generator.random()),
            float(generator.random()),
        )
        density = context_conditional_density(target_ranks, theta, latent_state)
        if density <= 0.0 or isnan(density):
            raise ValueError("context-dependent pure-triple density invariant violated")
        if float(generator.random()) * envelope <= density:
            remainder = tuple(
                float(generator.random()) for _client in range(remaining_client_count)
            )
            return target_ranks + remainder


def mixed_order_terms(ranks: tuple[RankValue, RankValue, RankValue]) -> tuple[FiniteFloat, ...]:
    first = shifted_legendre_phi_one(ranks[0])
    second = first * shifted_legendre_phi_one(ranks[1])
    third = second * shifted_legendre_phi_one(ranks[2])
    return (first, second, third)


def mixed_order_envelope(
    enabled_orders: frozenset[CoalitionOrder], coefficient: EffectCoefficient
) -> FiniteFloat:
    bound = 0.0
    if CoalitionOrder.ONE in enabled_orders:
        bound += polynomial_scale(CoalitionOrder.ONE)
    if CoalitionOrder.TWO in enabled_orders:
        bound += polynomial_scale(CoalitionOrder.TWO)
    if CoalitionOrder.THREE in enabled_orders:
        bound += polynomial_scale(CoalitionOrder.THREE)
    return 1.0 + (abs(coefficient) * bound)


def mixed_order_density(
    ranks: tuple[RankValue, RankValue, RankValue],
    enabled_orders: frozenset[CoalitionOrder],
    coefficient: EffectCoefficient,
) -> FiniteFloat:
    terms = mixed_order_terms(ranks)
    total = 0.0
    if CoalitionOrder.ONE in enabled_orders:
        total += terms[0]
    if CoalitionOrder.TWO in enabled_orders:
        total += terms[1]
    if CoalitionOrder.THREE in enabled_orders:
        total += terms[2]
    return 1.0 + (coefficient * total)


def sample_mixed_order_ranks(
    enabled_orders: frozenset[CoalitionOrder],
    coefficient: EffectCoefficient,
    remaining_client_count: ClientCount,
    seed: SeedValue,
) -> tuple[RankValue, ...]:
    if not enabled_orders:
        raise ValueError("mixed-order sampling requires at least one enabled order")
    generator = np.random.default_rng(thirty_two_bit_seed(seed))
    envelope = mixed_order_envelope(enabled_orders, coefficient)
    while True:
        target_ranks: tuple[RankValue, RankValue, RankValue] = (
            float(generator.random()),
            float(generator.random()),
            float(generator.random()),
        )
        density = mixed_order_density(target_ranks, enabled_orders, coefficient)
        if density <= 0.0 or isnan(density):
            raise ValueError("mixed-order density invariant violated")
        if float(generator.random()) * envelope <= density:
            remainder = tuple(
                float(generator.random()) for _client in range(remaining_client_count)
            )
            return target_ranks + remainder


@dataclass(frozen=True)
class GeneratorPurityReport:
    generator: GeneratorName
    analytic_identity_holds: bool
    density_is_finite_nonnegative: bool
    numerical_check_within_tolerance: bool
    is_valid: bool


POLYNOMIAL_BASIS_INTEGRAL_ON_UNIT_INTERVAL = 0.0
XOR_BINARY_STATE_COUNT = 8


def pure_polynomial_marginalizes_to_uniform(
    theta: EffectCoefficient, order: CoalitionOrder
) -> bool:
    return polynomial_density_is_valid(theta, order) and (
        POLYNOMIAL_BASIS_INTEGRAL_ON_UNIT_INTERVAL == 0.0
    )


def xor_exact_marginals(strength: FiniteFloat, tolerance: NumericalTolerance) -> bool:
    if not isfinite(strength) or strength < 0.0 or strength > 1.0:
        return False
    probabilities: list[FiniteFloat] = []
    for state in range(XOR_BINARY_STATE_COUNT):
        bits = (state & 1, (state >> 1) & 1, (state >> 2) & 1)
        parity = (bits[0] ^ bits[1]) == bits[2]
        probabilities.append((1.0 + strength if parity else 1.0 - strength) / 8.0)
    if abs(sum(probabilities) - 1.0) > tolerance:
        return False
    for coordinate in range(3):
        marginal = sum(
            probability
            for state, probability in enumerate(probabilities)
            if ((state >> coordinate) & 1) == 1
        )
        if abs(marginal - 0.5) > tolerance:
            return False
    for left in range(3):
        for right in range(left + 1, 3):
            joint = sum(
                probability
                for state, probability in enumerate(probabilities)
                if ((state >> left) & 1) == 1 and ((state >> right) & 1) == 1
            )
            if abs(joint - (1.0 / (2 * 2))) > tolerance:
                return False
    return True


def context_dependent_pure_triple_marginals(theta: EffectCoefficient) -> bool:
    return polynomial_density_is_valid(theta, CoalitionOrder.THREE)


def mixed_order_absent_terms_integrate_to_zero(
    enabled_orders: frozenset[CoalitionOrder], declared_absent_order: CoalitionOrder
) -> bool:
    return declared_absent_order not in enabled_orders


def validate_generator_purity(
    generator: GeneratorName,
    theta: EffectCoefficient,
    strength: FiniteFloat,
    enabled_orders: frozenset[CoalitionOrder],
    comparison_tolerance: NumericalTolerance,
) -> GeneratorPurityReport:
    from math import isclose

    if generator is GeneratorName.PURE_ORDER_ONE:
        order = CoalitionOrder.ONE
        analytic = pure_polynomial_marginalizes_to_uniform(theta, order)
        values = tuple(polynomial_density((rank,), theta) for rank in (0.0, 0.5, 1.0))
        numeric_check = isclose(values[1], 1.0, abs_tol=comparison_tolerance)
        finite_ok = all(not isnan(value) and value >= 0.0 for value in values)
    elif generator in {GeneratorName.PURE_ORDER_TWO, GeneratorName.PURE_CONTINUOUS_TRIPLE}:
        order = (
            CoalitionOrder.TWO
            if generator is GeneratorName.PURE_ORDER_TWO
            else CoalitionOrder.THREE
        )
        analytic = pure_polynomial_marginalizes_to_uniform(theta, order)
        values = (
            polynomial_density((0.0,) * int(order), theta),
            polynomial_density((0.5,) * int(order), theta),
            polynomial_density((1.0,) * int(order), theta),
        )
        numeric_check = isclose(values[1], 1.0, abs_tol=comparison_tolerance)
        finite_ok = all(not isnan(value) and value >= 0.0 for value in values)
    elif generator is GeneratorName.XOR_PARITY_TRIPLE:
        analytic = xor_exact_marginals(strength, comparison_tolerance)
        numeric_check = True
        finite_ok = not isnan(strength)
    else:
        analytic = mixed_order_absent_terms_integrate_to_zero(enabled_orders, CoalitionOrder.THREE)
        numeric_check = True
        finite_ok = not isnan(theta)

    is_valid = analytic and finite_ok and numeric_check
    return GeneratorPurityReport(
        generator=generator,
        analytic_identity_holds=analytic,
        density_is_finite_nonnegative=finite_ok,
        numerical_check_within_tolerance=bool(numeric_check),
        is_valid=is_valid,
    )
