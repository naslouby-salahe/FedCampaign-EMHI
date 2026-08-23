import statistics
from dataclasses import dataclass

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import ClaimState, ExperimentState
from fedcampaign_emhi.domain.types import (
    ByteCount,
    ClientCount,
    LatencySeconds,
    Probability,
    RecordCount,
    SeedValue,
)
from fedcampaign_emhi.experiments.scalability import (
    derived_coalition_count,
    enumerate_scalability_plan,
    latency_gate,
    scalability_numerical_failure_gate,
)


@dataclass(frozen=True)
class ScalabilityMeasurement:
    client_count: ClientCount
    seed: SeedValue
    repetition: RecordCount
    server_latency_seconds: LatencySeconds
    end_to_end_latency_seconds: LatencySeconds
    peak_rss_bytes: ByteCount
    application_payload_bytes: ByteCount
    numerical_failure_count: RecordCount
    attempted_cell_count: RecordCount


@dataclass(frozen=True)
class ScalabilitySummary:
    client_count: ClientCount
    median_server_latency_seconds: LatencySeconds
    p95_server_latency_seconds: LatencySeconds
    median_end_to_end_latency_seconds: LatencySeconds
    peak_rss_bytes: ByteCount
    application_payload_bytes: ByteCount
    numerical_failure_rate: Probability
    latency_gate_state: ClaimState
    numerical_gate_state: ClaimState
    state: ExperimentState


def _p95(values: tuple[LatencySeconds, ...]) -> LatencySeconds:
    if not values:
        raise ValueError("p95 latency requires at least one measurement")
    ordered = sorted(values)
    rank = ((95 * len(ordered)) + 99) // 100
    return ordered[rank - 1]


def summarize_scalability(
    client_count: ClientCount,
    measurements: tuple[ScalabilityMeasurement, ...],
    maximum_p95_server_latency_seconds: LatencySeconds,
    maximum_numerical_failure_rate: Probability,
) -> ScalabilitySummary:
    selected = tuple(row for row in measurements if row.client_count == client_count)
    if not selected:
        raise ValueError("scalability summary requires matching measurements")
    server = tuple(row.server_latency_seconds for row in selected)
    end_to_end = tuple(row.end_to_end_latency_seconds for row in selected)
    failure_count = sum(row.numerical_failure_count for row in selected)
    attempted_count = sum(row.attempted_cell_count for row in selected)
    if attempted_count <= 0:
        raise ValueError("scalability summary requires attempted scientific cells")
    failure_rate = failure_count / attempted_count
    latency_passed = latency_gate(_p95(server), maximum_p95_server_latency_seconds)
    failure_passed = scalability_numerical_failure_gate(
        failure_count, attempted_count, maximum_numerical_failure_rate
    )
    return ScalabilitySummary(
        client_count=client_count,
        median_server_latency_seconds=statistics.median(server),
        p95_server_latency_seconds=_p95(server),
        median_end_to_end_latency_seconds=statistics.median(end_to_end),
        peak_rss_bytes=max(row.peak_rss_bytes for row in selected),
        application_payload_bytes=max(row.application_payload_bytes for row in selected),
        numerical_failure_rate=failure_rate,
        latency_gate_state=ClaimState.SUPPORTED if latency_passed else ClaimState.NOT_SUPPORTED,
        numerical_gate_state=ClaimState.SUPPORTED if failure_passed else ClaimState.NOT_SUPPORTED,
        state=ExperimentState.COMPLETED,
    )


def expected_scalability_coalitions(
    config: ScientificConfig, client_count: ClientCount
) -> RecordCount:
    plan = enumerate_scalability_plan(config)
    maximum_order = max(int(order) for order in plan.enabled_orders)
    return derived_coalition_count(client_count, maximum_order)
