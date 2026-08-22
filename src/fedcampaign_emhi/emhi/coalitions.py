from itertools import combinations
from math import ceil, comb

from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.domain.types import (
    ClientCount,
    ClientId,
    CoalitionCount,
    CoalitionMembers,
    Probability,
)


def coalition_count(client_count: ClientCount, maximum_order: CoalitionOrder) -> CoalitionCount:
    return sum(comb(client_count, order) for order in range(1, int(maximum_order) + 1))


def required_outside_client_count(
    complement_size: ClientCount,
    minimum_available_outside_clients: ClientCount,
    minimum_available_outside_fraction: Probability,
) -> ClientCount:
    fractional = ceil(minimum_available_outside_fraction * complement_size)
    return max(minimum_available_outside_clients, fractional)


def enumerate_coalitions(
    client_ids: tuple[ClientId, ...], maximum_order: CoalitionOrder
) -> tuple[CoalitionMembers, ...]:
    ordered = tuple(sorted(client_ids))
    coalitions: list[CoalitionMembers] = []
    for order in range(1, int(maximum_order) + 1):
        coalition_order = CoalitionOrder(order)
        for members in combinations(ordered, order):
            coalitions.append(CoalitionMembers(client_ids=members, order=coalition_order))
    return tuple(coalitions)


def complement_members(
    selected_client_ids: tuple[ClientId, ...], coalition_client_ids: tuple[ClientId, ...]
) -> tuple[ClientId, ...]:
    coalition = set(coalition_client_ids)
    return tuple(client_id for client_id in selected_client_ids if client_id not in coalition)


def proper_subset_members(coalition: CoalitionMembers) -> tuple[CoalitionMembers, ...]:
    subsets: list[CoalitionMembers] = []
    for order in range(1, int(coalition.order)):
        coalition_order = CoalitionOrder(order)
        for members in combinations(coalition.client_ids, order):
            subsets.append(CoalitionMembers(client_ids=members, order=coalition_order))
    return tuple(subsets)
