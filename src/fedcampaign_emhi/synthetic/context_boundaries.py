from dataclasses import dataclass

import numpy as np

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.domain.types import (
    CellCount,
    ClientId,
    FiniteFloat,
    PositiveInt,
    Probability,
    RankValue,
    SeedValue,
    SignedInt,
)
from fedcampaign_emhi.emhi.basis import shifted_legendre_phi_one
from fedcampaign_emhi.runtime.determinism import thirty_two_bit_seed


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
    support_per_context: PositiveInt,
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


def initial_markov_state(negative_probability: Probability, seed: SeedValue) -> SignedInt:
    generator = np.random.default_rng(thirty_two_bit_seed(seed))
    if float(generator.random()) < negative_probability:
        return -1
    return 1


def next_markov_state(
    current_state: SignedInt, same_state_probability: Probability, seed: SeedValue
) -> SignedInt:
    generator = np.random.default_rng(thirty_two_bit_seed(seed))
    if float(generator.random()) < same_state_probability:
        return current_state
    return -current_state


def outside_rank_from_interval(lower: RankValue, upper: RankValue, seed: SeedValue) -> RankValue:
    generator = np.random.default_rng(thirty_two_bit_seed(seed))
    return float(generator.uniform(lower, upper))


def context_conditional_density(
    ranks: tuple[RankValue, ...], theta: FiniteFloat, latent_state: SignedInt
) -> FiniteFloat:
    product = 1.0
    for rank in ranks:
        product *= shifted_legendre_phi_one(rank)
    return 1.0 + (theta * latent_state * product)
