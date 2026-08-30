import pytest

from fedcampaign_emhi.analysis.multiplicity import (
    HolmHypothesisInput,
    primary_holm_family,
    primary_holm_family_identifiers,
)
from fedcampaign_emhi.domain.enums import ClaimState


def primary_inputs() -> tuple[HolmHypothesisInput, ...]:
    return tuple(
        HolmHypothesisInput(
            identifier=identifier,
            raw_p_value=0.01 if index == 0 else None,
            decision=ClaimState.SUPPORTED if index == 0 else ClaimState.NOT_TESTED,
        )
        for index, identifier in enumerate(primary_holm_family_identifiers())
    )


def test_primary_holm_retains_fixed_family_size_for_not_tested_hypotheses() -> None:
    results = primary_holm_family(primary_inputs())

    assert len(results) == 5
    assert results[0].adjusted_p_value == 0.05
    assert all(result.holm_input_p_value == 1.0 for result in results[1:])
    assert all(result.adjusted_p_value is None for result in results[1:])


def test_fixed_holm_family_rejects_missing_or_duplicate_identifiers() -> None:
    with pytest.raises(ValueError):
        primary_holm_family(primary_inputs()[:-1])
    with pytest.raises(ValueError):
        primary_holm_family((*primary_inputs(), primary_inputs()[0]))
