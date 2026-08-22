from dataclasses import dataclass

from fedcampaign_emhi.comparators.contracts import native_target_order
from fedcampaign_emhi.domain.enums import MethodName
from fedcampaign_emhi.domain.types import (
    ArtifactFilename,
    FiniteFloat,
    NumericalTolerance,
    PositiveEpochCount,
    RecordCount,
    RuntimeSeconds,
    SeedCount,
)
from fedcampaign_emhi.emhi.thresholds import clopper_pearson_one_sided_upper_bound


@dataclass(frozen=True)
class CompositionCandidateResult:
    method_name: MethodName
    invariants_pass: bool
    calibration_succeeded: bool
    heldout_false_stops: RecordCount
    calibration_horizons: RecordCount
    mean_standardized_error: FiniteFloat
    median_runtime_seconds: RuntimeSeconds


@dataclass(frozen=True)
class StrongComparatorComposition:
    selected_method: MethodName
    native_target_order: PositiveEpochCount | None
    artifact_filename: ArtifactFilename


def candidate_is_eligible(
    candidate_result: CompositionCandidateResult,
    confidence: FiniteFloat,
    target_pfa: FiniteFloat,
) -> bool:
    if not candidate_result.invariants_pass or not candidate_result.calibration_succeeded:
        return False
    upper = clopper_pearson_one_sided_upper_bound(
        candidate_result.heldout_false_stops,
        candidate_result.calibration_horizons,
        confidence,
    )
    return upper <= target_pfa


def mean_standardized_error(
    per_seed_errors: tuple[FiniteFloat, ...],
) -> FiniteFloat:
    if not per_seed_errors:
        raise ValueError("standardized target-order error requires development seeds")
    return sum(per_seed_errors) / len(per_seed_errors)


def median_runtime_seconds(runtimes: tuple[RuntimeSeconds, ...]) -> RuntimeSeconds:
    if not runtimes:
        raise ValueError("median runtime requires at least one measurement")
    ordered = sorted(runtimes)
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def select_strongest_comparator(
    candidates: tuple[MethodName, ...],
    standardized_errors: tuple[FiniteFloat, ...],
    runtimes_seconds: tuple[RuntimeSeconds, ...],
    error_tie_tolerance: NumericalTolerance,
    runtime_tie_tolerance: RuntimeSeconds,
) -> MethodName:
    if not candidates:
        raise ValueError("strong comparator composition requires at least one candidate")
    if len(candidates) != len(standardized_errors) or len(candidates) != len(runtimes_seconds):
        raise ValueError("candidates, errors, and runtimes must be aligned")
    selected_index = 0
    for index in range(1, len(candidates)):
        error_delta = standardized_errors[index] - standardized_errors[selected_index]
        if error_delta < -error_tie_tolerance:
            selected_index = index
            continue
        if abs(error_delta) <= error_tie_tolerance:
            runtime_delta = runtimes_seconds[index] - runtimes_seconds[selected_index]
            if runtime_delta < -runtime_tie_tolerance:
                selected_index = index
                continue
            if (
                abs(runtime_delta) <= runtime_tie_tolerance
                and candidates[index].value < candidates[selected_index].value
            ):
                selected_index = index
    return candidates[selected_index]


def materialize_composition_record(
    selected_method: MethodName,
    artifact_filename: ArtifactFilename,
) -> StrongComparatorComposition:
    return StrongComparatorComposition(
        selected_method=selected_method,
        native_target_order=native_target_order(selected_method),
        artifact_filename=artifact_filename,
    )


def composition_seed_count(development_root_count: SeedCount) -> SeedCount:
    return development_root_count
