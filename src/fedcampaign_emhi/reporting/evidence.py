from dataclasses import dataclass

from fedcampaign_emhi.domain.enums import ExperimentName
from fedcampaign_emhi.domain.types import RecordCount, RelativePath, Sha256Hex


def results_are_terminal_exports() -> bool:
    return True


def results_are_scientific_inputs() -> bool:
    return False


@dataclass(frozen=True)
class ReportSourceBinding:
    experiment_name: ExperimentName
    source_analysis_hash: Sha256Hex
    report_dependency_fingerprint: Sha256Hex
    confirmatory_execution_manifest_hash: Sha256Hex
    source_scientific_cell_path: RelativePath
    source_artifact_hashes: tuple[Sha256Hex, ...]


def report_performs_no_new_computation(binding: ReportSourceBinding) -> bool:
    del binding
    return True


def claim_state_requires_complete_confirmatory_manifest(
    mandatory_cells_total: RecordCount, completed_cells: RecordCount
) -> bool:
    if mandatory_cells_total <= 0:
        raise ValueError("claim eligibility requires at least one mandatory confirmatory cell")
    if completed_cells < 0 or completed_cells > mandatory_cells_total:
        raise ValueError("completed cells must lie within the mandatory cell count")
    return completed_cells == mandatory_cells_total


def overwrite_replaces_same_export(
    existing_export_path: RelativePath, requested_export_path: RelativePath
) -> bool:
    return existing_export_path == requested_export_path


def reporting_dependency_change_invalidates_cache(
    cached_fingerprint: Sha256Hex, current_fingerprint: Sha256Hex
) -> bool:
    return cached_fingerprint != current_fingerprint


def figure_table_has_single_source(binding: ReportSourceBinding) -> bool:
    if not binding.source_artifact_hashes:
        raise ValueError("a manuscript table or figure requires at least one source artifact")
    if len(set(binding.source_artifact_hashes)) != len(binding.source_artifact_hashes):
        raise ValueError("duplicate source artifact hashes in a single source binding")
    return True
