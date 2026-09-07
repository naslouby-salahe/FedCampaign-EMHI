from pathlib import Path

from fedcampaign_emhi.artifacts.records import ReportSourceRecord
from fedcampaign_emhi.artifacts.storage import write_atomic_json
from fedcampaign_emhi.reporting.evidence import report_source_is_reusable
from fedcampaign_emhi.runtime import assess_implementation_readiness


def test_readiness_probe() -> None:
    readiness = assess_implementation_readiness()
    assert readiness.production_configuration_valid is True
    assert readiness.unspecified_scientific_choice_count == 0


def test_report_source_reuse_requires_matching_lineage(tmp_path: Path) -> None:
    source_path = tmp_path / "evidence-source.json"
    record = ReportSourceRecord(
        source_analysis_hash="a" * 64,
        report_dependency_fingerprint="b" * 64,
        source_scientific_cell_paths=("outputs/cell.json",),
        source_artifact_hashes=("c" * 64,),
    )
    write_atomic_json(source_path, record.model_dump(mode="json"), tmp_path / "staging")
    assert report_source_is_reusable(source_path, record)
    changed = record.model_copy(update={"source_artifact_hashes": ("d" * 64,)})
    assert not report_source_is_reusable(source_path, changed)
