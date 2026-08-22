from fedcampaign_emhi.domain.types import RankValue


def mean_rank_fusion(ranks: tuple[RankValue, ...]) -> RankValue:
    if not ranks:
        raise ValueError("mean rank fusion requires at least one client rank")
    return sum(ranks) / len(ranks)


def max_rank_fusion(ranks: tuple[RankValue, ...]) -> RankValue:
    if not ranks:
        raise ValueError("max rank fusion requires at least one client rank")
    return max(ranks)
