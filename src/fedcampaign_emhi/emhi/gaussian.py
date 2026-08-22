from math import erf, sqrt

from fedcampaign_emhi.domain.types import FiniteFloat, RankValue


def standard_normal_cdf(gaussian_coordinate: FiniteFloat) -> RankValue:
    return 0.5 * (1.0 + erf(gaussian_coordinate / sqrt(2.0)))
