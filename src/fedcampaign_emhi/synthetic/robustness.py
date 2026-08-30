from math import floor

import numpy as np

from fedcampaign_emhi.domain.types import (
    Boolean,
    ClientCount,
    ClientId,
    FiniteFloat,
    NumericalFloor,
    Probability,
    RankValue,
    ScoreShift,
    SeedValue,
)
from fedcampaign_emhi.emhi.coalitions import required_outside_client_count
from fedcampaign_emhi.runtime.determinism import thirty_two_bit_seed
from fedcampaign_emhi.synthetic.pure_order import lexicographic_target_clients


def round_half_up(non_negative_count: FiniteFloat) -> ClientCount:
    if non_negative_count < 0.0:
        raise ValueError("round_half_up is defined for non-negative counts")
    return floor(non_negative_count + 0.5)


def contaminated_outside_count(fraction: Probability, complement_size: ClientCount) -> ClientCount:
    return round_half_up(fraction * complement_size)


def contaminated_outside_clients(
    complement_client_ids: tuple[ClientId, ...], fraction: Probability
) -> tuple[ClientId, ...]:
    ordered = tuple(sorted(complement_client_ids))
    count = contaminated_outside_count(fraction, len(ordered))
    return ordered[:count]


def contaminate_rank(
    rank: RankValue, outside_rank_shift: ScoreShift, rank_clip_epsilon: NumericalFloor
) -> RankValue:
    shifted = rank + outside_rank_shift
    upper = 1.0 - rank_clip_epsilon
    if shifted > upper:
        return upper
    return shifted


def availability_mask(
    client_ids: tuple[ClientId, ...], unavailable_fraction: Probability, seed: SeedValue
) -> tuple[ClientId, ...]:
    generator = np.random.default_rng(thirty_two_bit_seed(seed))
    available: list[ClientId] = []
    stay_probability = 1.0 - unavailable_fraction
    for client_id in client_ids:
        if float(generator.random()) < stay_probability:
            available.append(client_id)
    return tuple(available)


def dropout_coalition_is_active(
    coalition_client_ids: tuple[ClientId, ...],
    available_client_ids: tuple[ClientId, ...],
    selected_client_ids: tuple[ClientId, ...],
    minimum_available_outside_clients: ClientCount,
    minimum_available_outside_fraction: Probability,
) -> Boolean:
    available = set(available_client_ids)
    if any(member not in available for member in coalition_client_ids):
        return False
    complement = tuple(
        client_id for client_id in selected_client_ids if client_id not in set(coalition_client_ids)
    )
    available_outside = tuple(client_id for client_id in complement if client_id in available)
    required = required_outside_client_count(
        len(complement),
        minimum_available_outside_clients,
        minimum_available_outside_fraction,
    )
    return len(available_outside) >= required


def outside_contamination_targets(client_ids: tuple[ClientId, ...]) -> tuple[ClientId, ...]:
    return lexicographic_target_clients(client_ids, 3)
