import pytest

from fedcampaign_emhi.domain.enums import ExperimentName
from fedcampaign_emhi.reporting.evidence import (
    ReportSourceBinding,
    claim_state_requires_complete_confirmatory_manifest,
    figure_table_has_single_source,
    overwrite_replaces_same_export,
    report_performs_no_new_computation,
    reporting_dependency_change_invalidates_cache,
    results_are_scientific_inputs,
    results_are_terminal_exports,
)


def make_binding() -> ReportSourceBinding:
    return ReportSourceBinding(
        experiment_name=ExperimentName.PRIMARY_STRICT_ODI_EVALUATION,
        source_analysis_hash="a" * 64,
        report_dependency_fingerprint="b" * 64,
        confirmatory_execution_manifest_hash="c" * 64,
        source_scientific_cell_path="results/primary_strict_odi_evaluation/cell.json",
        source_artifact_hashes=("d" * 64, "e" * 64),
    )


def test_report_is_read_only_over_verified_evidence() -> None:
    assert results_are_terminal_exports() is True
    assert results_are_scientific_inputs() is False
    assert report_performs_no_new_computation(make_binding()) is True


def test_claim_eligibility_requires_every_mandatory_confirmatory_cell() -> None:
    assert claim_state_requires_complete_confirmatory_manifest(3, 3) is True
    assert claim_state_requires_complete_confirmatory_manifest(3, 2) is False
    with pytest.raises(ValueError):
        claim_state_requires_complete_confirmatory_manifest(0, 0)
    with pytest.raises(ValueError):
        claim_state_requires_complete_confirmatory_manifest(2, 5)


def test_overwrite_targets_same_export_only() -> None:
    path = "results/exports/tables.json"
    assert overwrite_replaces_same_export(path, path) is True
    assert overwrite_replaces_same_export(path, "results/exports/other.json") is False


def test_reporting_dependency_change_invalidates_cache() -> None:
    binding = make_binding()
    assert (
        reporting_dependency_change_invalidates_cache(
            binding.report_dependency_fingerprint, "f" * 64
        )
        is True
    )
    assert (
        reporting_dependency_change_invalidates_cache(
            binding.report_dependency_fingerprint, binding.report_dependency_fingerprint
        )
        is False
    )


def test_single_source_rule_and_provenance_hashes() -> None:
    binding = make_binding()
    assert figure_table_has_single_source(binding) is True
    empty = ReportSourceBinding(
        experiment_name=binding.experiment_name,
        source_analysis_hash=binding.source_analysis_hash,
        report_dependency_fingerprint=binding.report_dependency_fingerprint,
        confirmatory_execution_manifest_hash=binding.confirmatory_execution_manifest_hash,
        source_scientific_cell_path=binding.source_scientific_cell_path,
        source_artifact_hashes=(),
    )
    with pytest.raises(ValueError):
        figure_table_has_single_source(empty)
