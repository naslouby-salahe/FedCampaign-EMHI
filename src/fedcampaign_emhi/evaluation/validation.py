from collections import deque
from dataclasses import dataclass
from math import exp, isclose

from fedcampaign_emhi.artifacts.provenance import content_digest
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.datasets.campaigns import campaign_duration_epochs, merge_malicious_runs
from fedcampaign_emhi.detection import first_local_stop_epoch
from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    DatasetName,
    PartitionRole,
)
from fedcampaign_emhi.domain.types import (
    Boolean,
    ConfigurationDigest,
    MetricValue,
    OwnershipStatement,
    RankReference,
    RecordCount,
    SeedValue,
)
from fedcampaign_emhi.emhi.calibration import fold_observation_indexes
from fedcampaign_emhi.emhi.contexts import (
    assign_context_cell,
    exact_exclusion_members,
    histogram_bin_index,
    inclusive_context_members,
    lagged_context_epoch,
    leave_one_out_context_members,
    minimum_support_epochs_for_order,
    partial_coalition_context_members,
)
from fedcampaign_emhi.emhi.evidence import (
    operational_evidence_factor,
    signed_evidence_factor,
    within_order_aggregate,
)
from fedcampaign_emhi.emhi.projection import (
    blocked_fold_bounds,
    blocked_fold_sizes,
    proper_subset_design_column_count,
    select_ridge_penalty,
)
from fedcampaign_emhi.emhi.sequential import (
    distributed_support_predicate,
    trailing_support_window_client_ids,
)
from fedcampaign_emhi.emhi.structure import bounded_basis, clip_rank, midrank, tensor_dimension
from fedcampaign_emhi.emhi.thresholds import select_calibrated_threshold
from fedcampaign_emhi.evaluation.metrics import censored_plot_value, strict_odi_outcome
from fedcampaign_emhi.runtime import log_stage


@dataclass(frozen=True)
class SmokeFixtureName:
    label: OwnershipStatement


@dataclass(frozen=True)
class SmokeValidationResult:
    passed: Boolean
    failures: tuple[SmokeFixtureName, ...]
    executed_fixture_names: tuple[SmokeFixtureName, ...]
    expected_fixture_count: RecordCount
    maximum_absolute_identity_error: MetricValue
    exact_identity_tolerance: MetricValue
    expected_negative_fixture_count: RecordCount
    correctly_rejected_negative_fixture_count: RecordCount


@dataclass
class FixtureCollector:
    failures: deque[SmokeFixtureName]
    executed_fixture_names: deque[SmokeFixtureName]

    def record(self, fixture_name: SmokeFixtureName, condition: Boolean) -> None:
        self.executed_fixture_names.append(fixture_name)
        if not condition:
            self.failures.append(fixture_name)


def _check(fixture_name: SmokeFixtureName, condition: Boolean, collector: FixtureCollector) -> None:
    collector.record(fixture_name, condition)


MIDRANK_TIES = SmokeFixtureName("midrank ties")
RANK_CLIPPING_LOW = SmokeFixtureName("rank clipping low")
RANK_CLIPPING_HIGH = SmokeFixtureName("rank clipping high")
HISTOGRAM_BINS = SmokeFixtureName("histogram bins")
EXACT_EXCLUSION = SmokeFixtureName("exact exclusion")
INCLUSIVE_CONTEXT = SmokeFixtureName("inclusive context")
LEAVE_ONE_OUT = SmokeFixtureName("leave-one-out")
PARTIAL_TRIPLE = SmokeFixtureName("partial triple")
LAG_SEMANTICS = SmokeFixtureName("lag semantics")
KMEANS_TIE = SmokeFixtureName("kmeans tie")
PROJECTION_DIMENSIONS = SmokeFixtureName("projection dimensions")
BASIS_WIDTH = SmokeFixtureName("basis width")
RIDGE_TIE = SmokeFixtureName("ridge tie selects larger lambda within tolerance")
ABSTENTION_BOUNDARY = SmokeFixtureName("abstention boundary fixture")
BLOCKED_FOLD_SIZES = SmokeFixtureName("blocked fold sizes")
FOLD_BOUNDS = SmokeFixtureName("fold bounds")
CROSSFIT_FOLDS = SmokeFixtureName("cross-fitted calibration folds")
SIGNED_POSITIVE = SmokeFixtureName("signed positive factor")
SIGNED_NEGATIVE = SmokeFixtureName("signed negative factor")
OPERATIONAL_NORM = SmokeFixtureName("operational norm factor")
SUPPORT_UNION = SmokeFixtureName("support union")
FINITE_HORIZON_CANDIDATES = SmokeFixtureName("finite horizon candidates")
LOCAL_PERSISTENCE = SmokeFixtureName("local persistence triggers at epoch 3")
STRICT_ODI = SmokeFixtureName("strict ODI")
SAME_EPOCH_TIE_ODI = SmokeFixtureName("same-epoch tie ODI")
NULL_NO_STOP_STORAGE = SmokeFixtureName("null no-stop storage")
SEMANTIC_IDEMPOTENCY = SmokeFixtureName("semantic idempotency digests")
CAMPAIGN_MERGE = SmokeFixtureName("campaign merge fixture")
CAMPAIGN_DURATION = SmokeFixtureName("campaign duration")
NEUTRAL_AGGREGATE = SmokeFixtureName("within-order neutral aggregate")


@dataclass(frozen=True)
class SemanticIdempotencyRecord:
    dataset: DatasetName
    seed: SeedValue
    role: PartitionRole

    def semantic_payload(self) -> YamlNode:
        return {
            "dataset": self.dataset.value,
            "seed": self.seed,
            "role": self.role.value,
        }


@log_stage("evaluation.validation")
def run_synthetic_module_validation(loaded: LoadedScientificConfiguration) -> SmokeValidationResult:
    context = loaded.values.context
    projection = loaded.values.projection
    evidence = loaded.values.evidence
    distributed_support = loaded.values.distributed_support
    basis_size = loaded.values.basis.primary_size
    collector = FixtureCollector(deque(), deque())
    failures = collector
    exact_tolerance = loaded.values.synthetic_module_validation.exact_identity_tolerance

    tie_rank = midrank(0.5, RankReference(scores=(0.0, 0.5, 0.5, 1.0)))
    _check(MIDRANK_TIES, abs(tie_rank - 0.5) <= 0.0, collector)

    _check(
        RANK_CLIPPING_LOW,
        clip_rank(0.0, context.rank_clip_epsilon) == context.rank_clip_epsilon,
        collector,
    )
    _check(
        RANK_CLIPPING_HIGH,
        abs(clip_rank(1.0, context.rank_clip_epsilon) - (1.0 - context.rank_clip_epsilon)) <= 0.0,
        collector,
    )

    bin_indices = tuple(
        histogram_bin_index(rank, context.outside_histogram_bin_count)
        for rank in (0.01, 0.13, 0.99)
    )
    _check(HISTOGRAM_BINS, bin_indices == (0, 1, 7), collector)
    histogram_masses = tuple(
        bin_indices.count(index) / len(bin_indices)
        for index in range(context.outside_histogram_bin_count)
    )
    expected_masses = (1 / 3, 1 / 3, 0.0, 0.0, 0.0, 0.0, 0.0, 1 / 3)
    _check(
        SmokeFixtureName("histogram normalized mass"),
        histogram_masses == expected_masses[: context.outside_histogram_bin_count],
        collector,
    )

    selected = loaded.values.synthetic_module_validation.exclusion_fixture_selected_clients
    coalition = loaded.values.synthetic_module_validation.exclusion_fixture_coalition
    _check(
        EXACT_EXCLUSION,
        exact_exclusion_members(selected, coalition) == ("c4", "c5", "c6"),
        failures,
    )
    _check(INCLUSIVE_CONTEXT, inclusive_context_members(selected, coalition) == selected, failures)
    _check(
        LEAVE_ONE_OUT,
        leave_one_out_context_members(selected, coalition) == ("c2", "c3", "c4", "c5", "c6"),
        failures,
    )
    _check(
        PARTIAL_TRIPLE,
        partial_coalition_context_members(selected, coalition) == ("c3", "c4", "c5", "c6"),
        failures,
    )
    _check(
        LAG_SEMANTICS,
        lagged_context_epoch(5, context.outside_lag_epochs) == 4,
        failures,
    )

    tie_centroids = ((0.0, 0.0), (2.0, 0.0))
    tied_cell = assign_context_cell(
        (1.0, 0.0), tie_centroids, context.kmeans.assignment_tie_tolerance
    )
    _check(KMEANS_TIE, tied_cell == 0, failures)

    dimension_checks = (
        tensor_dimension(basis_size, CoalitionOrder.ONE) == 3,
        tensor_dimension(basis_size, CoalitionOrder.TWO) == 9,
        tensor_dimension(basis_size, CoalitionOrder.THREE) == 27,
        proper_subset_design_column_count(CoalitionOrder.ONE, basis_size) == 1,
        proper_subset_design_column_count(CoalitionOrder.TWO, basis_size) == 7,
        proper_subset_design_column_count(CoalitionOrder.THREE, basis_size) == 37,
    )
    _check(PROJECTION_DIMENSIONS, all(dimension_checks), failures)

    _check(BASIS_WIDTH, len(bounded_basis(0.5, basis_size)) == basis_size, failures)

    ridge_candidates = projection.ridge_candidates
    ridge_selected = select_ridge_penalty(
        ridge_candidates,
        tuple(0.05 + projection.selection_tie_tolerance_mse / 2 for _ in ridge_candidates),
        projection.selection_tie_tolerance_mse,
    )
    _check(
        RIDGE_TIE,
        abs(ridge_selected - max(ridge_candidates)) <= projection.selection_tie_tolerance_mse,
        failures,
    )
    exact_tie_selected = select_ridge_penalty(
        ridge_candidates[-3:-1], (0.05, 0.05), projection.selection_tie_tolerance_mse
    )
    _check(
        SmokeFixtureName("ridge tie exact instance"),
        exact_tie_selected == 0.1,
        failures,
    )

    order_three_minimum = minimum_support_epochs_for_order(
        CoalitionOrder.THREE,
        context.minimum_support_epochs.order_one,
        context.minimum_support_epochs.order_two,
        context.minimum_support_epochs.order_three,
    )
    _check(
        ABSTENTION_BOUNDARY,
        399 < order_three_minimum <= 400,
        failures,
    )
    _check(
        SmokeFixtureName("abstention boundary exact minimum"),
        order_three_minimum == context.minimum_support_epochs.order_three
        and order_three_minimum == 400,
        failures,
    )

    folds = blocked_fold_sizes(11, 5)
    _check(BLOCKED_FOLD_SIZES, folds == (3, 2, 2, 2, 2), failures)
    bounds = blocked_fold_bounds(11, 5)
    _check(
        FOLD_BOUNDS,
        bounds == ((0, 3), (3, 5), (5, 7), (7, 9), (9, 11)),
        failures,
    )

    crossfit_splits = fold_observation_indexes(4, 2)
    _check(
        CROSSFIT_FOLDS,
        crossfit_splits[0] == ((2, 3), (0, 1)) and crossfit_splits[1] == ((0, 1), (2, 3)),
        failures,
    )

    _check(
        SIGNED_POSITIVE,
        abs(signed_evidence_factor(1.0, evidence.clip_bound, evidence.bet_lambda) - exp(0.375))
        < 1e-15,
        failures,
    )
    _check(
        SIGNED_NEGATIVE,
        abs(signed_evidence_factor(-1.0, evidence.clip_bound, evidence.bet_lambda) - exp(-0.625))
        < 1e-15,
        failures,
    )

    norm_factor = operational_evidence_factor(
        (3.0, 4.0), 5.0, projection.norm_reference_floor, evidence.clip_bound, evidence.bet_lambda
    )
    _check(OPERATIONAL_NORM, abs(norm_factor - exp(-0.125)) < 1e-15, failures)

    window_union = trailing_support_window_client_ids(
        (("c1", "c2"), ("c2", "c3")), distributed_support.trailing_window_epochs
    )
    _check(
        SUPPORT_UNION,
        window_union == ("c1", "c2", "c3")
        and distributed_support_predicate(window_union, distributed_support.minimum_clients),
        failures,
    )

    finite_horizon_candidates = evidence.calibrated_finite_horizon.threshold_candidates[:4]
    exact_fixture_false_stop_counts = (20, 15, 5, 0)
    exact_fixture_observed_horizons = 200
    finite_horizon_selected = select_calibrated_threshold(
        finite_horizon_candidates,
        exact_fixture_false_stop_counts,
        exact_fixture_observed_horizons,
        evidence.calibrated_finite_horizon.calibration_confidence,
        evidence.calibrated_finite_horizon.target_pfa,
    )
    _check(
        FINITE_HORIZON_CANDIDATES,
        all(
            isclose(candidate, expected, rel_tol=0.0, abs_tol=0.0)
            for candidate, expected in zip(
                finite_horizon_candidates, (2.0, 3.0, 5.0, 10.0), strict=True
            )
        )
        and finite_horizon_selected is not None
        and isclose(finite_horizon_selected, 10.0, rel_tol=0.0, abs_tol=0.0),
        failures,
    )

    persistence_epoch = first_local_stop_epoch((True, False, True), 2, 3)
    _check(LOCAL_PERSISTENCE, persistence_epoch == 2, failures)

    _check(STRICT_ODI, strict_odi_outcome(4, (5, 8)).indicator == 1, failures)
    _check(SAME_EPOCH_TIE_ODI, strict_odi_outcome(5, (5, 8)).indicator == 0, failures)

    horizon = loaded.values.campaign.evaluation_horizon_epochs
    offset = evidence.no_stop_plot_offset_epochs
    _check(
        NULL_NO_STOP_STORAGE,
        censored_plot_value(horizon, offset) == horizon + offset == 61,
        failures,
    )

    smoke_root = loaded.values.randomness.engineering_smoke_root
    semantic_record = SemanticIdempotencyRecord(
        dataset=DatasetName.TON_IOT_NETWORK, seed=smoke_root, role=PartitionRole.NUISANCE_FIT
    )
    digest_a: ConfigurationDigest = content_digest(semantic_record.semantic_payload())
    digest_b: ConfigurationDigest = content_digest(semantic_record.semantic_payload())
    _check(SEMANTIC_IDEMPOTENCY, digest_a == digest_b and len(digest_a) == 64, failures)

    merged = merge_malicious_runs((1, 2, 4, 20), 2)
    _check(CAMPAIGN_MERGE, merged == ((1, 4), (20, 20)), failures)
    _check(CAMPAIGN_DURATION, campaign_duration_epochs(1, 4) == 4, failures)
    _check(NEUTRAL_AGGREGATE, within_order_aggregate(()) >= 1.0, failures)

    identity_errors = (
        abs(tie_rank - 0.5),
        abs(clip_rank(0.0, context.rank_clip_epsilon) - context.rank_clip_epsilon),
        abs(clip_rank(1.0, context.rank_clip_epsilon) - (1.0 - context.rank_clip_epsilon)),
        abs(signed_evidence_factor(1.0, evidence.clip_bound, evidence.bet_lambda) - exp(0.375)),
        abs(signed_evidence_factor(-1.0, evidence.clip_bound, evidence.bet_lambda) - exp(-0.625)),
        abs(norm_factor - exp(-0.125)),
    )
    maximum_absolute_identity_error = max(identity_errors)
    expected_fixture_count = loaded.values.synthetic_module_validation.expected_fixture_count
    return SmokeValidationResult(
        passed=(
            not collector.failures
            and len(collector.executed_fixture_names) == expected_fixture_count
            and maximum_absolute_identity_error <= exact_tolerance
        ),
        failures=tuple(collector.failures),
        executed_fixture_names=tuple(collector.executed_fixture_names),
        expected_fixture_count=expected_fixture_count,
        maximum_absolute_identity_error=maximum_absolute_identity_error,
        exact_identity_tolerance=exact_tolerance,
        expected_negative_fixture_count=0,
        correctly_rejected_negative_fixture_count=0,
    )
