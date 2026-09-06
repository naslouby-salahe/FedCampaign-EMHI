from pathlib import Path

from fedcampaign_emhi.artifacts.storage import (
    build_artifact_layout,
    write_atomic_json,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import (
    ExperimentName,
)
from fedcampaign_emhi.domain.types import (
    ClientCount,
    SeedValue,
)
from fedcampaign_emhi.evaluation.metrics import (
    application_payload_bytes_per_epoch,
    registry_coalition_count,
    throughput,
)
from fedcampaign_emhi.evaluation.scalability import (
    ScalabilityMeasurement,
    collect_scalability_measurements,
    expected_scalability_coalitions,
    summarize_scalability,
)
from fedcampaign_emhi.experiments.technical_retry import with_technical_retry


def collect_scalability_seed_measurements(
    loaded: LoadedScientificConfiguration,
    client_count: ClientCount,
    seed: SeedValue,
) -> tuple[ScalabilityMeasurement, ...]:
    return with_technical_retry(
        loaded,
        lambda: collect_scalability_measurements(loaded, client_count, seed),
    )


def materialize_coalition_scalability_summaries(
    loaded: LoadedScientificConfiguration,
    repository: Path,
) -> tuple[Path, ...]:
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(ExperimentName.COALITION_SCALABILITY)
    staging = layout.roots.outputs_root / "cache" / "staging"
    config = loaded.values
    maximum_order = config.study.maximum_coalition_order
    maximum_latency = config.materiality.reference_harness.p95_latency_maximum_seconds
    maximum_failure_rate = config.materiality.maximum_pooled_numerical_failure_rate
    paths: list[Path] = []
    for client_count in config.robustness.scalability_client_counts:
        coalitions = expected_scalability_coalitions(config, client_count)
        registered = registry_coalition_count(client_count, maximum_order)
        if coalitions != registered:
            raise ValueError("derived coalition count must match the registry coalition count")
        payload_bytes = application_payload_bytes_per_epoch(client_count)
        seeds = config.randomness.real_development_roots + tuple(
            seed
            for seed in config.randomness.real_confirmatory_roots
            if seed not in config.randomness.real_development_roots
        )

        collected: list[ScalabilityMeasurement] = []
        for seed in seeds:
            collected.extend(collect_scalability_seed_measurements(loaded, client_count, seed))
        measurements = tuple(collected)
        summary = summarize_scalability(
            client_count,
            measurements,
            maximum_latency,
            maximum_failure_rate,
            config.scalability_timing.result_quantile,
        )
        scored_rate = None
        if summary.median_server_latency_seconds > 0.0:
            scored_rate = throughput(coalitions, summary.median_server_latency_seconds)
        payload: YamlNode = {
            "client_count": client_count,
            "expected_coalitions": coalitions,
            "application_payload_bytes_per_epoch": payload_bytes,
            "median_server_latency_seconds": summary.median_server_latency_seconds,
            "p95_server_latency_seconds": summary.p95_server_latency_seconds,
            "median_end_to_end_latency_seconds": summary.median_end_to_end_latency_seconds,
            "p95_end_to_end_latency_seconds": summary.p95_end_to_end_latency_seconds,
            "numerical_failure_rate": summary.numerical_failure_rate,
            "throughput": scored_rate,
            "local_timing_operating_point_available": (
                summary.local_timing_operating_point_available
            ),
            "global_timing_operating_point_available": (
                summary.global_timing_operating_point_available
            ),
            "latency_within_target": summary.latency_within_target,
            "numerical_failure_rate_within_bound": summary.numerical_failure_rate_within_bound,
            "artifact_fit_seconds": summary.artifact_fit_seconds,
            "state": summary.state.value,
        }
        path = root / "metrics" / "aggregate" / f"k-{client_count}.json"
        write_atomic_json(path, payload, staging)
        paths.append(path)
    return tuple(paths)
