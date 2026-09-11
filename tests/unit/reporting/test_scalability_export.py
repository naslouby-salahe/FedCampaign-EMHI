from pathlib import Path

from fedcampaign_emhi.artifacts.records import ScalabilityAggregateRecord
from fedcampaign_emhi.artifacts.storage import write_atomic_json
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import ExecutionRole, ExperimentName, ExperimentState
from fedcampaign_emhi.reporting.experiment_exports import (
    materialize_experiment_exports,
    scalability_aggregate_csv_bytes,
)


def _aggregate_record(client_count: int) -> ScalabilityAggregateRecord:
    return ScalabilityAggregateRecord(
        client_count=client_count,
        timing_seed_role=ExecutionRole.CONFIRMATORY,
        timing_seed_count=5,
        timing_environment_digest="a" * 64,
        expected_coalitions=client_count,
        application_payload_bytes_per_epoch=1024,
        median_server_latency_seconds=0.5,
        p95_server_latency_seconds=1.0,
        median_end_to_end_latency_seconds=0.6,
        p95_end_to_end_latency_seconds=1.1,
        numerical_failure_rate=0.0,
        throughput=10.0,
        local_timing_operating_point_available=True,
        global_timing_operating_point_available=True,
        latency_within_target=True,
        numerical_failure_rate_within_bound=True,
        artifact_fit_seconds=2.0,
        state=ExperimentState.COMPLETED,
    )


def test_scalability_aggregate_csv_orders_rows_by_client_count() -> None:
    records = (_aggregate_record(24), _aggregate_record(6), _aggregate_record(12))
    csv_bytes = scalability_aggregate_csv_bytes(records)
    rows = csv_bytes.decode("utf-8").splitlines()
    assert rows[0].startswith("client_count,")
    assert [row.split(",")[0] for row in rows[1:]] == ["6", "12", "24"]


def test_coalition_scalability_export_reads_aggregate_metric_paths(
    tmp_path: Path,
    production_configuration: LoadedScientificConfiguration,
) -> None:
    repository = tmp_path / "repository"
    aggregate_dir = repository / "metrics" / "aggregate"
    staging = repository / "staging"
    aggregate_paths: list[Path] = []
    for client_count in (6, 12):
        path = aggregate_dir / f"k-{client_count}.json"
        write_atomic_json(
            path,
            _aggregate_record(client_count).model_dump(mode="json"),
            staging,
        )
        aggregate_paths.append(path)

    exported = materialize_experiment_exports(
        production_configuration,
        repository,
        ExperimentName.COALITION_SCALABILITY,
        (),
        (),
        tuple(aggregate_paths),
        True,
    )

    assert len(exported) == 1
    table_path = exported[0]
    assert table_path.name == "scalability-summary.csv"
    rows = table_path.read_text(encoding="utf-8").splitlines()
    assert [row.split(",")[0] for row in rows[1:]] == ["6", "12"]
