from fedcampaign_emhi.config.loading import histogram_edges
from fedcampaign_emhi.domain.types import BinCount, BinIndex, ClientId, RankValue


def exact_exclusion_members(
    selected_client_ids: tuple[ClientId, ...],
    coalition_client_ids: tuple[ClientId, ...],
) -> tuple[ClientId, ...]:
    coalition = set(coalition_client_ids)
    return tuple(client_id for client_id in selected_client_ids if client_id not in coalition)


def histogram_bin_index(rank: RankValue, bin_count: BinCount) -> BinIndex:
    raw_index = int(rank * bin_count)
    last_index = bin_count - 1
    if raw_index > last_index:
        return last_index
    return raw_index


def equal_width_histogram_edges(bin_count: BinCount) -> tuple[RankValue, ...]:
    return histogram_edges(bin_count)
