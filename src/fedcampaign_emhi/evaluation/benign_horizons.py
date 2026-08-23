from fedcampaign_emhi.domain.types import BenignHorizon, EpochIndexValue


def sequential_stop_reset_epochs(
    horizons: tuple[BenignHorizon, ...],
) -> tuple[EpochIndexValue, ...]:
    return tuple(horizon.start_epoch for horizon in horizons)


def horizons_are_nonoverlapping(horizons: tuple[BenignHorizon, ...]) -> bool:
    seen: list[EpochIndexValue] = []
    for horizon in horizons:
        for epoch in horizon.epoch_indexes:
            if epoch in seen:
                return False
            seen.append(epoch)
    return True
