from fedcampaign_emhi.domain.types import FiniteFloat, RankValue
from fedcampaign_emhi.emhi.innovations import centered_scaled_coordinate


def lancaster_triple_moment(
    first_rank: RankValue, second_rank: RankValue, third_rank: RankValue
) -> FiniteFloat:
    return ((2.0 * first_rank) - 1.0) * ((2.0 * second_rank) - 1.0) * ((2.0 * third_rank) - 1.0)


def lancaster_triple_nonconformity(
    moment: FiniteFloat,
    benign_mean: FiniteFloat,
    benign_deviation: FiniteFloat,
    scale_floor: FiniteFloat,
) -> FiniteFloat:
    standardized = centered_scaled_coordinate(moment, benign_mean, benign_deviation, scale_floor)
    if standardized < 0.0:
        return -standardized
    return standardized
