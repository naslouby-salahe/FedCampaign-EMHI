import math
import statistics
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import numpy as np

from fedcampaign_emhi.artifacts.records import (
    BenignHorizonRecord,
    BenignPartitionRecord,
    ClientDetectorScoreStream,
    DatasetSplitRecord,
    DetectorScoreArtifactRecord,
    EMHIFitArtifactRecord,
    MarginalRankArtifactRecord,
    ProjectionCellFitRecord,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration, ScientificConfig
from fedcampaign_emhi.detection import (
    FittedClientDetector,
    assign_detector_families,
    first_local_stop_epoch,
    fit_client_detector,
    score_exceeds_threshold,
    score_fitted_client_detector,
)
from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    ContextMethodName,
    DatasetName,
    ExperimentName,
    ExperimentState,
    MethodName,
    SupportState,
)
from fedcampaign_emhi.domain.types import (
    Boolean,
    ByteCount,
    ClientCount,
    ClientId,
    EpochIndexValue,
    FeatureDimension,
    FeatureValue,
    LatencySeconds,
    LocalPolicyArtifact,
    Percentile,
    Probability,
    RecordCount,
    SeedCoordinate,
    SeedDerivationIdentity,
    SeedValue,
    ThresholdValue,
)
from fedcampaign_emhi.emhi.calibration import build_emhi_fit_artifact
from fedcampaign_emhi.emhi.sequential import initial_global_state
from fedcampaign_emhi.emhi.structure import build_marginal_rank_artifact
from fedcampaign_emhi.evaluation.metrics import application_payload_bytes_per_epoch
from fedcampaign_emhi.evaluation.records import ClientLocalOperatingPoint
from fedcampaign_emhi.evaluation.sequential import (
    advance_operational_epoch,
    calibrate_client_local_operating_point,
    calibrate_global_operating_point,
    scores_for_epochs,
)
from fedcampaign_emhi.runtime import (
    derive_component_seed,
    deterministic_digest,
    log_stage,
    thirty_two_bit_seed,
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
    local_timing_operating_point_available: Boolean
    global_timing_operating_point_available: Boolean
    artifact_fit_seconds: LatencySeconds


@dataclass(frozen=True)
class ScalabilitySummary:
    client_count: ClientCount
    median_server_latency_seconds: LatencySeconds
    p95_server_latency_seconds: LatencySeconds
    median_end_to_end_latency_seconds: LatencySeconds
    p95_end_to_end_latency_seconds: LatencySeconds
    peak_rss_bytes: ByteCount
    application_payload_bytes: ByteCount
    numerical_failure_rate: Probability
    latency_criterion_state: SupportState
    numerical_criterion_state: SupportState
    local_timing_operating_point_available: Boolean
    global_timing_operating_point_available: Boolean
    artifact_fit_seconds: LatencySeconds
    state: ExperimentState


def scalability_client_ids(client_count: ClientCount) -> tuple[ClientId, ...]:
    return tuple(f"client-{index:03d}" for index in range(client_count))


def latency_quantile(latencies: tuple[LatencySeconds, ...], quantile: Percentile) -> LatencySeconds:
    if not latencies:
        raise ValueError("latency quantile requires at least one measurement")
    return float(np.quantile(np.asarray(latencies, dtype=np.float64), quantile))


def seed_level_latency_quantiles(
    measurements: tuple[ScalabilityMeasurement, ...],
    latency_of: Callable[[ScalabilityMeasurement], LatencySeconds],
    quantile: Percentile,
) -> tuple[LatencySeconds, ...]:
    seeds = tuple(dict.fromkeys(row.seed for row in measurements))
    return tuple(
        latency_quantile(
            tuple(latency_of(row) for row in measurements if row.seed == seed),
            quantile,
        )
        for seed in seeds
    )


def measure_repetition_epoch_latencies(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    scores: DetectorScoreArtifactRecord,
    local_points: tuple[ClientLocalOperatingPoint, ...],
    epoch_indexes: tuple[EpochIndexValue, ...],
    threshold: ThresholdValue,
    fitted_detectors: tuple[FittedClientDetector, ...],
    client_features: tuple[tuple[tuple[FeatureValue, ...], ...], ...],
) -> tuple[tuple[LatencySeconds, LatencySeconds], ...]:
    state = initial_global_state()
    history: tuple[tuple[ClientId, ...], ...] = ()
    exceedances: tuple[tuple[Boolean, ...], ...] = tuple(() for _point in local_points)
    timed: list[tuple[LatencySeconds, LatencySeconds]] = []
    for epoch_index in epoch_indexes:
        end_to_end_started = perf_counter()
        for fitted, features in zip(fitted_detectors, client_features, strict=True):
            score_fitted_client_detector(fitted, (features[epoch_index],))
        server_started = perf_counter()
        advance = advance_operational_epoch(
            config,
            ranks,
            fit,
            epoch_index,
            state,
            history,
            threshold,
        )
        server_elapsed = perf_counter() - server_started
        updated: list[tuple[Boolean, ...]] = []
        for point, client_exceedances in zip(local_points, exceedances, strict=True):
            policy = point.policy
            if policy is None:
                updated.append(client_exceedances)
                continue
            score = scores_for_epochs(scores, point.client_id, (epoch_index,))[0]
            next_exceedances = (
                *client_exceedances,
                score_exceeds_threshold(score, policy.threshold),
            )
            first_local_stop_epoch(
                next_exceedances,
                policy.required_exceedances,
                policy.window_epochs,
            )
            updated.append(next_exceedances)
        exceedances = tuple(updated)
        timed.append((server_elapsed, perf_counter() - end_to_end_started))
        state = advance.global_state
        history = advance.active_history
    return tuple(timed)


def resident_set_bytes() -> ByteCount:
    status_path = Path("/proc/self/status")
    if status_path.is_file():
        for line in status_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) << 10
    return 0


def summarize_scalability(
    client_count: ClientCount,
    measurements: tuple[ScalabilityMeasurement, ...],
    maximum_p95_end_to_end_latency_seconds: LatencySeconds,
    maximum_numerical_failure_rate: Probability,
    result_quantile: Percentile,
) -> ScalabilitySummary:
    selected = tuple(row for row in measurements if row.client_count == client_count)
    if not selected:
        raise ValueError("scalability summary requires matching measurements")
    server = tuple(row.server_latency_seconds for row in selected)
    end_to_end = tuple(row.end_to_end_latency_seconds for row in selected)
    seed_p95_server = seed_level_latency_quantiles(
        selected, lambda row: row.server_latency_seconds, result_quantile
    )
    seed_p95_end_to_end = seed_level_latency_quantiles(
        selected, lambda row: row.end_to_end_latency_seconds, result_quantile
    )
    failure_count = sum(row.numerical_failure_count for row in selected)
    attempted_count = sum(row.attempted_cell_count for row in selected)
    if attempted_count <= 0:
        raise ValueError("scalability summary requires attempted scientific cells")
    failure_rate = failure_count / attempted_count
    end_to_end_quantile = latency_quantile(seed_p95_end_to_end, result_quantile)
    latency_passed = end_to_end_quantile <= maximum_p95_end_to_end_latency_seconds
    failure_passed = failure_rate <= maximum_numerical_failure_rate
    return ScalabilitySummary(
        client_count=client_count,
        median_server_latency_seconds=statistics.median(server),
        p95_server_latency_seconds=latency_quantile(seed_p95_server, result_quantile),
        median_end_to_end_latency_seconds=statistics.median(end_to_end),
        p95_end_to_end_latency_seconds=end_to_end_quantile,
        peak_rss_bytes=max(row.peak_rss_bytes for row in selected),
        application_payload_bytes=max(row.application_payload_bytes for row in selected),
        numerical_failure_rate=failure_rate,
        latency_criterion_state=SupportState.SUPPORTED
        if latency_passed
        else SupportState.NOT_SUPPORTED,
        numerical_criterion_state=SupportState.SUPPORTED
        if failure_passed
        else SupportState.NOT_SUPPORTED,
        local_timing_operating_point_available=all(
            row.local_timing_operating_point_available for row in selected
        ),
        global_timing_operating_point_available=all(
            row.global_timing_operating_point_available for row in selected
        ),
        artifact_fit_seconds=max(row.artifact_fit_seconds for row in selected),
        state=ExperimentState.COMPLETED,
    )


def expected_scalability_coalitions(
    config: ScientificConfig, client_count: ClientCount
) -> RecordCount:
    maximum_order = config.study.maximum_coalition_order
    if maximum_order > client_count:
        raise ValueError("maximum coalition order cannot exceed the client count")
    return sum(math.comb(client_count, order) for order in range(1, maximum_order + 1))


def generate_scalability_feature_rows(
    config: ScientificConfig,
    client_count: ClientCount,
    epoch_count: RecordCount,
    feature_dimension: FeatureDimension,
    seed: SeedValue,
) -> tuple[tuple[tuple[FeatureValue, ...], ...], ...]:
    common = config.generators.common_mode
    latent_seed = derive_component_seed(
        SeedDerivationIdentity(
            base_seed=seed,
            component_name="scalability-latent",
            dataset=None,
            client_ids=(),
            coalition_ids=(),
            condition_coordinates=(SeedCoordinate(name="client-count", scalar=client_count),),
        )
    )
    latent_generator = np.random.default_rng(thirty_two_bit_seed(latent_seed))
    rho = common.latent_ar_coefficient
    innovation_scale = math.sqrt(1.0 - (rho**2))
    latent = float(latent_generator.standard_normal())
    latents = [latent]
    for _epoch in range(max(0, epoch_count - 1)):
        latent = (rho * latent) + (innovation_scale * float(latent_generator.standard_normal()))
        latents.append(latent)
    span = common.client_loading_maximum - common.client_loading_minimum
    denominator = max(client_count - 1, 1)
    client_rows: list[tuple[tuple[FeatureValue, ...], ...]] = []
    for client_index in range(client_count):
        loading = common.client_loading_minimum + (span * client_index / denominator)
        feature_seed = derive_component_seed(
            SeedDerivationIdentity(
                base_seed=seed,
                component_name="scalability-features",
                dataset=None,
                client_ids=(),
                coalition_ids=(),
                condition_coordinates=(SeedCoordinate(name="client-index", scalar=client_index),),
            )
        )
        feature_generator = np.random.default_rng(thirty_two_bit_seed(feature_seed))
        rows: list[tuple[FeatureValue, ...]] = []
        for latent_value in latents:
            first = (loading * latent_value) + (
                common.client_noise_standard_deviation * float(feature_generator.standard_normal())
            )
            remaining = tuple(
                float(feature_generator.standard_normal())
                for _feature in range(feature_dimension - 1)
            )
            rows.append((first, *remaining))
        client_rows.append(tuple(rows))
    return tuple(client_rows)


def _projection_numerical_failures(
    fit: EMHIFitArtifactRecord,
) -> tuple[RecordCount, RecordCount]:
    cells: tuple[ProjectionCellFitRecord, ...] = tuple(
        cell for coalition in fit.coalition_fits for cell in coalition.cells
    )
    attempted = len(cells)
    failed = sum(1 for cell in cells if cell.numerical_failure)
    return failed, attempted


def _stringent_local_policy(config: ScientificConfig) -> LocalPolicyArtifact:
    persistence = max(
        config.local_policy.candidate_persistence,
        key=lambda item: (item.required_exceedances, item.window_epochs),
    )
    return LocalPolicyArtifact(
        threshold=max(config.local_policy.candidate_score_quantiles),
        required_exceedances=persistence.required_exceedances,
        window_epochs=persistence.window_epochs,
    )


@log_stage("evaluation.scalability")
def collect_scalability_measurements(
    loaded: LoadedScientificConfiguration,
    client_count: ClientCount,
    seed: SeedValue,
) -> tuple[ScalabilityMeasurement, ...]:
    config = loaded.values
    timing = config.scalability_timing
    if timing.concurrent_experiment_cells != 1:
        raise ValueError("reference-harness concurrency must equal concurrent_experiment_cells")
    client_ids = scalability_client_ids(client_count)
    nuisance_count = config.synthetic.sample_sizes.generic_nuisance_fit_epochs
    warmup = timing.unmeasured_harness_warmup_epochs
    measured = timing.measured_epochs_per_repetition
    calibration_count = config.synthetic.sample_sizes.finite_horizon_calibration_horizons_per_seed
    horizon = config.campaign.evaluation_horizon_epochs
    campaign_warmup = config.campaign.prestart_warmup_epochs
    calibration_length = campaign_warmup + horizon
    total_epochs = (
        nuisance_count
        + nuisance_count
        + (calibration_count * calibration_length)
        + warmup
        + measured
    )
    fit_started = perf_counter()
    features = generate_scalability_feature_rows(
        config,
        client_count,
        total_epochs,
        loaded.derived.model_input_dimension,
        seed,
    )
    assignments = assign_detector_families(client_ids)
    fingerprint = deterministic_digest(
        {
            "producer": ExperimentName.COALITION_SCALABILITY.value,
            "seed": seed,
            "client_count": client_count,
        }
    )
    epochs = tuple(range(total_epochs))
    streams: list[ClientDetectorScoreStream] = []
    fitted_detectors: list[FittedClientDetector] = []
    for assignment, client_features in zip(assignments, features, strict=True):
        detector_seed = derive_component_seed(
            SeedDerivationIdentity(
                base_seed=seed,
                component_name="local-detector-fit",
                dataset=None,
                client_ids=(assignment.client_id,),
                coalition_ids=(),
                condition_coordinates=(),
            )
        )
        fitted = fit_client_detector(
            config,
            assignment.family,
            client_features[:nuisance_count],
            detector_seed,
            assignment.client_id,
        )
        fitted_detectors.append(fitted)
        scores = score_fitted_client_detector(fitted, client_features)
        streams.append(
            ClientDetectorScoreStream(
                client_id=assignment.client_id,
                detector_family=assignment.family,
                detector_seed=detector_seed,
                epoch_indexes=epochs,
                scores=scores,
            )
        )
    score_artifact = DetectorScoreArtifactRecord(
        dataset_name=DatasetName.TON_IOT_NETWORK,
        root_seed=seed,
        selected_client_ids=client_ids,
        client_streams=tuple(streams),
        dependency_fingerprint=fingerprint,
    )
    nuisance_epochs = tuple(range(nuisance_count, 2 * nuisance_count))
    split = DatasetSplitRecord(
        dataset_name=DatasetName.TON_IOT_NETWORK,
        selected_client_ids=client_ids,
        eligible_client_ids=client_ids,
        support_state=SupportState.SUPPORTED,
        detector_fit_epochs=tuple(range(nuisance_count)),
        nuisance_fit_epochs=nuisance_epochs,
        threshold_calibration_epochs=(),
        heldout_benign_epochs=(),
    )
    ranks = build_marginal_rank_artifact(
        score_artifact, nuisance_epochs, config.context.rank_clip_epsilon, fingerprint
    )
    fit = build_emhi_fit_artifact(
        config,
        score_artifact,
        ranks,
        split,
        MethodName.FULL_FEDCAMPAIGN_EMHI,
        ContextMethodName.EXACT_COALITION_EXCLUSION,
        CoalitionOrder(config.study.maximum_coalition_order),
        config.basis.primary_size,
        config.context.primary_cell_count,
        True,
        False,
        fingerprint,
    )
    failed, attempted = _projection_numerical_failures(fit)
    calibration_start = 2 * nuisance_count
    calibration_horizons = tuple(
        BenignHorizonRecord(
            start_epoch=calibration_start + (index * calibration_length) + campaign_warmup,
            epoch_indexes=tuple(
                range(
                    calibration_start + (index * calibration_length) + campaign_warmup,
                    calibration_start + ((index + 1) * calibration_length),
                )
            ),
        )
        for index in range(calibration_count)
    )
    partitions = BenignPartitionRecord(
        dataset_name=DatasetName.TON_IOT_NETWORK,
        calibration_horizons=calibration_horizons,
        heldout_horizons=(),
    )
    global_operating = calibrate_global_operating_point(config, ranks, fit, partitions)
    selected_threshold: ThresholdValue
    if global_operating.threshold is None:
        selected_threshold = max(config.evidence.calibrated_finite_horizon.threshold_candidates)
        global_available = False
    else:
        selected_threshold = global_operating.threshold
        global_available = True
    local_points = tuple(
        calibrate_client_local_operating_point(
            config,
            score_artifact,
            client_id,
            nuisance_epochs,
            partitions,
            config.evidence.calibrated_finite_horizon.target_pfa,
        )
        for client_id in client_ids
    )
    local_available = all(point.policy is not None for point in local_points)
    if not local_available:
        fallback = _stringent_local_policy(config)
        local_points = tuple(
            point
            if point.policy is not None
            else ClientLocalOperatingPoint(
                client_id=point.client_id,
                policy=fallback,
                calibration_false_stop_count=point.calibration_false_stop_count,
                heldout_false_stop_count=point.heldout_false_stop_count,
                heldout_horizon_count=point.heldout_horizon_count,
                heldout_upper_pfa=point.heldout_upper_pfa,
            )
            for point in local_points
        )
    warmup_start = calibration_start + (calibration_count * calibration_length)
    measured_start = warmup_start + warmup
    warmup_epochs = tuple(range(warmup_start, measured_start))
    measured_epochs = tuple(range(measured_start, measured_start + measured))
    artifact_fit_seconds = perf_counter() - fit_started
    peak = resident_set_bytes()
    fitted = tuple(fitted_detectors)
    measure_repetition_epoch_latencies(
        config,
        ranks,
        fit,
        score_artifact,
        local_points,
        warmup_epochs,
        selected_threshold,
        fitted,
        features,
    )
    peak = max(peak, resident_set_bytes())
    payload_bytes = application_payload_bytes_per_epoch(client_count)
    measurements: list[ScalabilityMeasurement] = []
    for repetition in range(timing.measured_repetitions_per_seed_client_count):
        epoch_latencies = measure_repetition_epoch_latencies(
            config,
            ranks,
            fit,
            score_artifact,
            local_points,
            measured_epochs,
            selected_threshold,
            fitted,
            features,
        )
        peak = max(peak, resident_set_bytes())
        for server_elapsed, end_to_end_elapsed in epoch_latencies:
            measurements.append(
                ScalabilityMeasurement(
                    client_count=client_count,
                    seed=seed,
                    repetition=repetition,
                    server_latency_seconds=server_elapsed,
                    end_to_end_latency_seconds=end_to_end_elapsed,
                    peak_rss_bytes=peak,
                    application_payload_bytes=payload_bytes,
                    numerical_failure_count=failed,
                    attempted_cell_count=attempted,
                    local_timing_operating_point_available=local_available,
                    global_timing_operating_point_available=global_available,
                    artifact_fit_seconds=artifact_fit_seconds,
                )
            )
    return tuple(measurements)
