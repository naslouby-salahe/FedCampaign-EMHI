from fedcampaign_emhi.domain.types import EpochCount, FiniteFloat, PositiveInt


def persistence_is_triggered(
    exceedances: tuple[bool, ...],
    required_exceedances: PositiveInt,
    window_epochs: EpochCount,
) -> bool:
    if window_epochs <= 0:
        raise ValueError("window_epochs must be positive")
    examined = exceedances[-window_epochs:]
    if len(examined) < required_exceedances:
        return False
    return sum(1 for exceeded in examined if exceeded) >= required_exceedances


def score_exceeds_threshold(score: FiniteFloat, threshold: FiniteFloat) -> bool:
    return score >= threshold
