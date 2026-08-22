from math import sqrt
from random import Random

from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.domain.types import (
    ClientCount,
    ClientId,
    EffectCoefficient,
    FiniteFloat,
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
    generator = Random(thirty_two_bit_seed(seed))
    return tuple(generator.random() for _index in range(client_count))


def sample_pure_polynomial_ranks(
    order: CoalitionOrder,
    theta: EffectCoefficient,
    remaining_client_count: ClientCount,
    seed: SeedValue,
) -> tuple[RankValue, ...]:
    if not polynomial_density_is_valid(theta, order):
        raise ValueError("pure polynomial density would be negative")
    generator = Random(thirty_two_bit_seed(seed))
    envelope = polynomial_envelope(theta, order)
    while True:
        target_ranks = tuple(generator.random() for _member in range(int(order)))
        density = polynomial_density(target_ranks, theta)
        if density <= 0.0 or density != density:
            raise ValueError("pure polynomial density invariant violated")
        if generator.random() * envelope <= density:
            remainder = tuple(generator.random() for _client in range(remaining_client_count))
            return target_ranks + remainder


def sample_xor_ranks(
    strength: FiniteFloat, remaining_client_count: ClientCount, seed: SeedValue
) -> tuple[RankValue, ...]:
    generator = Random(thirty_two_bit_seed(seed))
    first = 1 if generator.random() < 0.5 else 0
    second = 1 if generator.random() < 0.5 else 0
    match_probability = 0.5 + (0.5 * strength)
    third = (first ^ second) if generator.random() < match_probability else 1 - (first ^ second)
    bits = (first, second, third)
    uniforms = tuple(generator.random() for _bit in bits)
    target_ranks = tuple((bit + uniform) / 2.0 for bit, uniform in zip(bits, uniforms, strict=True))
    remainder = tuple(generator.random() for _client in range(remaining_client_count))
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
