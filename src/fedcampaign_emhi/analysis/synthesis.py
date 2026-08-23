from dataclasses import dataclass

from fedcampaign_emhi.domain.types import ComponentName, RecordCount


@dataclass(frozen=True)
class SynthesisCompleteness:
    all_mandatory_confirmatory_cells_complete: bool
    all_source_artifacts_current: bool
    all_primary_and_secondary_holm_families_resolved: bool
    all_required_bca_and_exact_binomial_bounds_computed: bool
    all_materiality_and_equivalence_gates_evaluated: bool
    all_claim_state_rules_applied: bool
    no_results_artifact_used_as_computational_input: bool

    @property
    def missing_dependencies(self) -> tuple[ComponentName, ...]:
        checks = (
            ("mandatory_confirmatory_cells", self.all_mandatory_confirmatory_cells_complete),
            ("source_artifacts_current", self.all_source_artifacts_current),
            (
                "holm_families_resolved",
                self.all_primary_and_secondary_holm_families_resolved,
            ),
            (
                "confidence_bounds_computed",
                self.all_required_bca_and_exact_binomial_bounds_computed,
            ),
            ("materiality_gates_evaluated", self.all_materiality_and_equivalence_gates_evaluated),
            ("claim_state_rules_applied", self.all_claim_state_rules_applied),
            (
                "no_results_as_input",
                self.no_results_artifact_used_as_computational_input,
            ),
        )
        return tuple(name for name, satisfied in checks if not satisfied)

    @property
    def synthesis_is_allowed(self) -> bool:
        return not self.missing_dependencies


def synthesis_may_proceed(completeness: SynthesisCompleteness) -> bool:
    return completeness.synthesis_is_allowed


def reporting_command_stops_on_missing_dependency(
    completeness: SynthesisCompleteness,
) -> ComponentName:
    if completeness.synthesis_is_allowed:
        raise ValueError("stop-with-dependency requires an incomplete synthesis state")
    first_missing = completeness.missing_dependencies[0]
    message: ComponentName = f"missing dependency: {first_missing}"
    return message


def confirmatory_cell_completion(completed: RecordCount, mandatory: RecordCount) -> bool:
    if mandatory <= 0:
        raise ValueError("mandatory cell count must be positive")
    return completed >= mandatory
