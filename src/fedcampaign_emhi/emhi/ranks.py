from fedcampaign_emhi.domain.types import NumericalFloor, RankValue


def clip_rank(rank: RankValue, epsilon: NumericalFloor) -> RankValue:
    if rank < epsilon:
        return epsilon
    upper = 1.0 - epsilon
    if rank > upper:
        return upper
    return rank
