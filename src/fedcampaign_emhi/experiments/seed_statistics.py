import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from fedcampaign_emhi.analysis.results import (
    SECONDARY_HOLM_STATISTICS,
    paired_seed_differences,
)
from fedcampaign_emhi.analysis.statistics import (
    exact_sign_flip_means,
    hodges_lehmann_shift,
    holm_adjusted_p_values,
    paired_mean_bca_interval,
    sign_flip_p_value,
)
from fedcampaign_emhi.artifacts.provenance import (
    material_fingerprint,
    statistical_analysis_boundary_digest,
)
from fedcampaign_emhi.artifacts.records import (
    BenignCommonModePositivePowerMeasurementRecord,
    BenignHorizonRecord,
    BenignPartitionRecord,
    CampaignRegistryRecord,
    ClientDetectorScoreStream,
    ClientFeatureScalerRecord,
    CountStressDiagnosticRecord,
    DatasetSplitRecord,
    DetectorScoreArtifactRecord,
    EMHIFitArtifactRecord,
    MarginalRankArtifactRecord,
    PreparedDatasetRecord,
    SeedSummaryRecord,
    StatisticalRecord,
)
from fedcampaign_emhi.artifacts.storage import (
    build_artifact_layout,
    file_sha256,
    method_artifact_stem,
    payload_digest,
    write_atomic_json,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration, ScientificConfig
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.datasets.preprocessing import apply_robust_scaler
from fedcampaign_emhi.detection import (
    assign_detector_families,
    detector_seed,
    score_client,
)
from fedcampaign_emhi.domain.enums import (
    DatasetName,
    ExecutionRole,
    ExperimentName,
    MethodName,
    PrimaryHolmHypothesis,
)
from fedcampaign_emhi.domain.types import (
    ArtifactIdentity,
    BenignHorizon,
    Boolean,
    ComponentName,
    ConfigurationDigest,
    DetectorScore,
    EpochIndexValue,
    FalseAlarmRate,
    FeatureValue,
    MaterialDependencyFingerprint,
    MetricRate,
    MetricValue,
    RecordCount,
    RelativePath,
    RobustnessCountMultiplier,
    RobustScaler,
    SeedValue,
    ThresholdValue,
)
from fedcampaign_emhi.emhi.structure import build_marginal_rank_artifact
from fedcampaign_emhi.evaluation.metrics import (
    campaign_detection_rate,
    common_mode_suppression,
    outside_conditioning_power_loss,
    pfa_difference,
)
from fedcampaign_emhi.evaluation.sequential import (
    TrajectoryCache,
    calibrate_global_operating_point,
    calibrate_operating_points,
    global_stop_epoch,
    horizon_trajectory,
)
from fedcampaign_emhi.experiments.execution import campaign_dataset
from fedcampaign_emhi.experiments.registry import (
    confirmatory_completeness_within_tolerance,
)
from fedcampaign_emhi.experiments.robustness import (
    EpochEventVolume,
    detection_rate_loss_within_maximum,
    enumerate_benign_common_mode_plan,
    false_campaign_suppression_meets_minimum,
    federation_wide_epoch_event_counts,
    paired_false_campaign_difference,
    rolling_benign_horizons,
    select_high_volume_windows,
    stress_epoch_feature_values,
    window_event_counts,
)
from fedcampaign_emhi.experiments.seed_evaluation import (
    calibrate_comparator_operating_point,
    comparator_epoch_scores,
    comparator_evidence_scores,
    comparator_stop,
)
from fedcampaign_emhi.experiments.seed_materialization import (
    build_campaign_rows,
    local_pfa_target,
    materialize_detector_scores_with_retry,
    materialize_emhi_fit_with_retry,
    materialize_marginal_ranks_with_retry,
    preprocessing_paths,
)


@dataclass(frozen=True)
class MethodSeedOdi:
    seed: SeedValue
    method_value: MetricValue
    source_evaluation_id: ArtifactIdentity


def _raw_evaluation_operating_point(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    method_name: MethodName,
    seed: SeedValue,
) -> YamlNode | None:
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    path = (
        root
        / "evaluations"
        / "raw"
        / ExecutionRole.CONFIRMATORY.value
        / method_artifact_stem(method_name)
        / f"seed-{seed}.json"
    )
    if not path.is_file():
        return None
    payload = cast(YamlNode, json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(payload, Mapping):
        return None
    calibration_value = payload.get("calibration")
    if not isinstance(calibration_value, Mapping):
        return None
    global_value = calibration_value.get("global")
    if not isinstance(global_value, Mapping):
        return None
    return cast(YamlNode, global_value)


def _method_has_eligible_operating_point(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    method_name: MethodName,
    seed: SeedValue,
    require_heldout_pfa_within_target: Boolean,
) -> Boolean:
    operating_point = _raw_evaluation_operating_point(
        loaded, repository, experiment_name, method_name, seed
    )
    if not isinstance(operating_point, Mapping):
        return False
    threshold = operating_point.get("threshold")
    if not isinstance(threshold, int | float):
        return False
    if not require_heldout_pfa_within_target:
        return True
    heldout_upper = operating_point.get("heldout_upper_pfa")
    if not isinstance(heldout_upper, int | float):
        return False
    return float(heldout_upper) <= float(
        loaded.values.evidence.calibrated_finite_horizon.target_pfa
    )


def _paired_methods_have_eligible_operating_points(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    comparator_method: MethodName,
    confirmatory_seeds: tuple[SeedValue, ...],
) -> Boolean:
    return all(
        _method_has_eligible_operating_point(
            loaded,
            repository,
            experiment_name,
            method_name,
            seed,
            require_heldout_pfa_within_target=True,
        )
        for method_name in (MethodName.FULL_FEDCAMPAIGN_EMHI, comparator_method)
        for seed in confirmatory_seeds
    )


def materialize_seed_statistics(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
) -> tuple[Path, ...]:
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    summary_paths = tuple(sorted((root / "metrics" / "seed-summaries").glob("**/*.json")))
    summaries = tuple(
        SeedSummaryRecord.model_validate_json(path.read_bytes()) for path in summary_paths
    )
    method_groups = _group_method_summaries(summaries)
    expected_confirmatory = loaded.values.randomness.real_confirmatory_roots
    method_groups = [
        (method_name, records)
        for method_name, records in method_groups
        if confirmatory_completeness_within_tolerance(
            loaded,
            expected_confirmatory,
            tuple(
                record.seed
                for record in records
                if record.execution_role is ExecutionRole.CONFIRMATORY
            ),
        )
    ]
    if not method_groups:
        return ()
    raw_p_values: list[FalseAlarmRate] = []
    estimates: list[MetricRate] = []
    intervals: list[tuple[MetricRate, MetricRate] | None] = []
    sources: list[tuple[ArtifactIdentity, ...]] = []
    fingerprints: list[MaterialDependencyFingerprint] = []
    for _method_name, records in method_groups:
        values = tuple(record.method_value for record in records)
        estimate = sum(values) / len(values)
        estimates.append(estimate)
        source_ids = tuple(
            source_id for record in records for source_id in record.source_evaluation_ids
        )
        sources.append(source_ids)
        hashes = tuple(record.content_digest for record in records)
        fingerprints.append(
            material_fingerprint(
                statistical_analysis_boundary_digest(loaded.values),
                hashes,
            )
        )
        if len(values) < 2:
            raw_p_values.append(1.0)
            intervals.append(None)
            continue
        flipped = exact_sign_flip_means(values)
        raw_p_values.append(sign_flip_p_value(estimate, flipped, True))
        intervals.append(
            paired_mean_bca_interval(
                values,
                loaded.values.statistics.confidence_level,
                loaded.values.statistics.bootstrap_replicates,
                loaded.values.randomness.statistical_analysis_base_seed,
            )
        )
    adjusted = holm_adjusted_p_values(
        tuple(method_name.value for method_name, _records in method_groups),
        tuple(raw_p_values),
    )
    staging = layout.roots.outputs_root / "cache" / "staging"
    paths: list[Path] = []
    for index, (method_name, records) in enumerate(method_groups):
        interval = intervals[index]
        meets_threshold = adjusted[index] < loaded.values.statistics.nominal_significance_alpha
        payload: YamlNode = {
            "experiment_name": experiment_name.value,
            "method_name": method_name.value,
            "metric_name": "strict_odi_rate",
            "estimate": estimates[index],
            "raw_p_value": raw_p_values[index],
            "adjusted_p_value": adjusted[index],
            "confidence_level": loaded.values.statistics.confidence_level,
            "confidence_lower": None if interval is None else interval[0],
            "confidence_upper": None if interval is None else interval[1],
            "meets_threshold": meets_threshold,
            "source_result_ids": list(sources[index]),
            "independent_unit_count": len(records),
        }
        record = StatisticalRecord(
            hypothesis_identifier=f"{experiment_name.value}:{method_name.value}:strict_odi_rate",
            metric_name="strict_odi_rate",
            method_name=method_name,
            independent_unit_count=len(records),
            estimate=estimates[index],
            raw_p_value=raw_p_values[index],
            adjusted_p_value=adjusted[index],
            confidence_level=loaded.values.statistics.confidence_level,
            confidence_lower=None if interval is None else interval[0],
            confidence_upper=None if interval is None else interval[1],
            meets_threshold=meets_threshold,
            source_result_ids=sources[index],
            dependency_fingerprint=fingerprints[index],
            content_digest=payload_digest(payload),
        )
        path = (
            root
            / "statistics"
            / "seed-level"
            / f"{method_artifact_stem(method_name)}-strict-odi-rate.json"
        )
        write_atomic_json(path, cast(YamlNode, record.model_dump(mode="json")), staging)
        paths.append(path)
    return tuple(paths)


def _group_method_summaries(
    summaries: tuple[SeedSummaryRecord, ...],
) -> tuple[tuple[MethodName, tuple[SeedSummaryRecord, ...]], ...]:
    method_groups: list[tuple[MethodName, tuple[SeedSummaryRecord, ...]]] = []
    for summary in summaries:
        existing = next(
            (
                index
                for index, (method_name, _records) in enumerate(method_groups)
                if method_name is summary.method_name
            ),
            None,
        )
        if existing is None:
            method_groups.append((summary.method_name, (summary,)))
        else:
            method_name, records = method_groups[existing]
            method_groups[existing] = (method_name, (*records, summary))
    return tuple(method_groups)


def materialize_not_tested_primary_holm_statistic(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
) -> Path | None:
    hypotheses = {
        ExperimentName.PRIMARY_STRICT_ODI_EVALUATION: (
            PrimaryHolmHypothesis.PRIMARY_ODI_ADVANTAGE_OVER_ORDER_AT_MOST_TWO_EMHI,
            "paired_strict_odi_rate_advantage",
        ),
        ExperimentName.BENIGN_COMMON_MODE_ROBUSTNESS: (
            PrimaryHolmHypothesis.COMMON_MODE_FALSE_CAMPAIGN_REDUCTION,
            "false_campaign_reduction",
        ),
        ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE: (
            PrimaryHolmHypothesis.STRONG_LOCAL_ODI_ABOVE_MINIMUM,
            "strong_local_strict_odi_rate",
        ),
    }
    specification = hypotheses.get(experiment_name)
    if specification is None:
        return None
    dataset_name = campaign_dataset(loaded, experiment_name)
    prepared_path = preprocessing_paths(loaded, repository, dataset_name)[1]
    prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
    if prepared.has_sufficient_clients or prepared.selected_client_ids:
        return None
    hypothesis, metric_name = specification
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    source_paths = tuple(
        sorted(
            (
                root
                / "evaluations"
                / "raw"
                / ExecutionRole.CONFIRMATORY.value
                / method_artifact_stem(MethodName.FULL_FEDCAMPAIGN_EMHI)
            ).glob("*.json")
        )
    )
    expected_seeds = loaded.values.randomness.real_confirmatory_roots
    if len(source_paths) != len(expected_seeds):
        raise FileNotFoundError(
            f"missing confirmatory Not Tested sources for {experiment_name.value}"
        )
    source_digests = tuple(file_sha256(path) for path in source_paths)
    source_ids = tuple(path.relative_to(repository).as_posix() for path in source_paths)
    payload: YamlNode = {
        "experiment_name": experiment_name.value,
        "hypothesis_identifier": hypothesis.value,
        "metric_name": metric_name,
        "method_name": MethodName.FULL_FEDCAMPAIGN_EMHI.value,
        "independent_unit_count": len(source_paths),
        "estimate": 0.0,
        "raw_p_value": None,
        "confidence_level": None,
        "confidence_lower": None,
        "confidence_upper": None,
        "source_result_ids": list(source_ids),
    }
    record = StatisticalRecord(
        hypothesis_identifier=hypothesis.value,
        metric_name=metric_name,
        method_name=MethodName.FULL_FEDCAMPAIGN_EMHI.value,
        independent_unit_count=len(source_paths),
        estimate=0.0,
        raw_p_value=None,
        adjusted_p_value=None,
        confidence_level=None,
        confidence_lower=None,
        confidence_upper=None,
        meets_threshold=False,
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values),
            source_digests,
        ),
        content_digest=payload_digest(payload),
    )
    path = root / "statistics" / "tests" / "primary-holm-not-tested.json"
    write_atomic_json(
        path,
        cast(YamlNode, record.model_dump(mode="json")),
        layout.roots.outputs_root / "cache" / "staging",
    )
    return path


def _hypothesis_artifact_stem(identifier: ComponentName) -> RelativePath:
    return identifier.lower().replace(" ", "-")


def _load_seed_summaries(
    root: Path,
) -> tuple[tuple[Path, SeedSummaryRecord], ...]:
    summary_root = root / "metrics" / "seed-summaries"
    paths = tuple(sorted(summary_root.glob("**/*.json")))
    return tuple((path, SeedSummaryRecord.model_validate_json(path.read_bytes())) for path in paths)


def _confirmatory_method_summaries(
    summaries: tuple[tuple[Path, SeedSummaryRecord], ...],
    method_name: MethodName,
) -> tuple[tuple[Path, SeedSummaryRecord], ...]:
    return tuple(
        (path, record)
        for path, record in summaries
        if record.execution_role is ExecutionRole.CONFIRMATORY
        and record.method_name is method_name
        and record.metric_name == "strict_odi_rate"
    )


def _method_seed_odi(
    record: SeedSummaryRecord, summary_identity: ArtifactIdentity
) -> MethodSeedOdi:
    source_identity = (
        record.source_evaluation_ids[0] if record.source_evaluation_ids else summary_identity
    )
    return MethodSeedOdi(
        seed=record.seed,
        method_value=record.method_value,
        source_evaluation_id=source_identity,
    )


def _pair_confirmatory_odi(
    full_summaries: tuple[tuple[Path, SeedSummaryRecord], ...],
    comparator_summaries: tuple[tuple[Path, SeedSummaryRecord], ...],
) -> tuple[
    tuple[Path, ...],
    tuple[SeedSummaryRecord, ...],
    tuple[SeedSummaryRecord, ...],
    tuple[MethodSeedOdi, ...],
    tuple[MethodSeedOdi, ...],
]:
    comparator_by_seed = tuple((record.seed, path, record) for path, record in comparator_summaries)
    paired_paths: list[Path] = []
    paired_full_records: list[SeedSummaryRecord] = []
    paired_comparator_records: list[SeedSummaryRecord] = []
    paired_full_odi: list[MethodSeedOdi] = []
    paired_comparator_odi: list[MethodSeedOdi] = []
    for path, record in full_summaries:
        match = next(
            (
                (comparator_path, comparator_record)
                for seed, comparator_path, comparator_record in comparator_by_seed
                if seed == record.seed
            ),
            None,
        )
        if match is None:
            continue
        comparator_path, comparator_record = match
        full_identity = path.as_posix()
        comparator_identity = comparator_path.as_posix()
        paired_paths.extend((path, comparator_path))
        paired_full_records.append(record)
        paired_comparator_records.append(comparator_record)
        paired_full_odi.append(_method_seed_odi(record, full_identity))
        paired_comparator_odi.append(_method_seed_odi(comparator_record, comparator_identity))
    return (
        tuple(paired_paths),
        tuple(paired_full_records),
        tuple(paired_comparator_records),
        tuple(paired_full_odi),
        tuple(paired_comparator_odi),
    )


def _materialize_paired_confirmatory_odi_contrast(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    hypothesis_identifier: ComponentName,
    comparator_method: MethodName,
    metric_name: ComponentName,
) -> StatisticalRecord | None:
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    summaries = _load_seed_summaries(root)
    full_summaries = _confirmatory_method_summaries(summaries, MethodName.FULL_FEDCAMPAIGN_EMHI)
    comparator_summaries = _confirmatory_method_summaries(summaries, comparator_method)
    paired_paths, paired_full, paired_comparator, paired_full_odi, paired_comparator_odi = (
        _pair_confirmatory_odi(full_summaries, comparator_summaries)
    )
    paired_seeds = tuple(item.seed for item in paired_full_odi)
    expected = loaded.values.randomness.real_confirmatory_roots
    source_ids = tuple(path.relative_to(repository).as_posix() for path in paired_paths)
    source_digests = tuple(file_sha256(path) for path in paired_paths)
    complete = confirmatory_completeness_within_tolerance(loaded, expected, paired_seeds)
    matched_eligible = _paired_methods_have_eligible_operating_points(
        loaded, repository, experiment_name, comparator_method, expected
    )
    if not complete or not matched_eligible:
        payload: YamlNode = {
            "experiment_name": experiment_name.value,
            "hypothesis_identifier": hypothesis_identifier,
            "metric_name": metric_name,
            "method_name": MethodName.FULL_FEDCAMPAIGN_EMHI.value,
            "independent_unit_count": len(paired_seeds),
            "estimate": 0.0,
            "raw_p_value": None,
            "confidence_level": None,
            "confidence_lower": None,
            "confidence_upper": None,
            "hodges_lehmann_shift": None,
            "source_result_ids": list(source_ids),
        }
        record = StatisticalRecord(
            hypothesis_identifier=hypothesis_identifier,
            metric_name=metric_name,
            method_name=MethodName.FULL_FEDCAMPAIGN_EMHI.value,
            independent_unit_count=len(paired_seeds),
            estimate=0.0,
            raw_p_value=None,
            adjusted_p_value=None,
            confidence_level=None,
            confidence_lower=None,
            confidence_upper=None,
            hodges_lehmann_shift=None,
            meets_threshold=False,
            source_result_ids=source_ids,
            dependency_fingerprint=material_fingerprint(
                statistical_analysis_boundary_digest(loaded.values), source_digests
            ),
            content_digest=payload_digest(payload),
        )
        path = (
            root
            / "statistics"
            / "tests"
            / f"{_hypothesis_artifact_stem(hypothesis_identifier)}.json"
        )
        write_atomic_json(
            path,
            cast(YamlNode, record.model_dump(mode="json")),
            layout.roots.outputs_root / "cache" / "staging",
        )
        return record
    paired_with_difference = tuple(
        full.model_copy(
            update={
                "reference_method_name": comparator.method_name,
                "reference_value": comparator.method_value,
                "paired_difference": full.method_value - comparator.method_value,
            }
        )
        for full, comparator in zip(paired_full, paired_comparator, strict=True)
    )
    differences = paired_seed_differences(paired_with_difference)
    if len(differences) != len(paired_full_odi) or len(differences) != len(paired_comparator_odi):
        raise ValueError("paired ODI differences must preserve confirmatory seed pairing")
    estimate = sum(differences) / len(differences)
    shift = hodges_lehmann_shift(differences)
    raw_p_value = sign_flip_p_value(estimate, exact_sign_flip_means(differences), True)
    interval = paired_mean_bca_interval(
        differences,
        loaded.values.statistics.confidence_level,
        loaded.values.statistics.bootstrap_replicates,
        loaded.values.randomness.statistical_analysis_base_seed,
    )
    payload = {
        "experiment_name": experiment_name.value,
        "hypothesis_identifier": hypothesis_identifier,
        "metric_name": metric_name,
        "method_name": MethodName.FULL_FEDCAMPAIGN_EMHI.value,
        "independent_unit_count": len(differences),
        "estimate": estimate,
        "raw_p_value": raw_p_value,
        "confidence_level": loaded.values.statistics.confidence_level,
        "confidence_lower": interval[0],
        "confidence_upper": interval[1],
        "hodges_lehmann_shift": shift,
        "source_result_ids": list(source_ids),
    }
    record = StatisticalRecord(
        hypothesis_identifier=hypothesis_identifier,
        metric_name=metric_name,
        method_name=MethodName.FULL_FEDCAMPAIGN_EMHI.value,
        independent_unit_count=len(differences),
        estimate=estimate,
        raw_p_value=raw_p_value,
        adjusted_p_value=None,
        confidence_level=loaded.values.statistics.confidence_level,
        confidence_lower=interval[0],
        confidence_upper=interval[1],
        hodges_lehmann_shift=shift,
        meets_threshold=raw_p_value < loaded.values.statistics.nominal_significance_alpha,
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values),
            source_digests,
        ),
        content_digest=payload_digest(payload),
    )
    path = (
        root / "statistics" / "tests" / f"{_hypothesis_artifact_stem(hypothesis_identifier)}.json"
    )
    write_atomic_json(
        path,
        cast(YamlNode, record.model_dump(mode="json")),
        layout.roots.outputs_root / "cache" / "staging",
    )
    return record


def materialize_confirmatory_odi_inferences(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    primary_not_tested: Boolean,
) -> None:
    if experiment_name is ExperimentName.PRIMARY_STRICT_ODI_EVALUATION and not primary_not_tested:
        _materialize_paired_confirmatory_odi_contrast(
            loaded,
            repository,
            experiment_name,
            PrimaryHolmHypothesis.PRIMARY_ODI_ADVANTAGE_OVER_ORDER_AT_MOST_TWO_EMHI.value,
            MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI,
            "paired_strict_odi_rate_advantage",
        )
        return
    if experiment_name not in {
        ExperimentName.EXCLUSION_MECHANISM_ABLATION,
        ExperimentName.PURIFICATION_AND_ORDER_ABLATION,
    }:
        return
    for family_experiment, hypothesis, comparator_method in SECONDARY_HOLM_STATISTICS:
        if family_experiment is not experiment_name:
            continue
        _materialize_paired_confirmatory_odi_contrast(
            loaded,
            repository,
            experiment_name,
            hypothesis.value,
            comparator_method,
            "paired_strict_odi_rate_advantage",
        )


def _write_null_odi_hypothesis_record(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    hypothesis_identifier: ComponentName,
    metric_name: ComponentName,
    independent_unit_count: RecordCount,
    source_ids: tuple[ArtifactIdentity, ...],
    source_digests: tuple[ConfigurationDigest, ...],
) -> Path:
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    payload: YamlNode = {
        "experiment_name": experiment_name.value,
        "hypothesis_identifier": hypothesis_identifier,
        "metric_name": metric_name,
        "method_name": MethodName.FULL_FEDCAMPAIGN_EMHI.value,
        "independent_unit_count": independent_unit_count,
        "estimate": 0.0,
        "raw_p_value": None,
        "confidence_level": None,
        "confidence_lower": None,
        "confidence_upper": None,
        "hodges_lehmann_shift": None,
        "source_result_ids": list(source_ids),
    }
    record = StatisticalRecord(
        hypothesis_identifier=hypothesis_identifier,
        metric_name=metric_name,
        method_name=MethodName.FULL_FEDCAMPAIGN_EMHI.value,
        independent_unit_count=independent_unit_count,
        estimate=0.0,
        raw_p_value=None,
        adjusted_p_value=None,
        confidence_level=None,
        confidence_lower=None,
        confidence_upper=None,
        hodges_lehmann_shift=None,
        meets_threshold=False,
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values),
            source_digests,
        ),
        content_digest=payload_digest(payload),
    )
    path = (
        root / "statistics" / "tests" / f"{_hypothesis_artifact_stem(hypothesis_identifier)}.json"
    )
    write_atomic_json(
        path,
        cast(YamlNode, record.model_dump(mode="json")),
        layout.roots.outputs_root / "cache" / "staging",
    )
    return path


def materialize_strong_local_odi_statistic(
    loaded: LoadedScientificConfiguration,
    repository: Path,
) -> Path | None:
    experiment_name = ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    not_tested_path = root / "statistics" / "tests" / "primary-holm-not-tested.json"
    if not_tested_path.is_file():
        return None
    summaries = _load_seed_summaries(root)
    confirmatory = _confirmatory_method_summaries(summaries, MethodName.FULL_FEDCAMPAIGN_EMHI)
    expected = loaded.values.randomness.real_confirmatory_roots
    observed = tuple(record.seed for _path, record in confirmatory)
    complete = confirmatory_completeness_within_tolerance(loaded, expected, observed)
    operating_points_available = all(
        _method_has_eligible_operating_point(
            loaded,
            repository,
            experiment_name,
            MethodName.FULL_FEDCAMPAIGN_EMHI,
            seed,
            require_heldout_pfa_within_target=False,
        )
        for seed in expected
    )
    source_paths = tuple(path for path, _record in confirmatory)
    source_ids = tuple(path.relative_to(repository).as_posix() for path in source_paths)
    source_digests = tuple(file_sha256(path) for path in source_paths)
    hypothesis_identifier = PrimaryHolmHypothesis.STRONG_LOCAL_ODI_ABOVE_MINIMUM
    if not complete:
        return None
    if not operating_points_available:
        return _write_null_odi_hypothesis_record(
            loaded,
            repository,
            experiment_name,
            hypothesis_identifier.value,
            "strong_local_strict_odi_rate",
            len(observed),
            source_ids,
            source_digests,
        )
    minimum = loaded.values.materiality.strong_local.minimum_strict_odi_rate
    shifted = tuple(record.method_value - minimum for _path, record in confirmatory)
    estimate: MetricValue = sum(shifted) / len(shifted)
    raw_p_value = sign_flip_p_value(estimate, exact_sign_flip_means(shifted), True)
    shift = hodges_lehmann_shift(shifted)
    interval = paired_mean_bca_interval(
        shifted,
        loaded.values.statistics.confidence_level,
        loaded.values.statistics.bootstrap_replicates,
        loaded.values.randomness.statistical_analysis_base_seed,
    )
    payload: YamlNode = {
        "experiment_name": experiment_name.value,
        "hypothesis_identifier": hypothesis_identifier.value,
        "metric_name": "strong_local_strict_odi_rate",
        "method_name": MethodName.FULL_FEDCAMPAIGN_EMHI.value,
        "independent_unit_count": len(shifted),
        "estimate": estimate,
        "raw_p_value": raw_p_value,
        "confidence_level": loaded.values.statistics.confidence_level,
        "confidence_lower": interval[0],
        "confidence_upper": interval[1],
        "hodges_lehmann_shift": shift,
        "source_result_ids": list(source_ids),
    }
    record = StatisticalRecord(
        hypothesis_identifier=hypothesis_identifier.value,
        metric_name="strong_local_strict_odi_rate",
        method_name=MethodName.FULL_FEDCAMPAIGN_EMHI.value,
        independent_unit_count=len(shifted),
        estimate=estimate,
        raw_p_value=raw_p_value,
        adjusted_p_value=None,
        confidence_level=loaded.values.statistics.confidence_level,
        confidence_lower=interval[0],
        confidence_upper=interval[1],
        hodges_lehmann_shift=shift,
        meets_threshold=raw_p_value < loaded.values.statistics.nominal_significance_alpha,
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values),
            source_digests,
        ),
        content_digest=payload_digest(payload),
    )
    path = root / "statistics" / "tests" / "strong-local-odi-above-minimum.json"
    write_atomic_json(
        path,
        cast(YamlNode, record.model_dump(mode="json")),
        layout.roots.outputs_root / "cache" / "staging",
    )
    return path


def _stress_window_false_declaration_rate(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    threshold: ThresholdValue | None,
    stress_windows: tuple[BenignHorizon, ...],
    trajectory_cache: TrajectoryCache,
) -> MetricRate | None:
    if threshold is None or not stress_windows:
        return None
    stops = tuple(
        global_stop_epoch(
            horizon_trajectory(
                config,
                ranks,
                fit,
                BenignHorizonRecord(
                    start_epoch=window.start_epoch, epoch_indexes=window.epoch_indexes
                ),
                None,
                trajectory_cache,
            ),
            threshold,
        )
        is not None
        for window in stress_windows
    )
    return sum(stops) / len(stops)


def _comparator_stress_window_false_declaration_rate(
    evidence_scores: tuple[tuple[EpochIndexValue, DetectorScore], ...],
    threshold: ThresholdValue | None,
    stress_windows: tuple[BenignHorizon, ...],
) -> MetricRate | None:
    if threshold is None or not stress_windows:
        return None
    stops = tuple(
        comparator_stop(evidence_scores, window.epoch_indexes, threshold) is not None
        for window in stress_windows
    )
    return sum(stops) / len(stops)


def _benign_common_mode_seed_fcr(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    seed: SeedValue,
    stress_windows: tuple[BenignHorizon, ...],
) -> tuple[MetricRate, MetricRate, tuple[Path, ...]] | None:
    _inventory_path, _prepared_path, split_path, partitions_path, _campaigns_path = (
        preprocessing_paths(loaded, repository, dataset_name)
    )
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    partitions = BenignPartitionRecord.model_validate_json(partitions_path.read_bytes())
    score_path = materialize_detector_scores_with_retry(loaded, repository, dataset_name, seed)
    rank_path = materialize_marginal_ranks_with_retry(
        loaded, repository, dataset_name, seed, score_path
    )
    ranks = MarginalRankArtifactRecord.model_validate_json(rank_path.read_bytes())
    fit_path = materialize_emhi_fit_with_retry(
        loaded,
        repository,
        dataset_name,
        seed,
        MethodName.FULL_FEDCAMPAIGN_EMHI,
        score_path,
        rank_path,
    )
    fit = EMHIFitArtifactRecord.model_validate_json(fit_path.read_bytes())
    emhi_calibration = calibrate_global_operating_point(loaded.values, ranks, fit, partitions)
    trajectory_cache = TrajectoryCache()
    emhi_fcr = _stress_window_false_declaration_rate(
        loaded.values,
        ranks,
        fit,
        emhi_calibration.threshold,
        stress_windows,
        trajectory_cache,
    )
    raw_scores = comparator_epoch_scores(
        loaded, repository, ranks, MethodName.RAW_MEAN_RANK_FUSION, split.nuisance_fit_epochs
    )
    comparator_scores = comparator_evidence_scores(loaded, raw_scores, split.nuisance_fit_epochs)
    comparator_threshold, *_rest = calibrate_comparator_operating_point(
        loaded, comparator_scores, partitions
    )
    raw_mean_fcr = _comparator_stress_window_false_declaration_rate(
        comparator_scores, comparator_threshold, stress_windows
    )
    if emhi_fcr is None or raw_mean_fcr is None:
        return None
    return emhi_fcr, raw_mean_fcr, (score_path, rank_path, fit_path)


def _benign_common_mode_seed_difference(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    seed: SeedValue,
    stress_windows: tuple[BenignHorizon, ...],
) -> tuple[MetricRate, tuple[Path, ...]] | None:
    outcome = _benign_common_mode_seed_fcr(loaded, repository, dataset_name, seed, stress_windows)
    if outcome is None:
        return None
    emhi_fcr, raw_mean_fcr, paths = outcome
    reduction = paired_false_campaign_difference(raw_mean_fcr, emhi_fcr)
    if reduction != pfa_difference(raw_mean_fcr, emhi_fcr):
        raise ValueError("false-campaign reduction must match the PFA difference")
    return reduction, paths


def materialize_benign_common_mode_statistic(
    loaded: LoadedScientificConfiguration,
    repository: Path,
) -> Path | None:
    experiment_name = ExperimentName.BENIGN_COMMON_MODE_ROBUSTNESS
    plan = enumerate_benign_common_mode_plan(loaded.values)
    required_methods = {
        MethodName.FULL_FEDCAMPAIGN_EMHI,
        MethodName.RAW_MEAN_RANK_FUSION,
    }
    if not required_methods.issubset(plan.methods):
        return None
    _inventory_path, prepared_path, split_path, _partitions_path, _campaigns_path = (
        preprocessing_paths(loaded, repository, plan.dataset_name)
    )
    prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
    if not prepared.selected_client_ids:
        return None
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    horizon_length = loaded.values.campaign.evaluation_horizon_epochs
    all_windows = rolling_benign_horizons(
        split.heldout_benign_epochs,
        horizon_length,
        plan.stress_stride_epochs,
    )
    if not all_windows:
        return None
    epoch_volumes = tuple(
        EpochEventVolume(
            client_id=epoch.client_id,
            epoch_index=epoch.epoch_index,
            raw_event_count=epoch.raw_event_count,
        )
        for epoch in prepared.epochs
    )
    epoch_totals = federation_wide_epoch_event_counts(epoch_volumes, prepared.selected_client_ids)
    counts = window_event_counts(all_windows, epoch_totals)
    stress_windows = select_high_volume_windows(all_windows, counts, plan.top_event_count_fraction)
    expected_confirmatory = loaded.values.randomness.real_confirmatory_roots
    differences: list[MetricRate] = []
    source_paths: list[Path] = []
    covered_seeds: list[SeedValue] = []
    for seed in expected_confirmatory:
        outcome = _benign_common_mode_seed_difference(
            loaded, repository, plan.dataset_name, seed, stress_windows
        )
        if outcome is None:
            continue
        difference, seed_paths = outcome
        differences.append(difference)
        source_paths.extend(seed_paths)
        covered_seeds.append(seed)
    if not confirmatory_completeness_within_tolerance(
        loaded, expected_confirmatory, tuple(covered_seeds)
    ):
        return None
    estimate = sum(differences) / len(differences)
    shift = hodges_lehmann_shift(tuple(differences))
    flipped = exact_sign_flip_means(tuple(differences))
    raw_p_value = sign_flip_p_value(estimate, flipped, True)
    interval = paired_mean_bca_interval(
        tuple(differences),
        loaded.values.statistics.confidence_level,
        loaded.values.statistics.bootstrap_replicates,
        loaded.values.randomness.statistical_analysis_base_seed,
    )
    source_digests = tuple(file_sha256(path) for path in source_paths)
    source_ids = tuple(path.relative_to(repository).as_posix() for path in source_paths)
    payload: YamlNode = {
        "experiment_name": experiment_name.value,
        "hypothesis_identifier": PrimaryHolmHypothesis.COMMON_MODE_FALSE_CAMPAIGN_REDUCTION.value,
        "metric_name": "false_campaign_reduction",
        "method_name": MethodName.FULL_FEDCAMPAIGN_EMHI.value,
        "independent_unit_count": len(differences),
        "estimate": estimate,
        "raw_p_value": raw_p_value,
        "confidence_level": loaded.values.statistics.confidence_level,
        "confidence_lower": interval[0],
        "confidence_upper": interval[1],
        "hodges_lehmann_shift": shift,
        "source_result_ids": list(source_ids),
    }
    record = StatisticalRecord(
        hypothesis_identifier=PrimaryHolmHypothesis.COMMON_MODE_FALSE_CAMPAIGN_REDUCTION.value,
        metric_name="false_campaign_reduction",
        method_name=MethodName.FULL_FEDCAMPAIGN_EMHI.value,
        independent_unit_count=len(differences),
        estimate=estimate,
        raw_p_value=raw_p_value,
        adjusted_p_value=None,
        confidence_level=loaded.values.statistics.confidence_level,
        confidence_lower=interval[0],
        confidence_upper=interval[1],
        hodges_lehmann_shift=shift,
        meets_threshold=raw_p_value < loaded.values.statistics.nominal_significance_alpha,
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values),
            source_digests,
        ),
        content_digest=payload_digest(payload),
    )
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    path = root / "statistics" / "tests" / "common-mode-false-campaign-reduction.json"
    write_atomic_json(
        path,
        cast(YamlNode, record.model_dump(mode="json")),
        layout.roots.outputs_root / "cache" / "staging",
    )
    return path


def _apply_client_scaler(
    scaler: ClientFeatureScalerRecord, values: tuple[FeatureValue, ...]
) -> tuple[FeatureValue, ...]:
    return tuple(
        apply_robust_scaler(
            RobustScaler(median=median, iqr=iqr, iqr_floor=scaler.iqr_floor), (value,)
        )[0]
        for median, iqr, value in zip(scaler.medians, scaler.iqrs, values, strict=True)
    )


def _stressed_detector_scores(
    loaded: LoadedScientificConfiguration,
    prepared: PreparedDatasetRecord,
    split: DatasetSplitRecord,
    scores: DetectorScoreArtifactRecord,
    dataset_name: DatasetName,
    root_seed: SeedValue,
    stress_epoch_indexes: tuple[EpochIndexValue, ...],
    factor: RobustnessCountMultiplier,
) -> DetectorScoreArtifactRecord:
    assignments = assign_detector_families(split.selected_client_ids)
    stress_epoch_set = set(stress_epoch_indexes)
    nuisance_epoch_set = set(split.nuisance_fit_epochs)
    scalers_by_client = {scaler.client_id: scaler for scaler in prepared.client_scalers}
    streams: list[ClientDetectorScoreStream] = []
    for assignment in assignments:
        client_rows = tuple(row for row in prepared.epochs if row.client_id == assignment.client_id)
        fit_rows = tuple(
            row.feature_values
            for row in client_rows
            if row.epoch_index in split.detector_fit_epochs
        )
        scaler = scalers_by_client[assignment.client_id]
        stress_rows = tuple(
            _apply_client_scaler(
                scaler, stress_epoch_feature_values(row.unscaled_feature_values, factor)
            )
            for row in client_rows
            if row.epoch_index in stress_epoch_set
        )
        seed = detector_seed(root_seed, dataset_name, assignment.client_id)
        stress_scores = score_client(
            loaded.values, assignment.family, fit_rows, stress_rows, seed, assignment.client_id
        )
        stress_epochs = tuple(
            row.epoch_index for row in client_rows if row.epoch_index in stress_epoch_set
        )
        original_stream = next(
            stream for stream in scores.client_streams if stream.client_id == assignment.client_id
        )
        nuisance_pairs = tuple(
            (epoch, score)
            for epoch, score in zip(
                original_stream.epoch_indexes, original_stream.scores, strict=True
            )
            if epoch in nuisance_epoch_set
        )
        stress_pairs = tuple(zip(stress_epochs, stress_scores, strict=True))
        combined = tuple(sorted((*nuisance_pairs, *stress_pairs)))
        streams.append(
            ClientDetectorScoreStream(
                client_id=assignment.client_id,
                detector_family=assignment.family,
                detector_seed=seed,
                epoch_indexes=tuple(epoch for epoch, _score in combined),
                scores=tuple(score for _epoch, score in combined),
            )
        )
    return DetectorScoreArtifactRecord(
        dataset_name=dataset_name,
        root_seed=root_seed,
        selected_client_ids=split.selected_client_ids,
        client_streams=tuple(streams),
        dependency_fingerprint=scores.dependency_fingerprint,
    )


def _count_stress_false_declaration_rates(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    seed: SeedValue,
    factor: RobustnessCountMultiplier,
) -> tuple[MetricRate, MetricRate, tuple[Path, ...]] | None:
    _inventory_path, prepared_path, split_path, partitions_path, _campaigns_path = (
        preprocessing_paths(loaded, repository, dataset_name)
    )
    prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    partitions = BenignPartitionRecord.model_validate_json(partitions_path.read_bytes())
    stress_windows = tuple(
        BenignHorizon(start_epoch=horizon.start_epoch, epoch_indexes=horizon.epoch_indexes)
        for horizon in partitions.heldout_horizons
    )
    if not stress_windows:
        return None
    stress_epoch_indexes = tuple(
        sorted({epoch for horizon in stress_windows for epoch in horizon.epoch_indexes})
    )
    score_path = materialize_detector_scores_with_retry(loaded, repository, dataset_name, seed)
    rank_path = materialize_marginal_ranks_with_retry(
        loaded, repository, dataset_name, seed, score_path
    )
    scores = DetectorScoreArtifactRecord.model_validate_json(score_path.read_bytes())
    stressed_scores = _stressed_detector_scores(
        loaded, prepared, split, scores, dataset_name, seed, stress_epoch_indexes, factor
    )
    stressed_ranks = build_marginal_rank_artifact(
        stressed_scores,
        split.nuisance_fit_epochs,
        loaded.values.context.rank_clip_epsilon,
        stressed_scores.dependency_fingerprint,
    )
    fit_path = materialize_emhi_fit_with_retry(
        loaded,
        repository,
        dataset_name,
        seed,
        MethodName.FULL_FEDCAMPAIGN_EMHI,
        score_path,
        rank_path,
    )
    fit = EMHIFitArtifactRecord.model_validate_json(fit_path.read_bytes())
    emhi_calibration = calibrate_global_operating_point(
        loaded.values, stressed_ranks, fit, partitions
    )
    trajectory_cache = TrajectoryCache()
    emhi_fcr = _stress_window_false_declaration_rate(
        loaded.values,
        stressed_ranks,
        fit,
        emhi_calibration.threshold,
        stress_windows,
        trajectory_cache,
    )
    raw_scores = comparator_epoch_scores(
        loaded,
        repository,
        stressed_ranks,
        MethodName.RAW_MEAN_RANK_FUSION,
        split.nuisance_fit_epochs,
    )
    comparator_scores = comparator_evidence_scores(loaded, raw_scores, split.nuisance_fit_epochs)
    comparator_threshold, *_rest = calibrate_comparator_operating_point(
        loaded, comparator_scores, partitions
    )
    raw_mean_fcr = _comparator_stress_window_false_declaration_rate(
        comparator_scores, comparator_threshold, stress_windows
    )
    if emhi_fcr is None or raw_mean_fcr is None:
        return None
    return emhi_fcr, raw_mean_fcr, (score_path, rank_path, fit_path)


def materialize_benign_common_mode_count_stress_diagnostics(
    loaded: LoadedScientificConfiguration,
    repository: Path,
) -> tuple[Path, ...]:
    experiment_name = ExperimentName.BENIGN_COMMON_MODE_ROBUSTNESS
    plan = enumerate_benign_common_mode_plan(loaded.values)
    required_methods = {MethodName.FULL_FEDCAMPAIGN_EMHI, MethodName.RAW_MEAN_RANK_FUSION}
    if not required_methods.issubset(plan.methods):
        return ()
    _inventory_path, prepared_path, _split_path, _partitions_path, _campaigns_path = (
        preprocessing_paths(loaded, repository, plan.dataset_name)
    )
    prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
    if not prepared.selected_client_ids:
        return ()
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    staging = layout.roots.outputs_root / "cache" / "staging"
    paths: list[Path] = []
    for factor in loaded.values.robustness.benign_count_multiplication_factors:
        for seed in loaded.values.randomness.real_confirmatory_roots:
            outcome = _count_stress_false_declaration_rates(
                loaded, repository, plan.dataset_name, seed, factor
            )
            if outcome is None:
                continue
            emhi_fcr, raw_mean_fcr, source_paths = outcome
            source_digests = tuple(file_sha256(path) for path in source_paths)
            source_ids = tuple(path.relative_to(repository).as_posix() for path in source_paths)
            payload: YamlNode = {
                "seed": seed,
                "multiplication_factor": factor,
                "emhi_false_declaration_rate": emhi_fcr,
                "raw_mean_false_declaration_rate": raw_mean_fcr,
                "source_result_ids": list(source_ids),
            }
            record = CountStressDiagnosticRecord(
                seed=seed,
                multiplication_factor=factor,
                emhi_false_declaration_rate=emhi_fcr,
                raw_mean_false_declaration_rate=raw_mean_fcr,
                source_result_ids=source_ids,
                dependency_fingerprint=material_fingerprint(
                    statistical_analysis_boundary_digest(loaded.values),
                    source_digests,
                ),
                content_digest=payload_digest(payload),
            )
            path = root / "diagnostics" / "count-stress" / f"factor-{factor}" / f"seed-{seed}.json"
            write_atomic_json(path, cast(YamlNode, record.model_dump(mode="json")), staging)
            paths.append(path)
    return tuple(paths)


def _campaign_detection_rate_for_method(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    dataset_name: DatasetName,
    method_name: MethodName,
    seed: SeedValue,
) -> tuple[MetricRate, tuple[Path, ...]] | None:
    _inventory_path, _prepared_path, split_path, partitions_path, campaigns_path = (
        preprocessing_paths(loaded, repository, dataset_name)
    )
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    partitions = BenignPartitionRecord.model_validate_json(partitions_path.read_bytes())
    campaigns = CampaignRegistryRecord.model_validate_json(campaigns_path.read_bytes())
    score_path = materialize_detector_scores_with_retry(loaded, repository, dataset_name, seed)
    rank_path = materialize_marginal_ranks_with_retry(
        loaded, repository, dataset_name, seed, score_path
    )
    fit_path = materialize_emhi_fit_with_retry(
        loaded,
        repository,
        dataset_name,
        seed,
        method_name,
        score_path,
        rank_path,
    )
    scores = DetectorScoreArtifactRecord.model_validate_json(score_path.read_bytes())
    ranks = MarginalRankArtifactRecord.model_validate_json(rank_path.read_bytes())
    fit = EMHIFitArtifactRecord.model_validate_json(fit_path.read_bytes())
    target_local_pfa = local_pfa_target(loaded, experiment_name)
    calibration = calibrate_operating_points(
        loaded.values,
        scores,
        ranks,
        fit,
        split.nuisance_fit_epochs,
        partitions,
        target_local_pfa,
    )
    rows, _odi_values = build_campaign_rows(loaded, scores, ranks, fit, campaigns, calibration)
    typed_rows = tuple(cast(Mapping[str, YamlNode], row) for row in rows)
    if not typed_rows:
        return None
    relative_stops = tuple(
        None
        if row["global_stop_epoch"] is None
        else cast(EpochIndexValue, row["global_stop_epoch"])
        - cast(EpochIndexValue, row["start_epoch"])
        for row in typed_rows
    )
    detection_rate = campaign_detection_rate(
        relative_stops,
        loaded.values.campaign.evaluation_horizon_epochs,
    )
    return detection_rate, (score_path, rank_path, fit_path)


def materialize_benign_common_mode_positive_power_measurement(
    loaded: LoadedScientificConfiguration,
    repository: Path,
) -> Path | None:
    experiment_name = ExperimentName.BENIGN_COMMON_MODE_ROBUSTNESS
    plan = enumerate_benign_common_mode_plan(loaded.values)
    required_methods = {
        MethodName.FULL_FEDCAMPAIGN_EMHI,
        MethodName.RAW_MEAN_RANK_FUSION,
        MethodName.NO_OUTSIDE_CONTEXT_FULL_HIERARCHY,
    }
    if not required_methods.issubset(plan.methods):
        return None
    _inventory_path, prepared_path, split_path, _partitions_path, _campaigns_path = (
        preprocessing_paths(loaded, repository, plan.dataset_name)
    )
    prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
    if not prepared.selected_client_ids:
        return None
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    horizon_length = loaded.values.campaign.evaluation_horizon_epochs
    all_windows = rolling_benign_horizons(
        split.heldout_benign_epochs, horizon_length, plan.stress_stride_epochs
    )
    if not all_windows:
        return None
    epoch_volumes = tuple(
        EpochEventVolume(
            client_id=epoch.client_id,
            epoch_index=epoch.epoch_index,
            raw_event_count=epoch.raw_event_count,
        )
        for epoch in prepared.epochs
    )
    epoch_totals = federation_wide_epoch_event_counts(epoch_volumes, prepared.selected_client_ids)
    counts = window_event_counts(all_windows, epoch_totals)
    stress_windows = select_high_volume_windows(all_windows, counts, plan.top_event_count_fraction)
    materiality = loaded.values.materiality.benign_common_mode
    floor = loaded.values.numerics.metric_denominator_floor
    power_losses: list[MetricRate] = []
    suppressions: list[MetricRate] = []
    source_paths: list[Path] = []
    covered_seeds: list[SeedValue] = []
    for seed in loaded.values.randomness.real_confirmatory_roots:
        emhi_dr_outcome = _campaign_detection_rate_for_method(
            loaded,
            repository,
            experiment_name,
            plan.dataset_name,
            MethodName.FULL_FEDCAMPAIGN_EMHI,
            seed,
        )
        no_outside_dr_outcome = _campaign_detection_rate_for_method(
            loaded,
            repository,
            experiment_name,
            plan.dataset_name,
            MethodName.NO_OUTSIDE_CONTEXT_FULL_HIERARCHY,
            seed,
        )
        fcr_outcome = _benign_common_mode_seed_fcr(
            loaded, repository, plan.dataset_name, seed, stress_windows
        )
        if emhi_dr_outcome is None or no_outside_dr_outcome is None or fcr_outcome is None:
            continue
        emhi_dr, emhi_dr_paths = emhi_dr_outcome
        no_outside_dr, no_outside_dr_paths = no_outside_dr_outcome
        emhi_fcr, raw_mean_fcr, fcr_paths = fcr_outcome
        power_losses.append(outside_conditioning_power_loss(no_outside_dr, emhi_dr))
        suppressions.append(common_mode_suppression(emhi_fcr, raw_mean_fcr, floor))
        source_paths.extend((*emhi_dr_paths, *no_outside_dr_paths, *fcr_paths))
        covered_seeds.append(seed)
    if not confirmatory_completeness_within_tolerance(
        loaded, loaded.values.randomness.real_confirmatory_roots, tuple(covered_seeds)
    ):
        return None
    mean_power_loss = sum(power_losses) / len(power_losses)
    mean_suppression = sum(suppressions) / len(suppressions)
    source_digests = tuple(file_sha256(path) for path in source_paths)
    source_ids = tuple(path.relative_to(repository).as_posix() for path in source_paths)
    payload: YamlNode = {
        "independent_unit_count": len(covered_seeds),
        "mean_detection_rate_power_loss": mean_power_loss,
        "mean_common_mode_suppression": mean_suppression,
        "source_result_ids": list(source_ids),
    }
    record = BenignCommonModePositivePowerMeasurementRecord(
        independent_unit_count=len(covered_seeds),
        mean_detection_rate_power_loss=mean_power_loss,
        detection_rate_loss_within_maximum=detection_rate_loss_within_maximum(
            mean_power_loss, materiality.maximum_detection_rate_loss
        ),
        mean_common_mode_suppression=mean_suppression,
        false_campaign_suppression_meets_minimum=false_campaign_suppression_meets_minimum(
            mean_suppression, materiality.minimum_false_campaign_suppression
        ),
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values),
            source_digests,
        ),
        content_digest=payload_digest(payload),
    )
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    path = root / "diagnostics" / "positive-power" / "measurement.json"
    write_atomic_json(
        path,
        cast(YamlNode, record.model_dump(mode="json")),
        layout.roots.outputs_root / "cache" / "staging",
    )
    return path
