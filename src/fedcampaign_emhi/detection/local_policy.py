from fedcampaign_emhi.domain.types import EpochCount, EpochIndexValue, FiniteFloat, PositiveInt


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


def first_local_stop_epoch(
    exceedances: tuple[bool, ...],
    required_exceedances: PositiveInt,
    window_epochs: EpochCount,
) -> EpochIndexValue | None:
    for end_index in range(1, len(exceedances) + 1):
        if persistence_is_triggered(exceedances[:end_index], required_exceedances, window_epochs):
            return end_index - 1
    return None
