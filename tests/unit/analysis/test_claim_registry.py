import pytest

from fedcampaign_emhi.analysis.claim_registry import (
    ALL_REGISTRY_STATES,
    ClaimRegistryEntry,
    compute_registry_state,
    defect_blocks_claim,
    not_tested_requires_eligibility_failure,
    registry_states_are_distinct,
    state_is_byte_exact_serializable,
)
from fedcampaign_emhi.domain.enums import ClaimState


def test_all_seven_states_are_declared_byte_exact() -> None:
    assert set(ALL_REGISTRY_STATES) == set(ClaimState)
    for state in ALL_REGISTRY_STATES:
        assert state_is_byte_exact_serializable(state) is True


def test_registry_states_are_distinct() -> None:
    assert registry_states_are_distinct(ALL_REGISTRY_STATES) is True


def test_entry_rejects_more_completed_than_mandatory() -> None:
    with pytest.raises(ValueError):
        ClaimRegistryEntry(
            claim_name="strict ODI",
            state=ClaimState.SUPPORTED,
            source_artifact_hash="a" * 64,
            mandatory_cell_count=5,
            completed_cell_count=6,
        )


def test_defect_blocks_claim_until_artifact_is_current() -> None:
    assert defect_blocks_claim(None, True) is True
    entry_state = ClaimState.SUPPORTED
    assert defect_blocks_claim(entry_state, False) is True
    assert defect_blocks_claim(entry_state, True) is False


def test_not_tested_reserved_for_eligibility_failure() -> None:
    assert not_tested_requires_eligibility_failure(ClaimState.NOT_TESTED, True) is True
    assert not_tested_requires_eligibility_failure(ClaimState.NOT_TESTED, False) is False
    assert not_tested_requires_eligibility_failure(ClaimState.SUPPORTED, False) is True


def test_compute_registry_state_decision_order() -> None:
    base = dict(
        gates_pass=True,
        mechanism_only_evidence=False,
        partial_support=False,
        null_observation=False,
        conditionality_declared=False,
        eligibility_failed=False,
    )
    assert compute_registry_state(**base) is ClaimState.SUPPORTED
    assert compute_registry_state(**{**base, "eligibility_failed": True}) is ClaimState.NOT_TESTED
    assert compute_registry_state(**{**base, "null_observation": True}) is ClaimState.NULL_RESULT
    assert compute_registry_state(**{**base, "gates_pass": False}) is ClaimState.NOT_SUPPORTED
    assert (
        compute_registry_state(**{**base, "mechanism_only_evidence": True})
        is ClaimState.MECHANISM_ONLY
    )
    assert (
        compute_registry_state(**{**base, "conditionality_declared": True})
        is ClaimState.CONDITIONAL
    )
    assert (
        compute_registry_state(**{**base, "partial_support": True})
        is ClaimState.PARTIALLY_SUPPORTED
    )
