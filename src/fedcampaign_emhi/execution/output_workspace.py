from csv import writer
from io import BytesIO, StringIO
from pathlib import Path

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from fedcampaign_emhi.artifacts.records import ScientificCellRecord
from fedcampaign_emhi.artifacts.storage import (
    build_artifact_layout,
    file_sha256,
    write_atomic_bytes,
    write_atomic_json,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration, ReportingFigureConfig
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import (
    ArtifactPathSegment,
    ExperimentName,
    KnownArtifactOutputFilename,
    RunOutputColumn,
    RuntimeFigureLabel,
)
from fedcampaign_emhi.domain.types import ConfigurationDigest, DeterministicUtf8Bytes, FigureBytes
from fedcampaign_emhi.experiments.execution import cell_record_paths


def _table_bytes(cells: tuple[ScientificCellRecord, ...]) -> DeterministicUtf8Bytes:
    output = StringIO(newline="")
    rows = writer(output, lineterminator="\n")
    rows.writerow(
        (
            RunOutputColumn.ROLE,
            RunOutputColumn.SEED,
            RunOutputColumn.METHOD,
            RunOutputColumn.STATE,
            RunOutputColumn.RUNTIME_SECONDS,
            RunOutputColumn.PEAK_RSS_BYTES,
            RunOutputColumn.DIAGNOSTIC,
        )
    )
    for cell in cells:
        diagnostic = cell.completion_record.mandatory_output_paths[0]
        rows.writerow(
            (
                cell.execution_role.value,
                "" if cell.seed is None else cell.seed,
                "" if cell.method_name is None else cell.method_name.value,
                cell.state.value,
                cell.runtime_seconds,
                cell.peak_rss_bytes,
                diagnostic,
            )
        )
    return output.getvalue().encode("utf-8")


def _runtime_figure(
    cells: tuple[ScientificCellRecord, ...], figure_config: ReportingFigureConfig
) -> FigureBytes:
    figure = Figure(figsize=(figure_config.width_inches, figure_config.height_inches))
    FigureCanvasAgg(figure)
    axes = figure.add_subplot(1, 1, 1)
    positions = list(range(len(cells)))
    runtimes = [cell.runtime_seconds for cell in cells]
    labels = [
        f"{cell.execution_role.value[0]}:{'' if cell.seed is None else cell.seed}" for cell in cells
    ]
    axes.plot(positions, runtimes, "o", color="black", markersize=3)
    axes.set_xlabel(RuntimeFigureLabel.X_AXIS)
    axes.set_ylabel(RuntimeFigureLabel.Y_AXIS)
    axes.set_xticks(positions)
    axes.set_xticklabels(labels, rotation=70, fontsize=6)
    axes.set_title(RuntimeFigureLabel.TITLE)
    figure.tight_layout()
    output = BytesIO()
    figure.savefig(output, format="png", dpi=figure_config.dots_per_inch)
    return output.getvalue()


def materialize_run_output_workspace(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
) -> tuple[Path, ...]:
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    paths = cell_record_paths(root)
    cells = tuple(ScientificCellRecord.model_validate_json(path.read_bytes()) for path in paths)
    if not cells:
        raise ValueError(f"completed experiment {experiment_name.value} has no cell evidence")
    staging = layout.roots.outputs_root / ArtifactPathSegment.CACHE / ArtifactPathSegment.STAGING
    table_path = (
        root
        / ArtifactPathSegment.TABLES
        / ArtifactPathSegment.MAIN
        / KnownArtifactOutputFilename.CELL_EVIDENCE
    )
    figure_path = (
        root
        / ArtifactPathSegment.FIGURES
        / ArtifactPathSegment.MAIN
        / KnownArtifactOutputFilename.CELL_RUNTIME
    )
    table_hash = write_atomic_bytes(table_path, _table_bytes(cells), staging)
    figure_hash = write_atomic_bytes(
        figure_path, _runtime_figure(cells, loaded.values.reporting.figures), staging
    )
    sources: tuple[ConfigurationDigest, ...] = tuple(file_sha256(path) for path in paths)
    index_path = (
        root
        / ArtifactPathSegment.PROVENANCE
        / ArtifactPathSegment.ARTIFACTS
        / KnownArtifactOutputFilename.RUN_OUTPUT_INDEX
    )
    payload: YamlNode = {
        "experiment_name": experiment_name.value,
        "material_digest": loaded.material_digest,
        "cell_record_paths": [path.relative_to(repository).as_posix() for path in paths],
        "cell_record_hashes": list(sources),
        "table_path": table_path.relative_to(repository).as_posix(),
        "table_hash": table_hash,
        "figure_path": figure_path.relative_to(repository).as_posix(),
        "figure_hash": figure_hash,
    }
    write_atomic_json(index_path, payload, staging)
    return table_path, figure_path, index_path
