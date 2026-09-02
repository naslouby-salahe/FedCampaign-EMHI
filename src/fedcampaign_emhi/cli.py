from collections.abc import Callable

import typer

from fedcampaign_emhi.analysis.results import (
    materialize_primary_holm_family,
    materialize_secondary_holm_family,
)
from fedcampaign_emhi.artifacts.storage import build_artifact_layout
from fedcampaign_emhi.config.loading import (
    load_smoke_configuration,
    production_configuration_context,
    repository_root,
)
from fedcampaign_emhi.datasets.inventory import configured_raw_directory, discover_raw_paths
from fedcampaign_emhi.domain.enums import (
    DatasetName,
    ExperimentName,
    ExperimentState,
    OverwritePolicy,
    PreprocessingLayer,
)
from fedcampaign_emhi.domain.types import ArtifactIdentity, Boolean
from fedcampaign_emhi.execution.planning import (
    plan_experiments,
    resolve_requested_experiment,
)
from fedcampaign_emhi.execution.preprocessing import (
    execute_preprocess,
    preprocess_must_not_regenerate,
    requested_datasets,
)
from fedcampaign_emhi.execution.runner import execute_experiment, publish_plan_artifact
from fedcampaign_emhi.execution.status import project_status
from fedcampaign_emhi.experiments.registry import RESUME_SEQUENCE, assert_known_experiment
from fedcampaign_emhi.reporting.evidence import materialize_report_scope
from fedcampaign_emhi.runtime import assess_implementation_readiness

application = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    rich_markup_mode=None,
    context_settings={"max_content_width": 120},
)


def main() -> None:
    application()


def doctor_command() -> None:
    emit: Callable[[str], None] = typer.echo
    repository, loaded = production_configuration_context()
    readiness = assess_implementation_readiness(loaded, repository)
    layout = build_artifact_layout(loaded, repository)
    primary_raw = configured_raw_directory(loaded, DatasetName.TON_IOT_NETWORK, repository)
    secondary_raw = configured_raw_directory(loaded, DatasetName.EDGE_IIOTSET, repository)
    primary_files = discover_raw_paths(primary_raw)
    secondary_files = discover_raw_paths(secondary_raw)
    missing_directories = [path for path in layout.required_directories() if not path.exists()]
    raw_inventory_executable = primary_raw.exists() and secondary_raw.exists()
    emit(f"repository={repository}")
    emit(f"configuration={loaded.source_path}")
    emit(f"material_digest={readiness.material_digest}")
    emit(f"production_configuration_valid={readiness.production_configuration_valid}")
    emit(f"raw_inventory_executable={raw_inventory_executable}")
    emit(f"unspecified_scientific_choice_count={readiness.unspecified_scientific_choice_count}")
    emit(f"primary_raw_directory={primary_raw}")
    emit(f"primary_raw_file_count={len(primary_files)}")
    emit(f"secondary_raw_directory={secondary_raw}")
    emit(f"secondary_raw_file_count={len(secondary_files)}")
    emit(f"missing_artifact_directories={len(missing_directories)}")
    emit("next_action=fedcampaign preprocess")


_DATASET_ARGUMENT: DatasetName | None = typer.Argument(default=None)
_PREPROCESS_OVERWRITE_OPTION: Boolean = typer.Option(False, "--overwrite")


def preprocess_command(
    dataset_name: DatasetName | None = _DATASET_ARGUMENT,
    overwrite: Boolean = _PREPROCESS_OVERWRITE_OPTION,
) -> None:
    repository, loaded = production_configuration_context()
    selected = dataset_name
    policy = OverwritePolicy.OVERWRITE if overwrite else OverwritePolicy.REUSE_COMPATIBLE
    record = execute_preprocess(loaded, repository, selected, policy)
    typer.echo(f"material_digest={loaded.material_digest}")
    typer.echo(f"overwrite={overwrite}")
    typer.echo("datasets=" + ",".join(name.value for name in requested_datasets(selected)))
    for dataset, start_layer in record.reconstruct_from:
        origin = start_layer.value if start_layer is not None else "reuse_all"
        typer.echo(f"reconstruct_from.{dataset.value}={origin}")
    reused = tuple(decision.layer.value for decision in record.decisions if decision.reused)
    rebuilt = tuple(decision.layer.value for decision in record.decisions if decision.reconstructed)
    typer.echo("reused_layers=" + ",".join(reused))
    typer.echo("rebuilt_layers=" + ",".join(rebuilt))
    invalidated = tuple(
        artifact_id
        for decision in record.decisions
        for artifact_id in decision.invalidated_descendant_ids
    )
    unique_invalidated: list[ArtifactIdentity] = []
    for artifact_id in invalidated:
        if artifact_id not in unique_invalidated:
            unique_invalidated.append(artifact_id)
    typer.echo("invalidated_descendants=" + ",".join(unique_invalidated))
    typer.echo("ownership=" + ",".join(layer.value for layer in PreprocessingLayer))
    typer.echo(
        "must_not_regenerate=" + ",".join(kind.value for kind in preprocess_must_not_regenerate())
    )


def plan_command() -> None:
    repository, loaded = production_configuration_context()
    plan_path = publish_plan_artifact(loaded, repository)
    typer.echo(f"material_digest={loaded.material_digest}")
    typer.echo(f"plan_artifact={plan_path}")
    typer.echo("resume_sequence=" + " -> ".join(RESUME_SEQUENCE))
    for planned in plan_experiments(loaded):
        typer.echo(
            f"{planned.experiment_name.value}"
            f" role={planned.execution_role.value}"
            f" seeds={planned.seed_count}"
            f" state={planned.state.value}"
        )


_SMOKE_OVERWRITE_OPTION: Boolean = typer.Option(False, "--overwrite")


def smoke_command(
    overwrite: Boolean = _SMOKE_OVERWRITE_OPTION,
) -> None:
    repository = repository_root()
    loaded = load_smoke_configuration(repository)
    policy = OverwritePolicy.OVERWRITE if overwrite else OverwritePolicy.REUSE_COMPATIBLE
    result = execute_experiment(
        loaded,
        repository,
        ExperimentName.SYNTHETIC_MODULE_VALIDATION,
        policy,
    )
    typer.echo(f"experiment={ExperimentName.SYNTHETIC_MODULE_VALIDATION.value}")
    typer.echo(f"material_digest={loaded.material_digest}")
    typer.echo(f"overwrite={overwrite}")
    typer.echo(
        f"smoke_validation={'PASS' if result.state is ExperimentState.COMPLETED else 'FAIL'}"
    )
    typer.echo(f"state={result.state.value}")
    typer.echo(f"completed_cells={result.completed_cell_count}")
    typer.echo(f"detail={result.detail}")
    typer.echo("resume_sequence=" + " -> ".join(RESUME_SEQUENCE))
    typer.echo("must_not_invalidate=real-data scientific artifacts")
    if result.state is not ExperimentState.COMPLETED:
        raise typer.Exit(code=1)


_REQUESTED_EXPERIMENT_ARGUMENT: ExperimentName = typer.Argument()
_RUN_OVERWRITE_OPTION: Boolean = typer.Option(False, "--overwrite")
_DRY_RUN_OPTION: Boolean = typer.Option(False, "--dry-run")


def run_command(
    requested: ExperimentName = _REQUESTED_EXPERIMENT_ARGUMENT,
    overwrite: Boolean = _RUN_OVERWRITE_OPTION,
    dry_run: Boolean = _DRY_RUN_OPTION,
) -> None:
    repository, loaded = production_configuration_context()
    resolved = resolve_requested_experiment(requested.value)
    assert_known_experiment(loaded.values, resolved)
    if dry_run:
        typer.echo(f"experiment={resolved.value}")
        typer.echo(f"material_digest={loaded.material_digest}")
        typer.echo("scientific_configuration_overrides=rejected")
        typer.echo("dry_run=true")
        typer.echo("resume_sequence=" + " -> ".join(RESUME_SEQUENCE))
        return
    policy = OverwritePolicy.OVERWRITE if overwrite else OverwritePolicy.REUSE_COMPATIBLE
    result = execute_experiment(loaded, repository, resolved, policy)
    typer.echo(f"experiment={resolved.value}")
    typer.echo(f"material_digest={loaded.material_digest}")
    typer.echo(f"overwrite={overwrite}")
    typer.echo("scientific_configuration_overrides=rejected")
    typer.echo(f"run_record={result.run_record_path}")
    typer.echo(f"state={result.state.value}")
    typer.echo(f"completed_cells={result.completed_cell_count}")
    typer.echo(f"detail={result.detail}")
    typer.echo("resume_sequence=" + " -> ".join(RESUME_SEQUENCE))
    if result.state in {ExperimentState.FAILED, ExperimentState.INVALID}:
        raise typer.Exit(code=1)


_STATUS_EXPERIMENT_ARGUMENT: ExperimentName | None = typer.Argument(default=None)


def status_command(
    experiment_name: ExperimentName | None = _STATUS_EXPERIMENT_ARGUMENT,
) -> None:
    repository, loaded = production_configuration_context()
    typer.echo(f"material_digest={loaded.material_digest}")
    for item in project_status(loaded, repository):
        if experiment_name is not None and item.experiment_name is not experiment_name:
            continue
        typer.echo(
            f"{item.experiment_name.value}"
            f" state={item.state.value}"
            f" lifecycle={item.lifecycle_state.value}"
            f" development_seeds={item.development_seed_count}"
            f" confirmatory_seeds={item.confirmatory_seed_count}"
        )


_REPORT_EXPERIMENT_ARGUMENT: ExperimentName | None = typer.Argument(default=None)
_REPORT_OVERWRITE_OPTION: Boolean = typer.Option(False, "--overwrite")


def report_command(
    experiment_name: ExperimentName | None = _REPORT_EXPERIMENT_ARGUMENT,
    overwrite: Boolean = _REPORT_OVERWRITE_OPTION,
) -> None:
    repository, loaded = production_configuration_context()
    policy = OverwritePolicy.OVERWRITE if overwrite else OverwritePolicy.REUSE_COMPATIBLE
    reports = materialize_report_scope(loaded, repository, experiment_name, policy)
    if experiment_name is not None:
        typer.echo(f"experiment={experiment_name.value}")
    else:
        typer.echo("scope=project_summary")
    typer.echo(f"material_digest={loaded.material_digest}")
    typer.echo(f"overwrite={overwrite}")
    typer.echo(f"reported_experiments={len(reports)}")
    for report in reports:
        for path in report.output_paths:
            typer.echo(f"report_artifact={path}")


def analyze_command() -> None:
    repository, loaded = production_configuration_context()
    primary_holm_path = materialize_primary_holm_family(loaded, repository)
    secondary_holm_path = materialize_secondary_holm_family(loaded, repository)
    typer.echo(f"material_digest={loaded.material_digest}")
    typer.echo(f"primary_holm_artifact={primary_holm_path}")
    typer.echo(f"secondary_holm_artifact={secondary_holm_path}")


application.command("doctor")(doctor_command)
application.command("analyze")(analyze_command)
application.command("preprocess")(preprocess_command)
application.command("plan")(plan_command)
application.command("smoke")(smoke_command)
application.command("run")(run_command)
application.command("status")(status_command)
application.command("report")(report_command)


if __name__ == "__main__":
    main()
