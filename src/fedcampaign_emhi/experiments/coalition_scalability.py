import hashlib
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import cast

from fedcampaign_emhi.artifacts.provenance import material_fingerprint
from fedcampaign_emhi.artifacts.records import (
    CompletionRecord,
    ScalabilityAggregateRecord,
    ScalabilitySeedCacheRecord,
    ScientificCellRecord,
)
from fedcampaign_emhi.artifacts.storage import (
    build_artifact_layout,
    file_sha256,
    payload_digest,
    write_atomic_json,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration, ScientificConfig
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import (
    ExecutionRole,
    ExperimentName,
    ExperimentState,
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
    capture_timing_environment_identity,
    collect_scalability_measurements,
    expected_scalability_coalitions,
    summarize_scalability,
)
from fedcampaign_emhi.experiments.technical_retry import with_technical_retry
from fedcampaign_emhi.runtime import component_logger, deterministic_utf8_bytes


def confirmatory_timing_seed_sequence(
    config: ScientificConfig,
) -> tuple[SeedValue, ...]:
    return tuple(config.randomness.real_confirmatory_roots)


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
    staging = layout.roots.outputs_root / "cache" / "staging" #TODO: should be enums not hardcoded strings
    config = loaded.values
    maximum_order = config.study.maximum_coalition_order
    maximum_latency = config.materiality.reference_harness.p95_latency_maximum_seconds
    maximum_failure_rate = config.materiality.maximum_pooled_numerical_failure_rate
    logger = component_logger("experiments.coalition_scalability")
    cell_paths: list[Path] = []
    identity = capture_timing_environment_identity()
    environment_digest = hashlib.sha256(deterministic_utf8_bytes(identity)).hexdigest()
    environment_path = root / "provenance" / "environment" / "timing-environment.json" #TODO: should be enums not hardcoded strings
    environment_payload = cast(
        YamlNode,
        {
            "timing_environment_digest": environment_digest,
            "timing_environment_identity": identity,
        },
    )
    if environment_path.is_file():
        if environment_path.read_bytes() != deterministic_utf8_bytes(environment_payload):
            raise ValueError("timing environment changed across coalition scalability K cells")
    else:
        write_atomic_json(environment_path, environment_payload, staging)
    for client_count in config.robustness.scalability_client_counts:
        coalitions = expected_scalability_coalitions(config, client_count)
        registered = registry_coalition_count(client_count, maximum_order)
        if coalitions != registered:
            raise ValueError("derived coalition count must match the registry coalition count")
        payload_bytes = application_payload_bytes_per_epoch(client_count)
        seeds = confirmatory_timing_seed_sequence(config)
        logger.info(
            "scalability_phase phase=client_count_started client_count=%d coalition_count=%d seed_count=%d repetitions=%d",
            client_count,
            coalitions,
            len(seeds),
            config.scalability_timing.measured_repetitions_per_seed_client_count,
        )

        collected: list[ScalabilityMeasurement] = []
        for seed_index, seed in enumerate(seeds, start=1):
            seed_path = root / "metrics" / "per_seed" / f"k-{client_count}-seed-{seed}.json" #TODO: should be enums not hardcoded strings
            cell_path = (
                root
                / "provenance" #TODO: should be enums not hardcoded strings
                / "dependencies" #TODO: should be enums not hardcoded strings
                / f"cell-confirmatory-k-{client_count}-seed-{seed}.json" #TODO: should be enums not hardcoded strings
            )
            if cell_path.is_file() and seed_path.is_file():
                try:
                    existing = ScientificCellRecord.model_validate_json(cell_path.read_bytes())
                    outputs = existing.completion_record.mandatory_output_paths
                    hashes = existing.completion_record.mandatory_output_hashes
                    seed_cache = ScalabilitySeedCacheRecord.model_validate_json(
                        seed_path.read_bytes()
                    )
                    reusable = (
                        existing.state is ExperimentState.COMPLETED
                        and existing.material_digest == loaded.material_digest
                        and len(outputs) == len(hashes) == 1
                        and repository / outputs[0] == seed_path
                        and file_sha256(seed_path) == hashes[0]
                        and seed_cache.client_count == client_count
                        and seed_cache.seed == seed
                    )
                    if reusable:
                        measurements = tuple(
                            ScalabilityMeasurement(**measurement.model_dump())
                            for measurement in seed_cache.measurements
                        )
                        collected.extend(measurements)
                        cell_paths.append(cell_path)
                        logger.info(
                            "scalability_phase phase=seed_checkpoint_reused client_count=%d seed=%d seed_index=%d total_seeds=%d",
                            client_count,
                            seed,
                            seed_index,
                            len(seeds),
                        )
                        continue
                except ValueError:
                    pass
            logger.info(
                "scalability_phase phase=seed_started client_count=%d seed=%d seed_index=%d total_seeds=%d",
                client_count,
                seed,
                seed_index,
                len(seeds),
            )
            seed_started = perf_counter()
            seed_measurements = collect_scalability_seed_measurements(loaded, client_count, seed)
            seed_elapsed = perf_counter() - seed_started
            seed_peak_rss = max(
                (measurement.peak_rss_bytes for measurement in seed_measurements),
                default=0,
            )
            seed_payload: YamlNode = {
                "client_count": client_count,
                "seed": seed,
                "execution_role": ExecutionRole.CONFIRMATORY.value,
                "timing_environment_digest": environment_digest,
                "repetition_count": len(seed_measurements),
                "measurements": [
                    cast(YamlNode, asdict(measurement)) for measurement in seed_measurements
                ],
            }
            seed_hash = write_atomic_json(seed_path, seed_payload, staging)
            fingerprint = material_fingerprint(
                payload_digest(
                    cast(
                        YamlNode,
                        {
                            "producer": "coalition-scalability-timing-cell", #TODO: should be enums not hardcoded strings
                            "seed": seed,
                            "k": client_count,
                        },
                    )
                ),
                (environment_digest,),
            )
            completion = CompletionRecord(
                state=ExperimentState.COMPLETED,
                mandatory_output_paths=(seed_path.relative_to(repository).as_posix(),),
                mandatory_output_hashes=(seed_hash,),
            )
            cell = ScientificCellRecord(
                experiment_name=ExperimentName.COALITION_SCALABILITY,
                execution_role=ExecutionRole.CONFIRMATORY,
                semantic_cell_path=f"confirmatory/k-{client_count}/seed-{seed}",
                method_name=None,
                seed=seed,
                state=ExperimentState.COMPLETED,
                material_digest=loaded.material_digest,
                selected_client_ids=(),
                upstream_artifact_ids=(),
                dependency_fingerprint=fingerprint,
                runtime_seconds=seed_elapsed,
                peak_rss_bytes=seed_peak_rss,
                application_payload_bytes=len(seed_path.read_bytes()),
                completion_record=completion,
            )
            write_atomic_json(cell_path, cast(YamlNode, cell.model_dump(mode="json")), staging)
            logger.info(
                "scalability_phase phase=seed_checkpoint_published client_count=%d seed=%d seed_index=%d total_seeds=%d elapsed_seconds=%.3f",
                client_count,
                seed,
                seed_index,
                len(seeds),
                seed_elapsed,
            )
            cell_paths.append(cell_path)
            collected.extend(seed_measurements)
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
        aggregate = ScalabilityAggregateRecord(
            client_count=client_count,
            timing_seed_role=ExecutionRole.CONFIRMATORY,
            timing_seed_count=len(seeds),
            timing_environment_digest=environment_digest,
            expected_coalitions=coalitions,
            application_payload_bytes_per_epoch=payload_bytes,
            median_server_latency_seconds=summary.median_server_latency_seconds,
            p95_server_latency_seconds=summary.p95_server_latency_seconds,
            median_end_to_end_latency_seconds=summary.median_end_to_end_latency_seconds,
            p95_end_to_end_latency_seconds=summary.p95_end_to_end_latency_seconds,
            numerical_failure_rate=summary.numerical_failure_rate,
            throughput=scored_rate,
            local_timing_operating_point_available=(summary.local_timing_operating_point_available),
            global_timing_operating_point_available=(
                summary.global_timing_operating_point_available
            ),
            latency_within_target=summary.latency_within_target,
            numerical_failure_rate_within_bound=summary.numerical_failure_rate_within_bound,
            artifact_fit_seconds=summary.artifact_fit_seconds,
            state=summary.state,
        )
        path = root / "metrics" / "aggregate" / f"k-{client_count}.json" #TODO: should be enums not hardcoded strings
        write_atomic_json(path, cast(YamlNode, aggregate.model_dump(mode="json")), staging)
        logger.info(
            "scalability_phase phase=client_count_completed client_count=%d seed_count=%d",
            client_count,
            len(seeds),
        )
    return tuple(cell_paths)
