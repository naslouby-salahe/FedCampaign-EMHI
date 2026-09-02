from fedcampaign_emhi.config.loading import load_smoke_configuration
from fedcampaign_emhi.domain.enums import ExperimentState, SupportState
from fedcampaign_emhi.evaluation.scalability import (
    ScalabilityMeasurement,
    generate_scalability_feature_rows,
    latency_quantile,
    scalability_client_ids,
    summarize_scalability,
)


def test_scalability_client_ids_are_lexicographic() -> None:
    client_ids = scalability_client_ids(12)
    assert client_ids[0] == "client-000"
    assert client_ids[9] == "client-009"
    assert client_ids == tuple(sorted(client_ids))


def test_latency_quantile_uses_configured_fraction() -> None:
    values = (1.0, 2.0, 3.0, 4.0)
    assert latency_quantile(values, 1.0) == 4.0
    assert latency_quantile(values, 0.5) == 2.0


def test_scalability_feature_rows_are_deterministic_and_full_rank() -> None:
    loaded = load_smoke_configuration()
    first = generate_scalability_feature_rows(
        loaded.values, 6, 3, loaded.derived.model_input_dimension, 11
    )
    second = generate_scalability_feature_rows(
        loaded.values, 6, 3, loaded.derived.model_input_dimension, 11
    )
    assert first == second
    assert len(first) == 6
    assert len(first[0]) == 3
    assert len(first[0][0]) == loaded.derived.model_input_dimension
    assert first[0][0] != first[1][0]


def test_summarize_scalability_uses_end_to_end_quantile_for_latency_criterion() -> None:
    measurements = (
        ScalabilityMeasurement(
            client_count=6,
            seed=1,
            repetition=0,
            server_latency_seconds=0.01,
            end_to_end_latency_seconds=10.0,
            peak_rss_bytes=1,
            application_payload_bytes=120,
            numerical_failure_count=0,
            attempted_cell_count=1,
            local_timing_operating_point_available=True,
            global_timing_operating_point_available=True,
            artifact_fit_seconds=0.5,
        ),
    )
    summary = summarize_scalability(6, measurements, 1.0, 0.01, 1.0)
    assert summary.p95_end_to_end_latency_seconds == 10.0
    assert summary.latency_criterion_state is SupportState.NOT_SUPPORTED
    assert summary.numerical_criterion_state is SupportState.SUPPORTED
    assert summary.state is ExperimentState.COMPLETED
    assert summary.artifact_fit_seconds == 0.5


def test_summarize_scalability_aggregates_seed_level_p95_of_epoch_latencies() -> None:
    measurements = (
        ScalabilityMeasurement(
            client_count=4,
            seed=1,
            repetition=0,
            server_latency_seconds=0.01,
            end_to_end_latency_seconds=0.01,
            peak_rss_bytes=1,
            application_payload_bytes=80,
            numerical_failure_count=0,
            attempted_cell_count=1,
            local_timing_operating_point_available=True,
            global_timing_operating_point_available=True,
            artifact_fit_seconds=0.2,
        ),
        ScalabilityMeasurement(
            client_count=4,
            seed=1,
            repetition=0,
            server_latency_seconds=0.02,
            end_to_end_latency_seconds=0.04,
            peak_rss_bytes=2,
            application_payload_bytes=80,
            numerical_failure_count=0,
            attempted_cell_count=1,
            local_timing_operating_point_available=True,
            global_timing_operating_point_available=True,
            artifact_fit_seconds=0.2,
        ),
        ScalabilityMeasurement(
            client_count=4,
            seed=2,
            repetition=0,
            server_latency_seconds=0.03,
            end_to_end_latency_seconds=0.03,
            peak_rss_bytes=1,
            application_payload_bytes=80,
            numerical_failure_count=0,
            attempted_cell_count=1,
            local_timing_operating_point_available=True,
            global_timing_operating_point_available=True,
            artifact_fit_seconds=0.3,
        ),
        ScalabilityMeasurement(
            client_count=4,
            seed=2,
            repetition=0,
            server_latency_seconds=0.04,
            end_to_end_latency_seconds=0.08,
            peak_rss_bytes=3,
            application_payload_bytes=80,
            numerical_failure_count=0,
            attempted_cell_count=1,
            local_timing_operating_point_available=True,
            global_timing_operating_point_available=True,
            artifact_fit_seconds=0.3,
        ),
    )
    summary = summarize_scalability(4, measurements, 30.0, 0.01, 1.0)
    assert summary.p95_end_to_end_latency_seconds == 0.08
    assert summary.p95_server_latency_seconds == 0.04
    assert summary.median_end_to_end_latency_seconds == 0.035
    assert summary.artifact_fit_seconds == 0.3
    assert summary.latency_criterion_state is SupportState.SUPPORTED
