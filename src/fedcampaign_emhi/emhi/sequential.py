from fedcampaign_emhi.domain.types import (
    Boolean,
    ClientCount,
    ClientId,
    EpochIndexValue,
    EvidenceFactor,
    GlobalEvidenceState,
    PositiveEpochCount,
    ThresholdValue,
)


def initial_global_state() -> GlobalEvidenceState:
    return 0.0


def next_global_state(
    previous_state: GlobalEvidenceState, evidence_factor: EvidenceFactor
) -> GlobalEvidenceState:
    return (previous_state + 1.0) * evidence_factor


def threshold_predicate(global_state: GlobalEvidenceState, threshold: ThresholdValue) -> Boolean:
    return global_state >= threshold


def statistical_stop(
    global_state: GlobalEvidenceState,
    threshold: ThresholdValue,
    window_client_ids: tuple[ClientId, ...],
    minimum_clients: ClientCount,
) -> Boolean:
    return threshold_predicate(global_state, threshold) and distributed_support_predicate(
        window_client_ids, minimum_clients
    )


def distributed_support_predicate(
    window_client_ids: tuple[ClientId, ...], minimum_clients: ClientCount
) -> Boolean:
    return len(set(window_client_ids)) >= minimum_clients


def coalition_materially_active(
    operational_factor: EvidenceFactor, material_threshold: EvidenceFactor
) -> Boolean:
    return operational_factor >= material_threshold


def trailing_support_window_client_ids(
    active_client_ids_per_epoch: tuple[tuple[ClientId, ...], ...],
    window_epochs: PositiveEpochCount,
) -> tuple[ClientId, ...]:
    if window_epochs <= 0:
        raise ValueError("window_epochs must be positive")
    seen: set[ClientId] = set()
    union: list[ClientId] = []
    for client_ids in active_client_ids_per_epoch[-window_epochs:]:
        for client_id in client_ids:
            if client_id not in seen:
                seen.add(client_id)
                union.append(client_id)
    return tuple(union)


def trailing_window_support_predicate(
    active_client_ids_per_epoch: tuple[tuple[ClientId, ...], ...],
    window_epochs: PositiveEpochCount,
    minimum_clients: ClientCount,
) -> Boolean:
    return distributed_support_predicate(
        trailing_support_window_client_ids(active_client_ids_per_epoch, window_epochs),
        minimum_clients,
    )


def first_global_stop_epoch(
    evidence_factors: tuple[EvidenceFactor, ...],
    support_predicates: tuple[Boolean, ...],
    threshold: ThresholdValue,
) -> EpochIndexValue | None:
    if len(evidence_factors) != len(support_predicates):
        raise ValueError("evidence_factors and support_predicates must be aligned")
    state = initial_global_state()
    for epoch_index, (factor, supported) in enumerate(
        zip(evidence_factors, support_predicates, strict=True)
    ):
        state = next_global_state(state, factor)
        if threshold_predicate(state, threshold) and supported:
            return epoch_index
    return None
