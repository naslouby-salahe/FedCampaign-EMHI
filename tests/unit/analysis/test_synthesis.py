import pytest

from fedcampaign_emhi.analysis.synthesis import (
    SynthesisCompleteness,
    confirmatory_cell_completion,
    reporting_command_stops_on_missing_dependency,
    synthesis_may_proceed,
)


def complete() -> SynthesisCompleteness:
    return SynthesisCompleteness(
        all_mandatory_confirmatory_cells_complete=True,
        all_source_artifacts_current=True,
        all_primary_and_secondary_holm_families_resolved=True,
        all_required_bca_and_exact_binomial_bounds_computed=True,
        all_materiality_and_equivalence_gates_evaluated=True,
        all_claim_state_rules_applied=True,
        no_results_artifact_used_as_computational_input=True,
    )


def test_complete_synthesis_is_allowed() -> None:
    assert synthesis_may_proceed(complete()) is True
    assert complete().missing_dependencies == ()


def test_each_missing_dependency_is_named_and_blocks_synthesis() -> None:
    base = complete()
    blocked = SynthesisCompleteness(
        all_mandatory_confirmatory_cells_complete=False,
        all_source_artifacts_current=base.all_source_artifacts_current,
        all_primary_and_secondary_holm_families_resolved=(
            base.all_primary_and_secondary_holm_families_resolved
        ),
        all_required_bca_and_exact_binomial_bounds_computed=(
            base.all_required_bca_and_exact_binomial_bounds_computed
        ),
        all_materiality_and_equivalence_gates_evaluated=(
            base.all_materiality_and_equivalence_gates_evaluated
        ),
        all_claim_state_rules_applied=base.all_claim_state_rules_applied,
        no_results_artifact_used_as_computational_input=(
            base.no_results_artifact_used_as_computational_input
        ),
    )
    assert synthesis_may_proceed(blocked) is False
    assert blocked.missing_dependencies == ("mandatory_confirmatory_cells",)


def test_reporting_stops_with_precise_missing_dependency() -> None:
    base = complete()
    stale = SynthesisCompleteness(
        all_mandatory_confirmatory_cells_complete=True,
        all_source_artifacts_current=False,
        all_primary_and_secondary_holm_families_resolved=True,
        all_required_bca_and_exact_binomial_bounds_computed=False,
        all_materiality_and_equivalence_gates_evaluated=True,
        all_claim_state_rules_applied=True,
        no_results_artifact_used_as_computational_input=True,
    )
    message = reporting_command_stops_on_missing_dependency(stale)
    assert "source_artifacts_current" in message
    with pytest.raises(ValueError):
        reporting_command_stops_on_missing_dependency(base)


def test_confirmatory_cell_completion_gate() -> None:
    assert confirmatory_cell_completion(10, 10) is True
    assert confirmatory_cell_completion(9, 10) is False
    with pytest.raises(ValueError):
        confirmatory_cell_completion(5, 0)
