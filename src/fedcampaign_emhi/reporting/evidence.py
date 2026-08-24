from dataclasses import dataclass
from pathlib import Path

from fedcampaign_emhi.artifacts.paths import build_artifact_layout
from fedcampaign_emhi.artifacts.provenance import content_digest, material_fingerprint
from fedcampaign_emhi.artifacts.records import (
    ExperimentRunRecord,
    ReportSourceRecord,
    ScientificCellRecord,
)
from fedcampaign_emhi.artifacts.storage import file_sha256, write_atomic_json
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import ExperimentName, ExperimentState, OverwritePolicy
from fedcampaign_emhi.domain.types import ConfigurationDigest
from fedcampaign_emhi.reporting.figures import write_paired_difference_figure
from fedcampaign_emhi.reporting.reproducibility import export_reproducibility
from fedcampaign_emhi.reporting.tables import load_seed_summaries, write_seed_summary_table


@dataclass(frozen=True)
class VerifiedExperimentEvidence:
    run_record: ExperimentRunRecord
    seed_summary_paths: tuple[Path, ...]
    statistical_record_paths: tuple[Path, ...]
    scientific_cell_paths: tuple[Path, ...]
    source_hashes: tuple[ConfigurationDigest, ...]


@dataclass(frozen=True)
class ReportMaterialization:
    experiment_name: ExperimentName
    output_paths: tuple[Path, ...]


def _json_files(root: Path) -> tuple[Path, ...]:
    if not root.is_dir():
        return ()
    return tuple(sorted(path for path in root.rglob("*.json") if path.is_file()))


def _completed_experiments(
    loaded: LoadedScientificConfiguration, repository: Path
) -> tuple[ExperimentName, ...]:
    layout = build_artifact_layout(loaded, repository)
    completed: list[ExperimentName] = []
    for experiment_name in ExperimentName:
        run_record_path = (
            layout.experiment_outputs_root(experiment_name)
            / "provenance"
            / "dependencies"
            / "run-record.json"
        )
        if not run_record_path.is_file():
            continue
        try:
            run_record = ExperimentRunRecord.model_validate_json(run_record_path.read_bytes())
        except ValueError:
            continue
        if (
            run_record.state is ExperimentState.COMPLETED
            and run_record.material_digest == loaded.material_digest
        ):
            completed.append(experiment_name)
    return tuple(completed)


def select_verified_evidence(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
) -> VerifiedExperimentEvidence:
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    run_record_path = root / "provenance" / "dependencies" / "run-record.json"
    if not run_record_path.is_file():
        raise FileNotFoundError(f"missing run record for {experiment_name.value}")
    run_record = ExperimentRunRecord.model_validate_json(run_record_path.read_bytes())
    if run_record.state is not ExperimentState.COMPLETED:
        raise ValueError(f"experiment {experiment_name.value} is not completed")
    if run_record.material_digest != loaded.material_digest:
        raise ValueError(
            f"experiment {experiment_name.value} is stale for the active configuration"
        )
    seed_paths = tuple(
        sorted(
            {
                *(_json_files(root / "metrics" / "per_seed")),
                *(_json_files(root / "metrics" / "seed-summaries")),
            }
        )
    )
    statistical_paths = _json_files(root / "statistics")
    cell_paths = tuple(
        path
        for path in _json_files(root / "provenance" / "dependencies")
        if path.name != "run-record.json"
    )
    required = seed_paths + statistical_paths + cell_paths
    if not cell_paths:
        raise ValueError(f"experiment {experiment_name.value} lacks scientific cell records")
    for cell_path in cell_paths:
        cell = ScientificCellRecord.model_validate_json(cell_path.read_bytes())
        if cell.material_digest != loaded.material_digest:
            raise ValueError(f"scientific cell {cell_path} is stale")
        if cell.state is not ExperimentState.COMPLETED:
            raise ValueError(f"scientific cell {cell_path} is not completed")
        if len(cell.completion_record.mandatory_output_paths) != len(
            cell.completion_record.mandatory_output_hashes
        ):
            raise ValueError(f"scientific cell {cell_path} has incomplete output hashes")
        for relative_path, expected_hash in zip(
            cell.completion_record.mandatory_output_paths,
            cell.completion_record.mandatory_output_hashes,
            strict=True,
        ):
            output_path = repository / relative_path
            if not output_path.is_file() or file_sha256(output_path) != expected_hash:
                raise ValueError(f"scientific cell {cell_path} has unverifiable outputs")
    return VerifiedExperimentEvidence(
        run_record=run_record,
        seed_summary_paths=seed_paths,
        statistical_record_paths=statistical_paths,
        scientific_cell_paths=cell_paths,
        source_hashes=tuple(file_sha256(path) for path in required),
    )


def materialize_verified_experiment_report(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    overwrite_policy: OverwritePolicy,
) -> ReportMaterialization:
    evidence = select_verified_evidence(loaded, repository, experiment_name)
    layout = build_artifact_layout(loaded, repository)
    result_root = layout.experiment_results_root(experiment_name)
    source_path = result_root / "source_data" / "tables" / "evidence-source.json"
    output_paths: list[Path] = []
    if evidence.seed_summary_paths:
        table_path = result_root / "tables" / "main" / "seed-summary.csv"
        figure_path = result_root / "figures" / "main" / "paired-differences.svg"
        summaries = load_seed_summaries(evidence.seed_summary_paths)
        if overwrite_policy is OverwritePolicy.OVERWRITE or not table_path.is_file():
            write_seed_summary_table(table_path, summaries)
        output_paths.append(table_path)
        paired = tuple(summary for summary in summaries if summary.paired_difference is not None)
        if paired:
            if overwrite_policy is OverwritePolicy.OVERWRITE or not figure_path.is_file():
                write_paired_difference_figure(figure_path, paired)
            output_paths.append(figure_path)
    analysis_hash = content_digest({"source_hashes": list(evidence.source_hashes)})
    dependency_fingerprint = material_fingerprint(loaded.material_digest, evidence.source_hashes)
    source_record = ReportSourceRecord(
        source_analysis_hash=analysis_hash,
        report_dependency_fingerprint=dependency_fingerprint,
        source_scientific_cell_paths=tuple(
            str(path.relative_to(repository)) for path in evidence.scientific_cell_paths
        ),
        source_artifact_hashes=evidence.source_hashes,
    )
    staging = layout.roots.outputs_root / "cache" / "staging"
    if overwrite_policy is OverwritePolicy.OVERWRITE or not source_path.is_file():
        write_atomic_json(source_path, source_record.model_dump(mode="json"), staging)
    output_paths.append(source_path)
    return ReportMaterialization(experiment_name=experiment_name, output_paths=tuple(output_paths))


def materialize_report_scope(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName | None,
    overwrite_policy: OverwritePolicy,
) -> tuple[ReportMaterialization, ...]:
    if experiment_name is not None:
        return (
            materialize_verified_experiment_report(
                loaded, repository, experiment_name, overwrite_policy
            ),
        )
    completed = _completed_experiments(loaded, repository)
    reports = tuple(
        materialize_verified_experiment_report(
            loaded, repository, completed_experiment, overwrite_policy
        )
        for completed_experiment in completed
    )
    export_reproducibility(loaded, repository, completed)
    return reports
