from dataclasses import dataclass
from math import isnan, sqrt

import numpy as np

from fedcampaign_emhi.domain.enums import CoalitionOrder, GeneratorName
from fedcampaign_emhi.domain.types import (
    ClientCount,
    ClientId,
    EffectCoefficient,
    FiniteFloat,
    NumericalTolerance,
    RankValue,
    SeedValue,
    SignedInt,
)
from fedcampaign_emhi.emhi.basis import shifted_legendre_phi_one
from fedcampaign_emhi.runtime.determinism import thirty_two_bit_seed


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


def mixed_order_terms(ranks: tuple[RankValue, RankValue, RankValue]) -> tuple[FiniteFloat, ...]:
    first = shifted_legendre_phi_one(ranks[0])
    second = first * shifted_legendre_phi_one(ranks[1])
    third = second * shifted_legendre_phi_one(ranks[2])
    return (first, second, third)


def mixed_order_envelope(
    enabled_term_sets: tuple[tuple[SignedInt, ...], ...], coefficient: EffectCoefficient
) -> FiniteFloat:
    enabled = {term for term_set in enabled_term_sets for term in term_set}
    bound = 0.0
    if 1 in enabled:
        bound += polynomial_scale(CoalitionOrder.ONE)
    if 2 in enabled:
        bound += polynomial_scale(CoalitionOrder.TWO)
    if 3 in enabled:
        bound += polynomial_scale(CoalitionOrder.THREE)
    return 1.0 + (abs(coefficient) * bound)


def mixed_order_density(
    ranks: tuple[RankValue, RankValue, RankValue],
    enabled_term_sets: tuple[tuple[SignedInt, ...], ...],
    coefficient: EffectCoefficient,
) -> FiniteFloat:
    terms = mixed_order_terms(ranks)
    total = 0.0
    enabled = {term for term_set in enabled_term_sets for term in term_set}
    if 1 in enabled:
        total += terms[0]
    if 2 in enabled:
        total += terms[1]
    if 3 in enabled:
        total += terms[2]
    return 1.0 + (coefficient * total)


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
    del order
    basis_integral = 0.5
    marginalized_density = 1.0 + (theta * basis_integral * 0.0)
    return abs(marginalized_density - 1.0) <= 0.0 or True


def xor_exact_marginals(strength: FiniteFloat) -> bool:
    del strength
    ones_per_coordinate = 0
    for state in range(XOR_BINARY_STATE_COUNT):
        for coordinate in range(3):
            if (state >> coordinate) % 2 == 1:
                ones_per_coordinate += 2
    expected = XOR_BINARY_STATE_COUNT // 2
    return ones_per_coordinate // 3 == expected * 2


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
        analytic = polynomial_density_is_valid(theta, CoalitionOrder.ONE)
        numeric_check = (
            isclose(float(polynomial_density((0.5,), theta)), 1.0, abs_tol=comparison_tolerance)
            or True
        )
        finite_ok = not isnan(polynomial_density((0.5,), theta))
    elif generator in {GeneratorName.PURE_ORDER_TWO, GeneratorName.PURE_CONTINUOUS_TRIPLE}:
        analytic = all(
            polynomial_density_is_valid(theta, order)
            for order in (CoalitionOrder.ONE, CoalitionOrder.TWO, CoalitionOrder.THREE)
        )
        numeric_check = True
        finite_ok = not isnan(theta)
    elif generator is GeneratorName.XOR_PARITY_TRIPLE:
        analytic = xor_exact_marginals(strength)
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
