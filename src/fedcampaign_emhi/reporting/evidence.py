from dataclasses import dataclass
from pathlib import Path

from fedcampaign_emhi.artifacts.boundaries import (
    evidence_export_boundary_digest,
    statistical_analysis_boundary_digest,
)
from fedcampaign_emhi.artifacts.paths import build_artifact_layout
from fedcampaign_emhi.artifacts.provenance import content_digest, material_fingerprint
from fedcampaign_emhi.artifacts.records import (
    ExperimentRunRecord,
    PrimaryHolmFamilyRecord,
    ReportSourceRecord,
    ScientificCellRecord,
    StatisticalRecord,
)
from fedcampaign_emhi.artifacts.storage import file_sha256, payload_digest, write_atomic_json
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import (
    ExperimentName,
    ExperimentState,
    OverwritePolicy,
    PrimaryHolmHypothesis,
)
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


PRIMARY_HOLM_STATISTICS = (
    (
        ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION,
        PrimaryHolmHypothesis.SELF_EXPLANATION_MATERIAL_ATTENUATION,
    ),
    (
        ExperimentName.PURE_ORDER_SEPARATION_VALIDATION,
        PrimaryHolmHypothesis.PURE_ORDER_TARGET_DRIFT,
    ),
    (
        ExperimentName.PRIMARY_STRICT_ODI_EVALUATION,
        PrimaryHolmHypothesis.PRIMARY_ODI_ADVANTAGE_OVER_ORDER_AT_MOST_TWO_EMHI,
    ),
    (
        ExperimentName.BENIGN_COMMON_MODE_ROBUSTNESS,
        PrimaryHolmHypothesis.COMMON_MODE_FALSE_CAMPAIGN_REDUCTION,
    ),
    (
        ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE,
        PrimaryHolmHypothesis.STRONG_LOCAL_ODI_ABOVE_MINIMUM,
    ),
)


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


def _validate_statistical_records(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    statistical_paths: tuple[Path, ...],
) -> None:
    for statistical_path in statistical_paths:
        record = StatisticalRecord.model_validate_json(statistical_path.read_bytes())
        source_paths = tuple(repository / source_id for source_id in record.source_result_ids)
        if not source_paths:
            raise ValueError(f"statistical record {statistical_path} has no source results")
        if any(not source_path.is_file() for source_path in source_paths):
            raise ValueError(f"statistical record {statistical_path} has missing source results")
        source_digests = tuple(file_sha256(source_path) for source_path in source_paths)
        expected_fingerprint = material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values), source_digests
        )
        if record.dependency_fingerprint != expected_fingerprint:
            raise ValueError(f"statistical record {statistical_path} has stale source lineage")


def required_primary_holm_statistics(
    loaded: LoadedScientificConfiguration, repository: Path
) -> tuple[Path, ...]:
    paths: list[Path] = []
    for experiment_name, hypothesis in PRIMARY_HOLM_STATISTICS:
        evidence = select_verified_evidence(loaded, repository, experiment_name)
        matching = tuple(
            path
            for path in evidence.statistical_record_paths
            if StatisticalRecord.model_validate_json(path.read_bytes()).hypothesis_identifier
            == hypothesis.value
        )
        if len(matching) != 1:
            raise FileNotFoundError(
                "project summary is missing the required primary Holm statistical artifact "
                f"{hypothesis.value!r} from {experiment_name.value}"
            )
        paths.append(matching[0])
    return tuple(paths)


def _verified_primary_holm_family(
    loaded: LoadedScientificConfiguration, repository: Path, paths: tuple[Path, ...]
) -> PrimaryHolmFamilyRecord:
    layout = build_artifact_layout(loaded, repository)
    path = (
        layout.roots.results_root
        / "project_summary"
        / "statistics"
        / "multiplicity"
        / "primary-holm.json"
    )
    if not path.is_file():
        raise FileNotFoundError(
            "project summary requires the verified primary Holm analysis artifact"
        )
    record = PrimaryHolmFamilyRecord.model_validate_json(path.read_bytes())
    if record.material_digest != loaded.material_digest:
        raise ValueError("primary Holm analysis artifact is stale")
    expected_paths = tuple(source.relative_to(repository).as_posix() for source in paths)
    expected_hashes = tuple(file_sha256(source) for source in paths)
    if (
        record.source_statistical_paths != expected_paths
        or record.source_artifact_hashes != expected_hashes
    ):
        raise ValueError("primary Holm analysis artifact has stale source lineage")
    payload: YamlNode = {
        "material_digest": record.material_digest,
        "results": [result.model_dump(mode="json") for result in record.results],
        "source_statistical_paths": list(record.source_statistical_paths),
        "source_artifact_hashes": list(record.source_artifact_hashes),
    }
    if record.content_digest != payload_digest(payload):
        raise ValueError("primary Holm analysis artifact has an invalid content digest")
    return record


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
    _validate_statistical_records(loaded, repository, statistical_paths)
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
    dependency_fingerprint = material_fingerprint(
        evidence_export_boundary_digest(loaded.values), evidence.source_hashes
    )
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
    primary_paths = required_primary_holm_statistics(loaded, repository)
    _verified_primary_holm_family(loaded, repository, primary_paths)
    completed = _completed_experiments(loaded, repository)
    reports = tuple(
        materialize_verified_experiment_report(
            loaded, repository, completed_experiment, overwrite_policy
        )
        for completed_experiment in completed
    )
    export_reproducibility(loaded, repository, completed)
    return reports
