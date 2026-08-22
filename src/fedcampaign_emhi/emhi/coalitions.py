from math import ceil, comb

from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.domain.types import ClientCount, CoalitionCount, Probability


def coalition_count(client_count: ClientCount, maximum_order: CoalitionOrder) -> CoalitionCount:
    return sum(comb(client_count, order) for order in range(1, int(maximum_order) + 1))


def required_outside_client_count(
    complement_size: ClientCount,
    minimum_available_outside_clients: ClientCount,
    minimum_available_outside_fraction: Probability,
) -> ClientCount:
    fractional = ceil(minimum_available_outside_fraction * complement_size)
    return max(minimum_available_outside_clients, fractional)
