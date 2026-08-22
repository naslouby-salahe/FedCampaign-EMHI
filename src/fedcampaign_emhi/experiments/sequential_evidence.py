from dataclasses import dataclass

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.domain.types import (
    ClientCount,
    FiniteFloat,
    PositiveEpochCount,
    Probability,
    RecordCount,
)
from fedcampaign_emhi.emhi.evidence import (
    LOCKED_SIGNED_BET_LAMBDA,
    LOCKED_SIGNED_CLIP_BOUND,
    signed_theorem_compensator,
)
from fedcampaign_emhi.emhi.thresholds import clopper_pearson_one_sided_upper_bound


@dataclass(frozen=True)
class EstimatorFeasibilityPlan:
    primary_client_count: ClientCount
    maximum_coalition_order: CoalitionOrder
    support_sweep: tuple[RecordCount, ...]
    evaluation_samples_per_context_seed: RecordCount
    order_three_minimum_support: PositiveEpochCount


def enumerate_feasibility_plan(config: ScientificConfig) -> EstimatorFeasibilityPlan:
    return EstimatorFeasibilityPlan(
        primary_client_count=config.experiments.pure_order_separation_validation.primary_client_count,
        maximum_coalition_order=CoalitionOrder(config.study.maximum_coalition_order),
        support_sweep=config.support_grids.estimator_samples_per_context,
        evaluation_samples_per_context_seed=(
            config.synthetic.sample_sizes.estimator_evaluation_samples_per_context_seed
        ),
        order_three_minimum_support=config.context.minimum_support_epochs.order_three,
    )


@dataclass(frozen=True)
class FeasibilityAggregate:
    mean_coverage: Probability
    mean_projection_nrmse: FiniteFloat
    mean_standardized_null_bias: FiniteFloat
    pooled_failure_numerator: RecordCount
    pooled_failure_denominator: RecordCount

    @property
    def pooled_numerical_failure_rate(self) -> FiniteFloat:
        if self.pooled_failure_denominator <= 0:
            raise ValueError("pooled numerical-failure rate requires attempted fits")
        return self.pooled_failure_numerator / self.pooled_failure_denominator


def aggregate_feasibility(
    seed_coverages: tuple[Probability, ...],
    seed_projection_nrmse: tuple[FiniteFloat, ...],
    seed_null_bias: tuple[FiniteFloat, ...],
    failure_counts: tuple[RecordCount, ...],
    attempted_counts: tuple[RecordCount, ...],
) -> FeasibilityAggregate:
    if not (len(seed_coverages) == len(seed_projection_nrmse) == len(seed_null_bias)):
        raise ValueError("feasibility aggregates require aligned per-seed metrics")
    if len(failure_counts) != len(attempted_counts):
        raise ValueError("pooled failure counts must be aligned across seeds")
    return FeasibilityAggregate(
        mean_coverage=sum(seed_coverages) / len(seed_coverages),
        mean_projection_nrmse=sum(seed_projection_nrmse) / len(seed_projection_nrmse),
        mean_standardized_null_bias=sum(seed_null_bias) / len(seed_null_bias),
        pooled_failure_numerator=sum(failure_counts),
        pooled_failure_denominator=sum(attempted_counts),
    )


def support_rows_for_requested_count(
    requested_observations: RecordCount, cell_count: RecordCount
) -> RecordCount:
    if cell_count <= 0:
        raise ValueError("context-cell count must be positive")
    if requested_observations <= 0:
        raise ValueError("requested observations must be positive")
    return requested_observations * cell_count + 1


def latent_support_cell(epoch_index: RecordCount, cell_count: RecordCount) -> RecordCount:
    if cell_count <= 0:
        raise ValueError("context-cell count must be positive")
    return epoch_index % cell_count


def deterministic_outside_midpoint(cell: RecordCount, cell_count: RecordCount) -> FiniteFloat:
    if cell >= cell_count:
        raise ValueError("support cell exceeds the requested context-cell count")
    return (cell + 1 / 2) / cell_count


def restricted_arl(
    stopping_times: tuple[RecordCount, ...], maximum_epochs: PositiveEpochCount
) -> FiniteFloat:
    if not stopping_times:
        raise ValueError("restricted ARL requires at least one trajectory")
    for stopping_time in stopping_times:
        if stopping_time <= 0:
            raise ValueError("stopping times must be positive")
    capped = sum(min(stopping_time, maximum_epochs) for stopping_time in stopping_times)
    return capped / len(stopping_times)


def restricted_arl_lower_bound_passes(
    bca_lower_bound: FiniteFloat, minimum_epochs: PositiveEpochCount
) -> bool:
    return bca_lower_bound >= minimum_epochs


def theorem_route_assumption_checks(
    clip_bound: FiniteFloat,
    bet_lambda: FiniteFloat,
    configured_arl_alpha: FiniteFloat,
    expected_compensator_tolerance: FiniteFloat,
    observed_factors: tuple[FiniteFloat, ...],
) -> bool:
    expected_compensator = signed_theorem_compensator(clip_bound, bet_lambda)
    locked_compensator = signed_theorem_compensator(
        LOCKED_SIGNED_CLIP_BOUND, LOCKED_SIGNED_BET_LAMBDA
    )
    compensator_ok = (
        abs(expected_compensator - locked_compensator) <= expected_compensator_tolerance
    )
    factors_ok = all(factor >= 0.0 for factor in observed_factors)
    threshold_ok = 1.0 / configured_arl_alpha > 1.0
    return compensator_ok and factors_ok and threshold_ok


def calibrated_route_heldout_pfa_gate(
    false_stops: RecordCount,
    heldout_horizons: RecordCount,
    confidence: Probability,
    target_pfa: Probability,
) -> bool:
    upper = clopper_pearson_one_sided_upper_bound(false_stops, heldout_horizons, confidence)
    return upper <= target_pfa
