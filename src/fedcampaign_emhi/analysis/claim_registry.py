from dataclasses import dataclass

from fedcampaign_emhi.domain.types import ComponentName, RecordCount, Sha256Hex


@dataclass(frozen=True)
class ClaimRegistryState:
    label: ComponentName


SUPPORTED = ClaimRegistryState("SUPPORTED")
PARTIALLY_SUPPORTED = ClaimRegistryState("PARTIALLY_SUPPORTED")
MECHANISM_ONLY = ClaimRegistryState("MECHANISM_ONLY")
CONDITIONAL = ClaimRegistryState("CONDITIONAL")
NULL_RESULT = ClaimRegistryState("NULL_RESULT")
NOT_SUPPORTED = ClaimRegistryState("NOT_SUPPORTED")
NOT_TESTED = ClaimRegistryState("NOT_TESTED")

ALL_REGISTRY_STATES: tuple[ClaimRegistryState, ...] = (
    SUPPORTED,
    PARTIALLY_SUPPORTED,
    MECHANISM_ONLY,
    CONDITIONAL,
    NULL_RESULT,
    NOT_SUPPORTED,
    NOT_TESTED,
)


@dataclass(frozen=True)
class ClaimRegistryEntry:
    claim_name: ComponentName
    state: ClaimRegistryState
    source_artifact_hash: Sha256Hex
    mandatory_cell_count: RecordCount
    completed_cell_count: RecordCount

    def __post_init__(self) -> None:
        if self.completed_cell_count > self.mandatory_cell_count:
            raise ValueError("completed cells cannot exceed the declared mandatory cells")


def state_is_byte_exact_serializable(state: ClaimRegistryState) -> bool:
    return state.label == state.label.strip() and " " not in str(state.label)


def registry_states_are_distinct(states: tuple[ClaimRegistryState, ...]) -> bool:
    labels = [state.label for state in states]
    return len(set(labels)) == len(labels)


def defect_blocks_claim(claimed_state: ClaimRegistryState | None, artifact_current: bool) -> bool:
    if claimed_state is None:
        return True
    return not artifact_current


def not_tested_requires_eligibility_failure(
    state: ClaimRegistryState, eligibility_failed: bool
) -> bool:
    if state is NOT_TESTED:
        return eligibility_failed
    return True


def compute_registry_state(
    gates_pass: bool,
    mechanism_only_evidence: bool,
    partial_support: bool,
    null_observation: bool,
    conditionality_declared: bool,
    eligibility_failed: bool,
) -> ClaimRegistryState:
    if eligibility_failed:
        return NOT_TESTED
    if null_observation:
        return NULL_RESULT
    if not gates_pass:
        return NOT_SUPPORTED
    if mechanism_only_evidence:
        return MECHANISM_ONLY
    if conditionality_declared:
        return CONDITIONAL
    if partial_support:
        return PARTIALLY_SUPPORTED
    return SUPPORTED
