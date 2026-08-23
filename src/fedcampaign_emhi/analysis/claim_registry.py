from dataclasses import dataclass

from fedcampaign_emhi.domain.enums import ClaimState
from fedcampaign_emhi.domain.types import ComponentName, RecordCount, Sha256Hex

ALL_REGISTRY_STATES: tuple[ClaimState, ...] = tuple(ClaimState)


@dataclass(frozen=True)
class ClaimRegistryEntry:
    claim_name: ComponentName
    state: ClaimState
    source_artifact_hash: Sha256Hex
    mandatory_cell_count: RecordCount
    completed_cell_count: RecordCount

    def __post_init__(self) -> None:
        if self.completed_cell_count > self.mandatory_cell_count:
            raise ValueError("completed cells cannot exceed the declared mandatory cells")


def state_is_byte_exact_serializable(state: ClaimState) -> bool:
    return state.value == state.value.strip() and " " not in state.value


def registry_states_are_distinct(states: tuple[ClaimState, ...]) -> bool:
    return len(set(states)) == len(states)


def defect_blocks_claim(claimed_state: ClaimState | None, artifact_current: bool) -> bool:
    if claimed_state is None:
        return True
    return not artifact_current


def not_tested_requires_eligibility_failure(state: ClaimState, eligibility_failed: bool) -> bool:
    if state is ClaimState.NOT_TESTED:
        return eligibility_failed
    return True


def compute_registry_state(
    gates_pass: bool,
    mechanism_only_evidence: bool,
    partial_support: bool,
    null_observation: bool,
    conditionality_declared: bool,
    eligibility_failed: bool,
) -> ClaimState:
    if eligibility_failed:
        return ClaimState.NOT_TESTED
    if null_observation:
        return ClaimState.NULL_RESULT
    if not gates_pass:
        return ClaimState.NOT_SUPPORTED
    if mechanism_only_evidence:
        return ClaimState.MECHANISM_ONLY
    if conditionality_declared:
        return ClaimState.CONDITIONAL
    if partial_support:
        return ClaimState.PARTIALLY_SUPPORTED
    return ClaimState.SUPPORTED
