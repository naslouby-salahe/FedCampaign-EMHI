from scipy.stats import norm

from fedcampaign_emhi.domain.types import FiniteFloat, RankValue


def standard_normal_cdf(gaussian_coordinate: FiniteFloat) -> RankValue:
    return float(norm.cdf(gaussian_coordinate))
