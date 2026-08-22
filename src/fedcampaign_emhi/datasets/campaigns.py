from fedcampaign_emhi.domain.types import (
    ClientCount,
    ClientId,
    EpochCount,
    EpochIndexValue,
    PositiveEpochCount,
)


def merge_malicious_runs(
    malicious_epochs: tuple[EpochIndexValue, ...],
    merge_max_intervening_benign_epochs: EpochCount,
) -> tuple[tuple[EpochIndexValue, EpochIndexValue], ...]:
    if not malicious_epochs:
        return ()
    ordered = tuple(sorted(set(malicious_epochs)))
    start = ordered[0]
    previous = ordered[0]
    merged: list[tuple[EpochIndexValue, EpochIndexValue]] = []
    for epoch in ordered[1:]:
        intervening = epoch - previous - 1
        if intervening <= merge_max_intervening_benign_epochs:
            previous = epoch
            continue
        merged.append((start, previous))
        start = epoch
        previous = epoch
    merged.append((start, previous))
    return tuple(merged)


def campaign_duration_epochs(
    start_epoch: EpochIndexValue, end_epoch: EpochIndexValue
) -> EpochCount:
    return end_epoch - start_epoch + 1


def first_activity_is_distributed(
    first_malicious_epochs: tuple[EpochIndexValue, ...],
    window_epochs: PositiveEpochCount,
) -> bool:
    if not first_malicious_epochs:
        return False
    return max(first_malicious_epochs) - min(first_malicious_epochs) <= window_epochs


def campaign_has_distributed_support(
    participating_client_ids: tuple[ClientId, ...], minimum_clients: ClientCount
) -> bool:
    return len(set(participating_client_ids)) >= minimum_clients


def warmup_is_clean(
    warmup_malicious_epochs: tuple[EpochIndexValue, ...],
) -> bool:
    return not warmup_malicious_epochs
