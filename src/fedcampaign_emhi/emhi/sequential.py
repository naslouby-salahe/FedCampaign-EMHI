from fedcampaign_emhi.domain.types import (
    ClientCount,
    ClientId,
    EpochCount,
    EpochIndexValue,
    EvidenceFactor,
    FiniteFloat,
    ThresholdValue,
)


def initial_global_state() -> FiniteFloat:
    return 0.0


def next_global_state(previous_state: FiniteFloat, evidence_factor: EvidenceFactor) -> FiniteFloat:
    return (previous_state + 1.0) * evidence_factor


def threshold_predicate(global_state: FiniteFloat, threshold: ThresholdValue) -> bool:
    return global_state >= threshold


def distributed_support_predicate(
    window_client_ids: tuple[ClientId, ...], minimum_clients: ClientCount
) -> bool:
    return len(set(window_client_ids)) >= minimum_clients


def statistical_stop(
    global_state: FiniteFloat,
    threshold: ThresholdValue,
    window_client_ids: tuple[ClientId, ...],
    minimum_clients: ClientCount,
) -> bool:
    return threshold_predicate(global_state, threshold) and distributed_support_predicate(
        window_client_ids, minimum_clients
    )


def trailing_window_length(window_epochs: EpochCount, elapsed_epochs: EpochCount) -> EpochCount:
    if elapsed_epochs < window_epochs:
        return elapsed_epochs
    return window_epochs


def first_global_stop_epoch(
    evidence_factors: tuple[EvidenceFactor, ...],
    support_predicates: tuple[bool, ...],
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
