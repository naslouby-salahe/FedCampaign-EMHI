from random import Random

from fedcampaign_emhi.domain.types import (
    FiniteFloat,
    Probability,
    RankValue,
    SeedValue,
    SignedInt,
)
from fedcampaign_emhi.emhi.basis import shifted_legendre_phi_one
from fedcampaign_emhi.runtime.determinism import thirty_two_bit_seed


def initial_markov_state(negative_probability: Probability, seed: SeedValue) -> SignedInt:
    generator = Random(thirty_two_bit_seed(seed))
    if generator.random() < negative_probability:
        return -1
    return 1


def next_markov_state(
    current_state: SignedInt, same_state_probability: Probability, seed: SeedValue
) -> SignedInt:
    generator = Random(thirty_two_bit_seed(seed))
    if generator.random() < same_state_probability:
        return current_state
    return -current_state


def outside_rank_from_interval(lower: RankValue, upper: RankValue, seed: SeedValue) -> RankValue:
    generator = Random(thirty_two_bit_seed(seed))
    return generator.uniform(lower, upper)


def context_conditional_density(
    ranks: tuple[RankValue, ...], theta: FiniteFloat, latent_state: SignedInt
) -> FiniteFloat:
    product = 1.0
    for rank in ranks:
        product *= shifted_legendre_phi_one(rank)
    return 1.0 + (theta * latent_state * product)
