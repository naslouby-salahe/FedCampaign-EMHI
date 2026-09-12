import csv
from io import BytesIO, StringIO
from pathlib import Path

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from fedcampaign_emhi.artifacts.records import (
    ContextEstimatorSensitivityCellRecord,
    ContextEstimatorSensitivityMetrics,
    ScalabilityAggregateRecord,
    ScientificCellRecord,
    SeedSummaryRecord,
    StrongComparatorCompositionRecord,
)
from fedcampaign_emhi.artifacts.storage import payload_digest
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import (
    ArtifactPathSegment,
    ExperimentName,
    KnownArtifactOutputFilename,
    MethodName,
)
from fedcampaign_emhi.domain.types import (
    Boolean,
    ComponentName,
    DeterministicUtf8Bytes,
    FigureBytes,
    MetricRate,
    MetricValue,
    RelativePath,
    SeedValue,
)
from fedcampaign_emhi.experiments.seed_evaluation import sensitivity_cell_slug
from fedcampaign_emhi.reporting.export import write_csv_artifact, write_png_artifact


def selection_record_is_current(record: StrongComparatorCompositionRecord) -> Boolean:
    payload: YamlNode = {
        "selected_method": record.selected_method.value,
        "selected_native_order": record.selected_native_order,
        "eligible_candidates": [candidate.value for candidate in record.eligible_candidates],
        "candidate_native_orders": [
            item.model_dump(mode="json") for item in record.candidate_native_orders
        ],
        "null_pfa_results": [item.model_dump(mode="json") for item in record.null_pfa_results],
        "target_error_results": [
            item.model_dump(mode="json") for item in record.target_error_results
        ],
        "runtime_tiebreak_results": [
            item.model_dump(mode="json") for item in record.runtime_tiebreak_results
        ],
        "selection_rule_hash": record.selection_rule_hash,
        "source_artifact_hashes": list(record.source_artifact_hashes),
    }
    return payload_digest(payload) == record.content_digest


def load_verified_selection_record(path: Path) -> StrongComparatorCompositionRecord:
    if not path.is_file():
        raise FileNotFoundError("missing strong comparator composition selection artifact")
    try:
        record = StrongComparatorCompositionRecord.model_validate_json(path.read_bytes())
    except ValueError as error:
        raise ValueError("malformed strong comparator composition selection artifact") from error
    if not selection_record_is_current(record):
        raise ValueError(
            "strong comparator composition selection artifact has an invalid content digest"
        )
    return record


def _csv_writer(output: StringIO):
    return csv.writer(output, lineterminator="\n")


def _blank(candidate_value: YamlNode | None) -> YamlNode:
    return "" if candidate_value is None else candidate_value


def composition_table_bytes(
    record: StrongComparatorCompositionRecord,
) -> DeterministicUtf8Bytes:
    output = StringIO(newline="")
    writer = _csv_writer(output)
    writer.writerow(
        (
            "candidate",
            "native_target_order",
            "mean_standardized_error",
            "heldout_false_stops",
            "heldout_horizons",
            "heldout_upper_pfa",
            "median_runtime_seconds",
            "eligible",
            "selected",
        )
    )
    pfa = {item.method_name: item for item in record.null_pfa_results}
    runtime = {item.method_name: item for item in record.runtime_tiebreak_results}
    for item in record.target_error_results:
        pfa_record = pfa.get(item.method_name)
        runtime_record = runtime.get(item.method_name)
        writer.writerow(
            (
                item.method_name.value,
                int(item.native_target_order),
                item.mean_standardized_error,
                _blank(None if pfa_record is None else pfa_record.heldout_false_stops),
                _blank(None if pfa_record is None else pfa_record.heldout_horizons),
                _blank(None if pfa_record is None else pfa_record.heldout_upper_pfa),
                _blank(None if runtime_record is None else runtime_record.median_runtime_seconds),
                "yes" if item.method_name in record.eligible_candidates else "no",
                "selected" if item.method_name is record.selected_method else "",
            )
        )
    return output.getvalue().encode("utf-8")


def composition_figure_bytes(record: StrongComparatorCompositionRecord) -> FigureBytes:
    figure = Figure(figsize=(8, 4))
    FigureCanvasAgg(figure)
    axes = figure.add_subplot(1, 1, 1)
    order = tuple(item.method_name for item in record.target_error_results)
    errors = tuple(item.mean_standardized_error for item in record.target_error_results)
    positions = list(range(len(order)))
    axes.bar(
        positions,
        list(errors),
        color="0.7",
        edgecolor="black",
        linewidth=1.0,
    )
    for index, method in enumerate(order):
        if method is record.selected_method:
            axes.patches[index].set_edgecolor("black")
            axes.patches[index].set_linewidth(2)
    axes.set_xticks(positions)
    axes.set_xticklabels([method.value for method in order], rotation=18, ha="right")
    axes.set_ylabel("mean standardized target-order error")
    figure.tight_layout()
    return _figure_bytes(figure)


def _figure_bytes(figure: Figure) -> FigureBytes:
    output = BytesIO()
    figure.savefig(output, format="png", dpi=180)
    return output.getvalue()


def seed_odi_csv_bytes(summaries: tuple[SeedSummaryRecord, ...]) -> DeterministicUtf8Bytes:
    output = StringIO(newline="")
    writer = _csv_writer(output)
    writer.writerow(
        (
            "experiment",
            "execution_role",
            "method",
            "seed",
            "strict_odi_rate",
            "campaign_count",
        )
    )
    ordered = tuple(sorted(summaries, key=lambda item: (int(item.seed), item.execution_role.value)))
    for summary in ordered:
        writer.writerow(
            (
                summary.experiment_name.value,
                summary.execution_role.value,
                summary.method_name.value,
                summary.seed,
                summary.method_value,
                summary.campaign_count,
            )
        )
    return output.getvalue().encode("utf-8")


def scalability_aggregate_csv_bytes(
    records: tuple[ScalabilityAggregateRecord, ...],
) -> DeterministicUtf8Bytes:
    output = StringIO(newline="")
    writer = _csv_writer(output)
    writer.writerow(
        (
            "client_count",
            "p95_server_latency_seconds",
            "p95_end_to_end_latency_seconds",
            "numerical_failure_rate",
            "numerical_failure_rate_within_bound",
            "latency_within_target",
            "local_timing_operating_point_available",
            "global_timing_operating_point_available",
            "state",
        )
    )
    ordered = tuple(sorted(records, key=lambda item: item.client_count))
    for record in ordered:
        writer.writerow(
            (
                record.client_count,
                record.p95_server_latency_seconds,
                record.p95_end_to_end_latency_seconds,
                record.numerical_failure_rate,
                record.numerical_failure_rate_within_bound,
                record.latency_within_target,
                record.local_timing_operating_point_available,
                record.global_timing_operating_point_available,
                record.state.value,
            )
        )
    return output.getvalue().encode("utf-8")


def seed_odi_figure_bytes(
    summaries: tuple[SeedSummaryRecord, ...],
    minimum_odi_rate: MetricRate,
) -> FigureBytes:
    figure = Figure(figsize=(6, 4))
    FigureCanvasAgg(figure)
    axes = figure.add_subplot(1, 1, 1)
    ordered = tuple(sorted(summaries, key=lambda item: (int(item.seed), item.execution_role.value)))
    axes.plot(
        range(len(ordered)),
        [summary.method_value for summary in ordered],
        "o",
        color="black",
        markersize=5,
    )
    axes.axhline(minimum_odi_rate, color="0.5", linewidth=1, linestyle="--")
    axes.set_xticks(range(len(ordered)))
    axes.set_xticklabels(
        [f"{summary.execution_role.value[0]}:{summary.seed}" for summary in ordered],
        rotation=45,
        fontsize=8,
    )
    axes.set_ylabel("strict ODI rate")
    axes.set_ylim(0, 1)
    figure.tight_layout()
    return _figure_bytes(figure)


def _variant_slug(record: ContextEstimatorSensitivityCellRecord) -> RelativePath:
    return sensitivity_cell_slug(
        record.basis_size_override,
        record.context_cell_count_override,
        record.forced_ridge_override,
        record.context_method_override,
    )


def _group_by_variant(
    records: tuple[ContextEstimatorSensitivityCellRecord, ...],
) -> tuple[tuple[RelativePath, tuple[ContextEstimatorSensitivityCellRecord, ...]], ...]:
    order: list[RelativePath] = []
    slots: list[list[ContextEstimatorSensitivityCellRecord]] = []
    for record in records:
        slug = _variant_slug(record)
        if slug not in order:
            order.append(slug)
            slots.append([])
        slots[order.index(slug)].append(record)
    return tuple((slug, tuple(slots[index])) for index, slug in enumerate(order))


def _deduplicate_seeds(
    records: tuple[ContextEstimatorSensitivityCellRecord, ...],
) -> tuple[ContextEstimatorSensitivityCellRecord, ...]:
    observed: list[SeedValue] = []
    unique: list[ContextEstimatorSensitivityCellRecord] = []
    for record in records:
        if record.seed not in observed:
            observed.append(record.seed)
            unique.append(record)
    return tuple(unique)


def sensitivity_table_bytes(
    records: tuple[ContextEstimatorSensitivityCellRecord, ...],
) -> DeterministicUtf8Bytes:
    output = StringIO(newline="")
    writer = _csv_writer(output)
    writer.writerow(
        (
            "variant",
            "seed_count",
            "strict_odi_rate",
            "campaign_detection_rate",
            "heldout_pfa",
            "operational_lead_mean",
            "context_coverage",
            "abstention_rate",
            "numerical_failure_rate",
        )
    )
    writer.writerow(_aggregate_metrics(_deduplicate_seeds(records), True, "base-full-emhi"))
    for slug, variant_records in _group_by_variant(records):
        writer.writerow(_aggregate_metrics(variant_records, False, slug))
    return output.getvalue().encode("utf-8")


def _metric_source(
    record: ContextEstimatorSensitivityCellRecord,
    use_base: Boolean,
) -> ContextEstimatorSensitivityMetrics:
    return record.base if use_base else record.condition


def _aggregate_metrics(
    records: tuple[ContextEstimatorSensitivityCellRecord, ...],
    use_base: Boolean,
    label: ComponentName,
) -> tuple[YamlNode, ...]:
    count = len(records)
    if count == 0:
        return (label, 0, "", "", "", "", "", "", "")
    metrics = tuple(_metric_source(record, use_base) for record in records)
    leads = tuple(
        metric.operational_lead_mean
        for metric in metrics
        if metric.operational_lead_mean is not None
    )
    present_pfa = tuple(metric.heldout_pfa for metric in metrics if metric.heldout_pfa is not None)
    return (
        label,
        count,
        _mean_values(tuple(metric.strict_odi_rate for metric in metrics)),
        _mean_values(tuple(metric.campaign_detection_rate for metric in metrics)),
        _blank(None if not present_pfa else _mean_values(tuple(value for value in present_pfa))),
        _blank(None if not leads else _mean_values(tuple(lead for lead in leads))),
        _mean_values(tuple(metric.context_coverage for metric in metrics)),
        _mean_values(tuple(metric.abstention_rate for metric in metrics)),
        _mean_values(tuple(metric.numerical_failure_rate for metric in metrics)),
    )


def _mean_values(values: tuple[MetricValue, ...]) -> MetricValue:
    return sum(values) / len(values)


def _panel_value(
    record: ContextEstimatorSensitivityCellRecord,
    attribute: ComponentName,
    use_base: Boolean,
) -> MetricValue:
    value = getattr(_metric_source(record, use_base), attribute)
    return 0.0 if value is None else value


def sensitivity_figure_bytes(
    records: tuple[ContextEstimatorSensitivityCellRecord, ...],
) -> FigureBytes:
    figure = Figure(figsize=(10, 4))
    FigureCanvasAgg(figure)
    panels = (
        ("strict_odi_rate", "Strict ODI rate"),
        ("campaign_detection_rate", "Campaign detection rate"),
        ("heldout_pfa", "Held-out PFA"),
        ("context_coverage", "Context coverage"),
    )
    axes = figure.subplots(1, 4)
    for axis, (name, label) in zip(axes, panels, strict=True):
        variants: list[tuple[RelativePath, MetricValue, MetricValue]] = []
        for slug, variant_records in _group_by_variant(records):
            values = tuple(_panel_value(record, name, False) for record in variant_records)
            mean = _mean_values(values)
            deviation = (sum((value - mean) ** 2 for value in values) / len(values)) ** 0.5
            variants.append((slug, mean, deviation / len(values) ** 0.5))
        axis.errorbar(
            [index for index in range(len(variants))],
            [entry[1] for entry in variants],
            yerr=[entry[2] for entry in variants],
            marker="o",
            capsize=3,
            color="black",
        )
        base_values = tuple(
            _panel_value(record, name, True) for record in _deduplicate_seeds(records)
        )
        axis.axhline(_mean_values(base_values), color="0.5", linewidth=1, linestyle="--")
        axis.set_xticks([index for index in range(len(variants))])
        axis.set_xticklabels([entry[0] for entry in variants], rotation=55, ha="right", fontsize=7)
        axis.set_ylim(0.0, 1.0)
        axis.set_title(label, fontsize=9)
    figure.suptitle("Context and estimator sensitivity (base full EMHI dashed)")
    figure.tight_layout()
    return _figure_bytes(figure)


def _results_root(repository: Path, experiment_name: ExperimentName) -> Path:
    return repository / "results" / ArtifactPathSegment.EXPERIMENTS / experiment_name.value


def _selection_artifact_path(loaded: LoadedScientificConfiguration, repository: Path) -> Path:
    return (
        repository
        / ArtifactPathSegment.OUTPUTS
        / ArtifactPathSegment.EXPERIMENTS
        / ExperimentName.STRONG_COMPARATOR_COMPOSITION_CHALLENGE.value
        / ArtifactPathSegment.ARTIFACTS
        / ArtifactPathSegment.DERIVED
        / loaded.values.experiments.strong_comparator_composition_challenge.artifact_filename
    )


def _sensitivity_records(
    repository: Path,
    cell_paths: tuple[Path, ...],
) -> tuple[ContextEstimatorSensitivityCellRecord, ...]:
    records: list[ContextEstimatorSensitivityCellRecord] = []
    for cell_path in cell_paths:
        try:
            cell = ScientificCellRecord.model_validate_json(cell_path.read_bytes())
        except ValueError:
            continue
        if cell.method_name is not None or not cell.completion_record.mandatory_output_paths:
            continue
        diagnostic = repository / cell.completion_record.mandatory_output_paths[0]
        records.append(
            ContextEstimatorSensitivityCellRecord.model_validate_json(diagnostic.read_bytes())
        )
    return tuple(records)


def materialize_experiment_exports(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    seed_summary_paths: tuple[Path, ...],
    cell_paths: tuple[Path, ...],
    aggregate_metric_paths: tuple[Path, ...],
    overwrite: Boolean,
) -> tuple[Path, ...]:
    if experiment_name is ExperimentName.STRONG_COMPARATOR_COMPOSITION_CHALLENGE:
        root = _results_root(repository, experiment_name)
        table_path = (
            root
            / ArtifactPathSegment.TABLES
            / ArtifactPathSegment.MAIN
            / KnownArtifactOutputFilename.COMPARATOR_COMPOSITION_TABLE
        )
        figure_path = (
            root
            / ArtifactPathSegment.FIGURES
            / ArtifactPathSegment.MAIN
            / KnownArtifactOutputFilename.COMPARATOR_COMPOSITION_FIGURE
        )
        record = load_verified_selection_record(_selection_artifact_path(loaded, repository))
        if overwrite or not table_path.is_file():
            write_csv_artifact(table_path, composition_table_bytes(record))
        if overwrite or not figure_path.is_file():
            write_png_artifact(figure_path, composition_figure_bytes(record))
        return table_path, figure_path
    if experiment_name is ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE:
        root = _results_root(repository, experiment_name)
        table_path = (
            root
            / ArtifactPathSegment.TABLES
            / ArtifactPathSegment.MAIN
            / KnownArtifactOutputFilename.STRONG_LOCAL_ODI_TABLE
        )
        figure_path = (
            root
            / ArtifactPathSegment.FIGURES
            / ArtifactPathSegment.MAIN
            / KnownArtifactOutputFilename.STRONG_LOCAL_ODI_FIGURE
        )
        summaries = tuple(
            SeedSummaryRecord.model_validate_json(path.read_bytes()) for path in seed_summary_paths
        )
        full_summaries = tuple(
            summary
            for summary in summaries
            if summary.method_name is MethodName.FULL_FEDCAMPAIGN_EMHI
        )
        minimum_odi_rate = loaded.values.materiality.strong_local.minimum_strict_odi_rate
        if overwrite or not table_path.is_file():
            write_csv_artifact(table_path, seed_odi_csv_bytes(full_summaries))
        if overwrite or not figure_path.is_file():
            write_png_artifact(figure_path, seed_odi_figure_bytes(full_summaries, minimum_odi_rate))
        return table_path, figure_path
    if experiment_name is ExperimentName.CONTEXT_AND_ESTIMATOR_SENSITIVITY:
        root = _results_root(repository, experiment_name)
        table_path = (
            root
            / ArtifactPathSegment.TABLES
            / ArtifactPathSegment.MAIN
            / KnownArtifactOutputFilename.SENSITIVITY_SUMMARY
        )
        figure_path = (
            root
            / ArtifactPathSegment.FIGURES
            / ArtifactPathSegment.MAIN
            / KnownArtifactOutputFilename.SENSITIVITY_DETECTION
        )
        records = _sensitivity_records(repository, cell_paths)
        if overwrite or not table_path.is_file():
            write_csv_artifact(table_path, sensitivity_table_bytes(records))
        if overwrite or not figure_path.is_file():
            write_png_artifact(figure_path, sensitivity_figure_bytes(records))
        return table_path, figure_path
    if experiment_name is ExperimentName.COALITION_SCALABILITY:
        root = _results_root(repository, experiment_name)
        table_path = (
            root
            / ArtifactPathSegment.TABLES
            / ArtifactPathSegment.MAIN
            / KnownArtifactOutputFilename.SCALABILITY_SUMMARY
        )
        aggregates = tuple(
            ScalabilityAggregateRecord.model_validate_json(path.read_bytes())
            for path in aggregate_metric_paths
        )
        if overwrite or not table_path.is_file():
            write_csv_artifact(table_path, scalability_aggregate_csv_bytes(aggregates))
        return (table_path,)
    return ()
