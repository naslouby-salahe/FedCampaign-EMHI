from fedcampaign_emhi.domain.types import (
    ClientCount,
    ClientId,
    EpochCount,
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
