from dataclasses import dataclass

from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.types import (
    EpochIndexValue,
    OdiIndicator,
    RecordCount,
    StrictOdiOutcome,
)
from fedcampaign_emhi.emhi.projection import blocked_fold_sizes


def strict_odi_outcome(
    global_stop_epoch: EpochIndexValue | None,
    local_stop_epochs: tuple[EpochIndexValue | None, ...],
) -> StrictOdiOutcome:
    finite_local = [epoch for epoch in local_stop_epochs if epoch is not None]
    earliest_local = min(finite_local) if finite_local else None
    if global_stop_epoch is None or earliest_local is None:
        indicator = 0
    else:
        indicator = int(global_stop_epoch < earliest_local)
    return StrictOdiOutcome(
        global_stop_epoch=global_stop_epoch,
        earliest_local_stop_epoch=earliest_local,
        indicator=indicator,
    )


@dataclass(frozen=True)
class SmokeFixtureResult:
    blocked_fold_sizes: tuple[RecordCount, ...]
    strict_odi_indicator: OdiIndicator


def smoke_module_fixtures(loaded: LoadedScientificConfiguration) -> SmokeFixtureResult:
    del loaded
    return SmokeFixtureResult(
        blocked_fold_sizes=blocked_fold_sizes(11, 5),
        strict_odi_indicator=strict_odi_outcome(4, (5, 8)).indicator,
    )
