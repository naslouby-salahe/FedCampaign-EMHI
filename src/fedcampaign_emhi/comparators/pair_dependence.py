from fedcampaign_emhi.domain.types import FiniteFloat, RankValue
from fedcampaign_emhi.emhi.innovations import centered_scaled_coordinate


def pair_dependence_moment(left_rank: RankValue, right_rank: RankValue) -> FiniteFloat:
    return ((2.0 * left_rank) - 1.0) * ((2.0 * right_rank) - 1.0)


def pair_dependence_nonconformity(
    moment: FiniteFloat,
    benign_mean: FiniteFloat,
    benign_deviation: FiniteFloat,
    scale_floor: FiniteFloat,
) -> FiniteFloat:
    standardized = centered_scaled_coordinate(moment, benign_mean, benign_deviation, scale_floor)
    if standardized < 0.0:
        return -standardized
    return standardized
