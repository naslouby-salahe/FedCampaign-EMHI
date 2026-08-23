import math
from dataclasses import dataclass

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.domain.types import (
    ClientCount,
    FiniteFloat,
    Probability,
    RecordCount,
    SeedCount,
)


@dataclass(frozen=True)
class ScalabilityPlan:
    client_counts: tuple[ClientCount, ...]
    development_seed_count: SeedCount
    confirmatory_seed_count: SeedCount
    enabled_orders: tuple[CoalitionOrder, ...]


def enumerate_scalability_plan(config: ScientificConfig) -> ScalabilityPlan:
    maximum_order = int(config.study.maximum_coalition_order)
    return ScalabilityPlan(
        client_counts=tuple(config.robustness.scalability_client_counts),
        development_seed_count=len(config.randomness.real_development_roots),
        confirmatory_seed_count=len(config.randomness.real_confirmatory_roots),
        enabled_orders=tuple(CoalitionOrder(order) for order in range(1, maximum_order + 1)),
    )


def synthetic_workload_feature_dimension(
    event_type_hash_bucket_count: RecordCount,
) -> RecordCount:
    if event_type_hash_bucket_count <= 0:
        raise ValueError("hash bucket count must be positive")
    return event_type_hash_bucket_count + 2


def common_mode_loading(
    client_index: RecordCount, client_count: ClientCount, minimum: FiniteFloat, maximum: FiniteFloat
) -> FiniteFloat:
    if client_count <= 1:
        return minimum
    if not 0 <= client_index < client_count:
        raise ValueError("client index must lie within the configured client count")
    fraction = client_index / (client_count - 1)
    return minimum + fraction * (maximum - minimum)


def derived_coalition_count(client_count: ClientCount, maximum_order: RecordCount) -> RecordCount:
    if maximum_order <= 0:
        raise ValueError("maximum coalition order must be positive")
    if maximum_order > client_count:
        raise ValueError("maximum coalition order cannot exceed the client count")
    return sum(math.comb(client_count, order) for order in range(1, maximum_order + 1))


def latency_gate(p95_seconds: FiniteFloat, maximum_seconds: FiniteFloat) -> bool:
    return p95_seconds <= maximum_seconds


def scalability_numerical_failure_gate(
    pooled_failure_numerator: RecordCount,
    pooled_failure_denominator: RecordCount,
    maximum_rate: Probability,
) -> bool:
    if pooled_failure_denominator <= 0:
        raise ValueError("numerical-failure gate requires attempted cells")
    return pooled_failure_numerator / pooled_failure_denominator <= maximum_rate
