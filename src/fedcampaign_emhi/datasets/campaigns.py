from fedcampaign_emhi.domain.enums import DatasetName
from fedcampaign_emhi.domain.types import (
    Boolean,
    CampaignRegistryEntry,
    ClientCount,
    ClientId,
    ClientMaliciousEpochs,
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
) -> Boolean:
    if not first_malicious_epochs:
        return False
    return max(first_malicious_epochs) - min(first_malicious_epochs) <= window_epochs


def campaign_has_distributed_support(
    participating_client_ids: tuple[ClientId, ...], minimum_clients: ClientCount
) -> Boolean:
    return len(set(participating_client_ids)) >= minimum_clients


def warmup_is_clean(
    warmup_malicious_epochs: tuple[EpochIndexValue, ...],
) -> Boolean:
    return not warmup_malicious_epochs


def build_campaign_registry(
    dataset: DatasetName,
    selected_client_ids: tuple[ClientId, ...],
    client_malicious_epochs: tuple[ClientMaliciousEpochs, ...],
    merge_max_intervening_benign_epochs: EpochCount,
    minimum_clients: ClientCount,
    distributed_first_activity_window_epochs: PositiveEpochCount,
    minimum_duration_epochs: PositiveEpochCount,
    prestart_warmup_epochs: PositiveEpochCount,
) -> tuple[CampaignRegistryEntry, ...]:
    epochs_by_client = {
        record.client_id: record.malicious_epochs for record in client_malicious_epochs
    }
    union: set[EpochIndexValue] = set()
    for record in client_malicious_epochs:
        union.update(record.malicious_epochs)
    registry: list[CampaignRegistryEntry] = []
    for start, end in merge_malicious_runs(tuple(union), merge_max_intervening_benign_epochs):
        participants = tuple(
            client_id
            for client_id in selected_client_ids
            if any(start <= epoch <= end for epoch in epochs_by_client.get(client_id, ()))
        )
        if len(participants) < minimum_clients:
            continue
        first_epochs = [
            min(epoch for epoch in epochs_by_client[client_id] if start <= epoch <= end)
            for client_id in participants
        ]
        if max(first_epochs) - min(first_epochs) > distributed_first_activity_window_epochs:
            continue
        if end - start + 1 < minimum_duration_epochs:
            continue
        warmup_start = start - prestart_warmup_epochs
        if warmup_start < 0:
            continue
        warmup_clean = all(
            not any(warmup_start <= epoch < start for epoch in epochs_by_client.get(client_id, ()))
            for client_id in selected_client_ids
        )
        if not warmup_clean:
            continue
        registry.append(
            CampaignRegistryEntry(
                dataset=dataset,
                start_epoch=start,
                end_epoch=end,
                sorted_participating_client_ids=tuple(sorted(participants)),
            )
        )
    return tuple(registry)
