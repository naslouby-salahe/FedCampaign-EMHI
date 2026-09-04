import statistics
from dataclasses import dataclass

from fedcampaign_emhi.artifacts.provenance import content_digest, material_fingerprint
from fedcampaign_emhi.artifacts.records import (
    ComparatorNullPfaRecord,
    ComparatorRuntimeTiebreakRecord,
    ComparatorTargetErrorRecord,
    StrongComparatorCompositionRecord,
)
from fedcampaign_emhi.artifacts.storage import payload_digest
from fedcampaign_emhi.comparators.contracts import native_target_order
from fedcampaign_emhi.domain.enums import MethodName
from fedcampaign_emhi.domain.types import (
    ArtifactFilename,
    Boolean,
    ConfidenceLevel,
    ConfigurationDigest,
    EffectCoefficient,
    FalseAlarmRate,
    NumericalTolerance,
    PositiveEpochCount,
    RankValue,
    RecordCount,
    RuntimeSeconds,
    StandardizedError,
)
from fedcampaign_emhi.emhi.thresholds import clopper_pearson_one_sided_upper_bound


@dataclass(frozen=True)
class CompositionCandidateResult:
    method_name: MethodName
    invariants_pass: Boolean
    calibration_succeeded: Boolean
    heldout_false_stops: RecordCount
    heldout_horizons: RecordCount
    mean_standardized_error: StandardizedError
    median_runtime_seconds: RuntimeSeconds


@dataclass(frozen=True)
class StrongComparatorComposition:
    selected_method: MethodName
    native_target_order: PositiveEpochCount | None
    artifact_filename: ArtifactFilename


def candidate_is_eligible(
    candidate_result: CompositionCandidateResult,
    confidence: ConfidenceLevel,
    target_pfa: FalseAlarmRate,
) -> Boolean:
    if not candidate_result.invariants_pass or not candidate_result.calibration_succeeded:
        return False
    upper = clopper_pearson_one_sided_upper_bound(
        candidate_result.heldout_false_stops,
        candidate_result.heldout_horizons,
        confidence,
    )
    return upper <= target_pfa


def mean_standardized_error(
    per_seed_errors: tuple[StandardizedError, ...],
) -> StandardizedError:
    if not per_seed_errors:
        raise ValueError("standardized target-order error requires development seeds")
    return sum(per_seed_errors) / len(per_seed_errors)


def median_runtime_seconds(runtimes: tuple[RuntimeSeconds, ...]) -> RuntimeSeconds:
    if not runtimes:
        raise ValueError("median runtime requires at least one measurement")
    return statistics.median(runtimes)


def _prefer_candidate(
    candidate_error: StandardizedError,
    candidate_runtime: RuntimeSeconds,
    candidate_name: MethodName,
    selected_error: StandardizedError,
    selected_runtime: RuntimeSeconds,
    selected_name: MethodName,
    error_tie_tolerance: NumericalTolerance,
    runtime_tie_tolerance: RuntimeSeconds,
) -> Boolean:
    error_delta = candidate_error - selected_error
    if error_delta < -error_tie_tolerance:
        return True
    if abs(error_delta) > error_tie_tolerance:
        return False
    runtime_delta = candidate_runtime - selected_runtime
    if runtime_delta < -runtime_tie_tolerance:
        return True
    return abs(runtime_delta) <= runtime_tie_tolerance and candidate_name < selected_name


def select_strongest_comparator(
    candidates: tuple[MethodName, ...],
    standardized_errors: tuple[StandardizedError, ...],
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
        if _prefer_candidate(
            standardized_errors[index],
            runtimes_seconds[index],
            candidates[index],
            standardized_errors[selected_index],
            runtimes_seconds[selected_index],
            candidates[selected_index],
            error_tie_tolerance,
            runtime_tie_tolerance,
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


@dataclass(frozen=True)
class CompositionSelectionInputs:
    reference_theta: EffectCoefficient
    error_tie_tolerance: NumericalTolerance
    runtime_tie_tolerance: RuntimeSeconds
    calibration_horizons_per_seed: RecordCount
    heldout_null_horizons_per_seed: RecordCount
    timed_scoring_rows: RecordCount
    artifact_filename: ArtifactFilename


def selection_rule_identity(inputs: CompositionSelectionInputs) -> ConfigurationDigest:
    payload = {
        "reference_theta": inputs.reference_theta,
        "error_tie_tolerance": inputs.error_tie_tolerance,
        "runtime_tie_tolerance": inputs.runtime_tie_tolerance,
        "calibration_horizons_per_seed": inputs.calibration_horizons_per_seed,
        "heldout_null_horizons_per_seed": inputs.heldout_null_horizons_per_seed,
        "timed_scoring_rows": inputs.timed_scoring_rows,
    }
    return content_digest(payload)


def _target_error_record(candidate: CompositionCandidateResult) -> ComparatorTargetErrorRecord:
    native_order = native_target_order(candidate.method_name)
    if native_order is None:
        raise ValueError("target error requires a native-order candidate")
    return ComparatorTargetErrorRecord(
        method_name=candidate.method_name,
        native_target_order=native_order,
        mean_standardized_error=candidate.mean_standardized_error,
    )


def build_composition_selection_record(
    candidate_results: tuple[CompositionCandidateResult, ...],
    inputs: CompositionSelectionInputs,
    confidence: ConfidenceLevel,
    target_pfa: FalseAlarmRate,
    material_digest: ConfigurationDigest,
    source_artifact_hashes: tuple[ConfigurationDigest, ...],
) -> StrongComparatorCompositionRecord:
    if not candidate_results:
        raise ValueError("composition selection requires candidate results")
    eligible = tuple(
        result
        for result in candidate_results
        if candidate_is_eligible(result, confidence, target_pfa)
        and native_target_order(result.method_name) is not None
    )
    if not eligible:
        raise ValueError("composition selection has no eligible native-order candidate")
    selected_method = select_strongest_comparator(
        tuple(result.method_name for result in eligible),
        tuple(result.mean_standardized_error for result in eligible),
        tuple(result.median_runtime_seconds for result in eligible),
        inputs.error_tie_tolerance,
        inputs.runtime_tie_tolerance,
    )
    selected_order = native_target_order(selected_method)
    if selected_order is None:
        raise ValueError("selected composition candidate has no native target order")
    rule_hash = selection_rule_identity(inputs)
    null_pfa = tuple(
        ComparatorNullPfaRecord(
            method_name=result.method_name,
            heldout_false_stops=result.heldout_false_stops,
            heldout_horizons=result.heldout_horizons,
            heldout_upper_pfa=clopper_pearson_one_sided_upper_bound(
                result.heldout_false_stops, result.heldout_horizons, confidence
            )
            if result.heldout_horizons
            else None,
            eligible=result in eligible,
        )
        for result in candidate_results
    )
    target_errors = tuple(
        _target_error_record(result)
        for result in candidate_results
        if native_target_order(result.method_name) is not None
    )
    runtimes = tuple(
        ComparatorRuntimeTiebreakRecord(
            method_name=result.method_name,
            median_runtime_seconds=result.median_runtime_seconds,
        )
        for result in candidate_results
    )
    payload = {
        "selected_method": selected_method.value,
        "selected_native_order": selected_order,
        "eligible_candidates": [result.method_name.value for result in eligible],
        "candidate_native_orders": [record.model_dump(mode="json") for record in target_errors],
        "null_pfa_results": [record.model_dump(mode="json") for record in null_pfa],
        "target_error_results": [record.model_dump(mode="json") for record in target_errors],
        "runtime_tiebreak_results": [record.model_dump(mode="json") for record in runtimes],
        "selection_rule_hash": rule_hash,
        "source_artifact_hashes": list(source_artifact_hashes),
    }
    return StrongComparatorCompositionRecord(
        selected_method=selected_method,
        selected_native_order=selected_order,
        eligible_candidates=tuple(result.method_name for result in eligible),
        candidate_native_orders=target_errors,
        null_pfa_results=null_pfa,
        target_error_results=target_errors,
        runtime_tiebreak_results=runtimes,
        selection_rule_hash=rule_hash,
        source_artifact_hashes=source_artifact_hashes,
        dependency_fingerprint=material_fingerprint(material_digest, source_artifact_hashes),
        content_digest=payload_digest(payload),
    )


def mean_rank_fusion(ranks: tuple[RankValue, ...]) -> RankValue:
    if not ranks:
        raise ValueError("mean rank fusion requires at least one client rank")
    return sum(ranks) / len(ranks)


def max_rank_fusion(ranks: tuple[RankValue, ...]) -> RankValue:
    if not ranks:
        raise ValueError("max rank fusion requires at least one client rank")
    return max(ranks)
