import csv
import os
import platform
import sys
from io import BytesIO, StringIO
from pathlib import Path
from typing import cast

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from fedcampaign_emhi.artifacts.records import (
    DropoutBoundaryConditionRecord,
    DropoutBoundaryDiagnosticRecord,
    SeedSummaryRecord,
)
from fedcampaign_emhi.artifacts.storage import (
    build_artifact_layout,
    dataset_directory_stem,
    file_sha256,
    write_atomic_json,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import (
    ArtifactFilenamePattern,
    ArtifactPathSegment,
    DatasetName,
    ExperimentName,
    KnownArtifactOutputFilename,
    PreprocessingLayer,
    RepositoryFileName,
)
from fedcampaign_emhi.domain.types import DeterministicUtf8Bytes, FigureBytes, MetricValue
from fedcampaign_emhi.experiments.registry import enumerate_experiment_plan
from fedcampaign_emhi.runtime import log_stage


def load_seed_summaries(paths: tuple[Path, ...]) -> tuple[SeedSummaryRecord, ...]:
    return tuple(SeedSummaryRecord.model_validate_json(path.read_bytes()) for path in paths)


def seed_summary_csv(records: tuple[SeedSummaryRecord, ...]) -> DeterministicUtf8Bytes:
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        (
            "experiment",
            "execution_role",
            "method",
            "reference_method",
            "metric",
            "seed",
            "method_value",
            "reference_value",
            "paired_difference",
            "campaign_count",
        )
    )
    for record in records:
        writer.writerow(
            (
                record.experiment_name.value,
                record.execution_role.value,
                record.method_name.value,
                "" if record.reference_method_name is None else record.reference_method_name.value,
                record.metric_name,
                record.seed,
                record.method_value,
                "" if record.reference_value is None else record.reference_value,
                "" if record.paired_difference is None else record.paired_difference,
                record.campaign_count,
            )
        )
    return output.getvalue().encode("utf-8")


def write_csv_artifact(destination: Path, content: DeterministicUtf8Bytes) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_suffix(destination.suffix + ".partial")
    staging.write_bytes(content)
    staging.replace(destination)


def write_png_artifact(destination: Path, content: FigureBytes) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_suffix(destination.suffix + ".partial")
    staging.write_bytes(content)
    staging.replace(destination)


def write_seed_summary_table(destination: Path, records: tuple[SeedSummaryRecord, ...]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_suffix(destination.suffix + ".partial")
    staging.write_bytes(seed_summary_csv(records))
    staging.replace(destination)


def paired_difference_figure_bytes(paired_differences: tuple[MetricValue, ...]) -> FigureBytes:
    if not paired_differences:
        raise ValueError("paired-difference figure requires paired seed summaries")
    figure = Figure(figsize=(6, 3))
    FigureCanvasAgg(figure)
    axes = figure.add_subplot(1, 1, 1)
    axes.scatter(range(len(paired_differences)), paired_differences, s=24, facecolor="black")
    axes.axhline(0.0, color="black", linewidth=1)
    axes.set_xlabel("seed index")
    axes.set_ylabel("paired difference")
    figure.tight_layout()
    output = BytesIO()
    figure.savefig(output, format="png")
    return output.getvalue()


def write_paired_difference_figure(
    destination: Path, records: tuple[SeedSummaryRecord, ...]
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_suffix(destination.suffix + ".partial")
    paired_differences = tuple(
        float(record.paired_difference)
        for record in records
        if record.paired_difference is not None
    )
    staging.write_bytes(paired_difference_figure_bytes(paired_differences))
    staging.replace(destination)


def load_dropout_boundary_conditions(
    paths: tuple[Path, ...],
) -> tuple[DropoutBoundaryConditionRecord, ...]:
    diagnostics = tuple(
        DropoutBoundaryDiagnosticRecord.model_validate_json(path.read_bytes()) for path in paths
    )
    return tuple(
        condition
        for diagnostic in diagnostics
        for condition in diagnostic.evidence.dropout_conditions
    )


def dropout_boundary_csv(
    records: tuple[DropoutBoundaryConditionRecord, ...],
) -> DeterministicUtf8Bytes:
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        (
            "client_count",
            "unavailable_fraction",
            "context_coverage",
            "abstention_rate",
            "standardized_null_bias",
            "detection_rate",
            "latency_seconds",
            "null_pfa",
            "operating_point_available",
        )
    )
    for record in records:
        writer.writerow(
            (
                record.client_count,
                record.unavailable_fraction,
                record.context_coverage,
                record.abstention_rate,
                record.standardized_null_bias,
                record.detection_rate,
                record.latency_seconds,
                record.null_pfa,
                record.operating_point_available,
            )
        )
    return output.getvalue().encode("utf-8")


def write_dropout_boundary_table(
    destination: Path, records: tuple[DropoutBoundaryConditionRecord, ...]
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_suffix(destination.suffix + ".partial")
    staging.write_bytes(dropout_boundary_csv(records))
    staging.replace(destination)


def dropout_boundary_figure_bytes(
    records: tuple[DropoutBoundaryConditionRecord, ...],
) -> FigureBytes:
    if not records:
        raise ValueError("dropout boundary figure requires condition records")
    figure = Figure(figsize=(8, 2.0))
    FigureCanvasAgg(figure)
    axes = figure.subplots(1, 3, sharex=True)
    metrics = (
        ("context_coverage", "Context coverage"),
        ("detection_rate", "Campaign detection rate"),
        ("abstention_rate", "Abstention rate"),
    )
    client_counts = tuple(sorted({record.client_count for record in records}))
    fractions = tuple(sorted({record.unavailable_fraction for record in records}))
    for axis, (attribute, label) in zip(axes, metrics, strict=True):
        for client_count in client_counts:
            means: list[MetricValue] = []
            errors: list[MetricValue] = []
            for fraction in fractions:
                values = np.asarray(
                    [
                        getattr(record, attribute)
                        for record in records
                        if record.client_count == client_count
                        and record.unavailable_fraction == fraction
                    ],
                    dtype=float,
                )
                means.append(float(values.mean()))
                errors.append(
                    float(values.std(ddof=1) / np.sqrt(values.size))
                ) if values.size > 1 else errors.append(0.0)
            axis.errorbar(
                fractions, means, yerr=errors, marker="o", capsize=3, label=f"K={client_count}"
            )
        axis.set_xlabel("Unavailable-client fraction")
        axis.set_ylabel(label)
        axis.set_ylim(0.0, 1.0)
        axis.grid(axis="y", alpha=0.5)
    axes[0].legend(title="Clients", fontsize=8)
    figure.tight_layout()
    output = BytesIO()
    figure.savefig(output, format="png", dpi=180)
    return output.getvalue()


def write_dropout_boundary_figure(
    destination: Path, records: tuple[DropoutBoundaryConditionRecord, ...]
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_suffix(destination.suffix + ".partial")
    staging.write_bytes(dropout_boundary_figure_bytes(records))
    staging.replace(destination)


@log_stage("reporting.export")
def export_reproducibility(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    completed_experiments: tuple[ExperimentName, ...],
) -> tuple[Path, ...]:
    layout = build_artifact_layout(loaded, repository)
    root = (
        layout.roots.results_root
        / ArtifactPathSegment.PROJECT_SUMMARY
        / ArtifactPathSegment.REPRODUCIBILITY
    )
    staging = layout.roots.outputs_root / ArtifactPathSegment.CACHE / ArtifactPathSegment.STAGING
    configuration_path = (
        root
        / ArtifactPathSegment.CONFIGURATION
        / KnownArtifactOutputFilename.SCIENTIFIC_CONFIGURATION
    )
    dataset_path = (
        root / ArtifactPathSegment.DATASETS / KnownArtifactOutputFilename.DATASET_CONFIGURATION
    )
    seed_path = root / ArtifactPathSegment.SEEDS / KnownArtifactOutputFilename.SEED_CONFIGURATION
    software_path = (
        root / ArtifactPathSegment.SOFTWARE / KnownArtifactOutputFilename.SOFTWARE_IDENTITY
    )
    execution_path = (
        root / ArtifactPathSegment.EXECUTION / KnownArtifactOutputFilename.COMPLETED_EXPERIMENTS
    )
    write_atomic_json(
        configuration_path,
        cast(YamlNode, loaded.values.model_dump(mode="json")),
        staging,
    )
    write_atomic_json(
        dataset_path,
        cast(YamlNode, loaded.values.datasets.model_dump(mode="json")),
        staging,
    )
    write_atomic_json(
        seed_path,
        cast(YamlNode, loaded.values.randomness.model_dump(mode="json")),
        staging,
    )
    lock_path = repository / RepositoryFileName.LOCKFILE
    software_payload: YamlNode = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "uv_lock_sha256": file_sha256(lock_path) if lock_path.is_file() else None,
    }
    write_atomic_json(software_path, software_payload, staging)
    execution_payload: YamlNode = {
        "material_configuration_digest": loaded.material_digest,
        "completed_experiments": [experiment.value for experiment in completed_experiments],
    }
    write_atomic_json(execution_path, execution_payload, staging)
    environment_path = (
        root / ArtifactPathSegment.EXECUTION / KnownArtifactOutputFilename.ENVIRONMENT_IDENTITY
    )
    environment_payload: YamlNode = {
        "operating_system": platform.system(),
        "machine_architecture": platform.machine(),
        "python_version": sys.version.split()[0],
        "logical_core_count": os.cpu_count(),
        "material_configuration_digest": loaded.material_digest,
    }
    write_atomic_json(environment_path, environment_payload, staging)
    plan_payload: YamlNode = {
        "material_configuration_digest": loaded.material_digest,
        "planned_experiments": [
            {
                "experiment_name": experiment.value,
                "execution_role": role.value,
                "seed_count": seed_count,
            }
            for experiment, role, seed_count in enumerate_experiment_plan(loaded.values)
        ],
    }
    plan_path = root / ArtifactPathSegment.EXECUTION / KnownArtifactOutputFilename.PLAN_SNAPSHOT
    write_atomic_json(plan_path, plan_payload, staging)
    completion_path = (
        root
        / ArtifactPathSegment.EXECUTION
        / KnownArtifactOutputFilename.EXPERIMENT_COMPLETION_METADATA
    )
    completion_payload: YamlNode = {
        "material_configuration_digest": loaded.material_digest,
        "experiments": [
            {
                "experiment_name": experiment.value,
                "run_record_digest": file_sha256(
                    layout.experiment_outputs_root(experiment)
                    / ArtifactPathSegment.PROVENANCE
                    / ArtifactPathSegment.DEPENDENCIES
                    / KnownArtifactOutputFilename.RUN_RECORD
                ),
            }
            for experiment in completed_experiments
        ],
    }
    write_atomic_json(completion_path, completion_payload, staging)
    dataset_identity_path = (
        root / ArtifactPathSegment.DATASETS / KnownArtifactOutputFilename.PREPROCESSING_IDENTITY
    )
    preprocessing_root = layout.roots.outputs_root / ArtifactPathSegment.PREPROCESSING
    dataset_payload: YamlNode = {
        "datasets": [
            {
                "dataset_name": dataset.value,
                "layers": [
                    {
                        "layer": layer.value,
                        "relative_path": artifact_path.relative_to(repository).as_posix(),
                        "sha256": file_sha256(artifact_path),
                    }
                    for layer, artifact_path in _preprocessing_layer_paths(
                        preprocessing_root, dataset
                    )
                    if artifact_path.is_file()
                ],
            }
            for dataset in (DatasetName.TON_IOT_NETWORK, DatasetName.EDGE_IIOTSET)
        ]
    }
    write_atomic_json(dataset_identity_path, dataset_payload, staging)
    return (
        configuration_path,
        dataset_path,
        seed_path,
        software_path,
        execution_path,
        environment_path,
        plan_path,
        completion_path,
        dataset_identity_path,
    )


def _preprocessing_layer_paths(
    preprocessing_root: Path, dataset_name: DatasetName
) -> tuple[tuple[PreprocessingLayer, Path], ...]:
    stem = dataset_directory_stem(dataset_name)
    return (
        (
            PreprocessingLayer.INVENTORY,
            preprocessing_root / ArtifactPathSegment.INVENTORIES / f"{stem}.json",
        ),
        (
            PreprocessingLayer.PREPARED,
            preprocessing_root / ArtifactPathSegment.PREPARED / f"{stem}.json",
        ),
        (
            PreprocessingLayer.SPLITS,
            preprocessing_root / ArtifactPathSegment.SPLITS / f"{stem}.json",
        ),
        (
            PreprocessingLayer.PARTITIONS,
            preprocessing_root
            / ArtifactPathSegment.METADATA
            / ArtifactFilenamePattern.BENIGN_PARTITIONS.format(dataset=stem),
        ),
        (
            PreprocessingLayer.CAMPAIGN_REGISTRY,
            preprocessing_root
            / ArtifactPathSegment.METADATA
            / ArtifactFilenamePattern.CAMPAIGN_REGISTRY.format(dataset=stem),
        ),
    )
