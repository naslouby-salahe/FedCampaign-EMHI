from dataclasses import dataclass
from math import isfinite, isnan, sqrt

import numpy as np

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    GeneratorName,
    LatentMarkovState,
    MethodName,
)
from fedcampaign_emhi.domain.types import (
    BasisCoordinate,
    BinaryClassLabel,
    Boolean,
    ClientCount,
    ClientId,
    EffectCoefficient,
    InnovationCoordinate,
    NumericalTolerance,
    PolynomialDensity,
    Probability,
    RankValue,
    SeedValue,
    StandardizedDrift,
    XorInteractionStrength,
)
from fedcampaign_emhi.emhi.structure import shifted_legendre_phi_one
from fedcampaign_emhi.runtime import thirty_two_bit_seed
from fedcampaign_emhi.synthetic.feasibility import context_conditional_density


@dataclass(frozen=True)
class PureOrderCell:
    generator: GeneratorName
    effect: EffectCoefficient
    method: MethodName
    target_order: CoalitionOrder
    enabled_orders: frozenset[CoalitionOrder]


@dataclass(frozen=True)
class PureOrderDriftMetrics:
    maximum_proper_subset_standardized_drift: StandardizedDrift
    target_order_standardized_drift: StandardizedDrift
    proper_subset_scoring_available: Boolean


def sample_generator_row(
    cell: PureOrderCell, client_count: ClientCount, seed: SeedValue
) -> tuple[RankValue, ...]:
    remaining = client_count - cell.target_order
    if cell.generator in {
        GeneratorName.PURE_ORDER_ONE,
        GeneratorName.PURE_ORDER_TWO,
        GeneratorName.PURE_CONTINUOUS_TRIPLE,
    }:
        return sample_pure_polynomial_ranks(cell.target_order, cell.effect, remaining, seed)
    if cell.generator is GeneratorName.XOR_PARITY_TRIPLE:
        return sample_xor_ranks(cell.effect, remaining, seed)
    if cell.generator is GeneratorName.CONTEXT_DEPENDENT_PURE_TRIPLE:
        latent_state = LatentMarkovState.NEGATIVE if seed % 2 else LatentMarkovState.POSITIVE
        return sample_context_dependent_pure_triple_ranks(
            cell.effect, latent_state, remaining, seed
        )
    return sample_mixed_order_ranks(cell.enabled_orders, cell.effect, remaining, seed)


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


def polynomial_scale(order: CoalitionOrder) -> BasisCoordinate:
    return sqrt(3) ** order


def polynomial_density_is_valid(theta: EffectCoefficient, order: CoalitionOrder) -> Boolean:
    return abs(theta) <= (1.0 / polynomial_scale(order))


def polynomial_envelope(theta: EffectCoefficient, order: CoalitionOrder) -> PolynomialDensity:
    return 1.0 + (abs(theta) * polynomial_scale(order))


def pure_order_one_response(
    ranks: tuple[RankValue, ...], theta: EffectCoefficient
) -> InnovationCoordinate:
    product = 1.0
    for rank in ranks:
        product *= shifted_legendre_phi_one(rank)
    return theta * product


def xor_parity_response(
    bits: tuple[BinaryClassLabel, ...], strength: XorInteractionStrength
) -> InnovationCoordinate:
    parity = 0
    for bit in bits:
        parity ^= bit
    return strength if parity else -strength


def polynomial_density(ranks: tuple[RankValue, ...], theta: EffectCoefficient) -> PolynomialDensity:
    return 1.0 + pure_order_one_response(ranks, theta)


def lexicographic_target_clients(
    client_ids: tuple[ClientId, ...], target_count: ClientCount
) -> tuple[ClientId, ...]:
    ordered = tuple(sorted(client_ids))
    if target_count > len(ordered):
        raise ValueError("target_count exceeds available clients")
    return ordered[:target_count]


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
        target_ranks = tuple(float(generator.random()) for _member in range(order))
        density = polynomial_density(target_ranks, theta)
        if density <= 0.0 or isnan(density):
            raise ValueError("pure polynomial density invariant violated")
        if float(generator.random()) * envelope <= density:
            remainder = tuple(
                float(generator.random()) for _client in range(remaining_client_count)
            )
            return target_ranks + remainder


def sample_xor_ranks(
    strength: XorInteractionStrength, remaining_client_count: ClientCount, seed: SeedValue
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
    latent_state: LatentMarkovState,
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


def mixed_order_terms(ranks: tuple[RankValue, RankValue, RankValue]) -> tuple[BasisCoordinate, ...]:
    first = shifted_legendre_phi_one(ranks[0])
    second = first * shifted_legendre_phi_one(ranks[1])
    third = second * shifted_legendre_phi_one(ranks[2])
    return (first, second, third)


def mixed_order_envelope(
    enabled_orders: frozenset[CoalitionOrder], coefficient: EffectCoefficient
) -> PolynomialDensity:
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
) -> InnovationCoordinate:
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
    analytic_identity_holds: Boolean
    density_is_finite_nonnegative: Boolean
    numerical_check_within_tolerance: Boolean
    is_valid: Boolean


POLYNOMIAL_BASIS_INTEGRAL_ON_UNIT_INTERVAL = 0.0
XOR_BINARY_STATE_COUNT = 8


def pure_polynomial_marginalizes_to_uniform(
    theta: EffectCoefficient, order: CoalitionOrder
) -> Boolean:
    return polynomial_density_is_valid(theta, order) and (
        POLYNOMIAL_BASIS_INTEGRAL_ON_UNIT_INTERVAL == 0.0
    )


def xor_exact_marginals(strength: XorInteractionStrength, tolerance: NumericalTolerance) -> Boolean:
    if not isfinite(strength) or strength < 0.0 or strength > 1.0:
        return False
    probabilities: list[Probability] = []
    for state in range(XOR_BINARY_STATE_COUNT):
        bits = (state & 1, (state >> 1) & 1, (state >> 2) & 1)
        parity = (bits[0] ^ bits[1]) == bits[2]
        signed = xor_parity_response(bits, 1.0)
        if signed not in {-1.0, 1.0}:
            return False
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


def mixed_order_absent_terms_integrate_to_zero(
    enabled_orders: frozenset[CoalitionOrder], declared_absent_order: CoalitionOrder
) -> Boolean:
    return declared_absent_order not in enabled_orders


def validate_generator_purity(
    generator: GeneratorName,
    theta: EffectCoefficient,
    strength: XorInteractionStrength,
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
            polynomial_density((0.0,) * order, theta),
            polynomial_density((0.5,) * order, theta),
            polynomial_density((1.0,) * order, theta),
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
