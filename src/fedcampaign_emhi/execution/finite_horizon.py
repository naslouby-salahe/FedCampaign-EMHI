from dataclasses import dataclass

from fedcampaign_emhi.artifacts.records import (
    BenignHorizonRecord,
    BenignPartitionRecord,
    ClientDetectorScoreStream,
    DatasetSplitRecord,
    DetectorScoreArtifactRecord,
)
from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import (
    ClaimState,
    CoalitionOrder,
    ContextMethodName,
    DatasetName,
    DetectorFamily,
    MethodName,
)
from fedcampaign_emhi.domain.types import (
    ClientCount,
    ClientId,
    ComponentName,
    FiniteFloat,
    PositiveEpochCount,
    RecordCount,
    SeedCoordinate,
    SeedDerivationIdentity,
    SeedValue,
)
from fedcampaign_emhi.emhi.innovation_calibration import build_emhi_fit_artifact
from fedcampaign_emhi.emhi.ranks import build_marginal_rank_artifact
from fedcampaign_emhi.evaluation.benign_horizons import calibrate_global_operating_point
from fedcampaign_emhi.runtime.determinism import canonical_digest, derive_component_seed
from fedcampaign_emhi.synthetic.common_mode import (
    equally_spaced_loadings,
    generate_common_mode_scores,
    generate_unit_variance_autoregressive_latent,
)


@dataclass(frozen=True)
class FiniteHorizonSeedMetrics:
    calibrated_threshold: FiniteFloat | None
    calibration_horizon_count: RecordCount
    heldout_horizon_count: RecordCount
    heldout_false_stop_count: RecordCount
    heldout_upper_pfa: FiniteFloat | None


@dataclass(frozen=True)
class FiniteHorizonSeedResult:
    metrics: FiniteHorizonSeedMetrics
    assumptions_hold: bool


def _seed(seed: SeedValue, component: ComponentName, horizon: SeedValue) -> SeedValue:
    return derive_component_seed(
        SeedDerivationIdentity(
            base_seed=seed,
            component_name=component,
            dataset=None,
            client_ids=(),
            coalition_ids=(),
            condition_coordinates=(SeedCoordinate(name="horizon", scalar=horizon),),
        )
    )


def _block(
    config: ScientificConfig,
    client_count: ClientCount,
    epoch_count: PositiveEpochCount,
    seed: SeedValue,
) -> tuple[tuple[FiniteFloat, ...], ...]:
    latent = generate_unit_variance_autoregressive_latent(
        epoch_count, config.generators.common_mode.latent_ar_coefficient, _seed(seed, "latent", 0)
    )
    return generate_common_mode_scores(
        latent,
        equally_spaced_loadings(
            client_count,
            config.generators.common_mode.client_loading_minimum,
            config.generators.common_mode.client_loading_maximum,
        ),
        config.generators.common_mode.client_noise_standard_deviation,
        _seed(seed, "noise", 0),
    )


def evaluate_finite_horizon_common_mode_seed(
    config: ScientificConfig, seed: SeedValue
) -> FiniteHorizonSeedResult:
    client_count = config.experiments.pure_order_separation_validation.primary_client_count
    client_ids: tuple[ClientId, ...] = tuple(
        f"synthetic-common-mode-client-{index}" for index in range(client_count)
    )
    nuisance_count = config.synthetic.sample_sizes.generic_nuisance_fit_epochs
    warmup, length = (
        config.campaign.prestart_warmup_epochs,
        config.campaign.evaluation_horizon_epochs,
    )
    calibration_count = config.synthetic.sample_sizes.finite_horizon_calibration_horizons_per_seed
    heldout_count = config.synthetic.sample_sizes.finite_horizon_heldout_null_horizons_per_seed
    specifications = tuple((True, index) for index in range(calibration_count)) + tuple(
        (False, index) for index in range(heldout_count)
    )
    blocks = [_block(config, client_count, nuisance_count, _seed(seed, "nuisance", 0))]
    blocks.extend(
        _block(
            config,
            client_count,
            warmup + length,
            _seed(seed, "calibration" if calibration else "heldout", index),
        )
        for calibration, index in specifications
    )
    rows = tuple(row for block in blocks for row in block)
    indexes = tuple(range(len(rows)))
    fingerprint = canonical_digest(
        {"producer": "finite-horizon-common-mode", "seed": seed, "client_count": client_count}
    )
    scores = DetectorScoreArtifactRecord(
        dataset_name=DatasetName.TON_IOT_NETWORK,
        root_seed=seed,
        selected_client_ids=client_ids,
        client_streams=tuple(
            ClientDetectorScoreStream(
                client_id=client_id,
                detector_family=DetectorFamily.ISOLATION_FOREST,
                detector_seed=seed,
                epoch_indexes=indexes,
                scores=tuple(row[index] for row in rows),
            )
            for index, client_id in enumerate(client_ids)
        ),
        dependency_fingerprint=fingerprint,
    )
    nuisance_epochs = tuple(range(nuisance_count))
    split = DatasetSplitRecord(
        dataset_name=DatasetName.TON_IOT_NETWORK,
        selected_client_ids=client_ids,
        eligible_client_ids=client_ids,
        claim_state=ClaimState.SUPPORTED,
        detector_fit_epochs=nuisance_epochs,
        nuisance_fit_epochs=nuisance_epochs,
        threshold_calibration_epochs=(),
        heldout_benign_epochs=(),
    )
    ranks = build_marginal_rank_artifact(
        scores, nuisance_epochs, config.context.rank_clip_epsilon, fingerprint
    )
    fit = build_emhi_fit_artifact(
        config,
        scores,
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
    offset = nuisance_count
    calibration_horizons: list[BenignHorizonRecord] = []
    heldout_horizons: list[BenignHorizonRecord] = []
    for calibration, _index in specifications:
        scored = tuple(range(offset + warmup, offset + warmup + length))
        (calibration_horizons if calibration else heldout_horizons).append(
            BenignHorizonRecord(start_epoch=scored[0], epoch_indexes=scored)
        )
        offset += warmup + length
    operating = calibrate_global_operating_point(
        config,
        ranks,
        fit,
        BenignPartitionRecord(
            dataset_name=DatasetName.TON_IOT_NETWORK,
            calibration_horizons=tuple(calibration_horizons),
            heldout_horizons=tuple(heldout_horizons),
        ),
    )
    metrics = FiniteHorizonSeedMetrics(
        calibrated_threshold=operating.threshold,
        calibration_horizon_count=operating.calibration_horizon_count,
        heldout_horizon_count=operating.heldout_horizon_count,
        heldout_false_stop_count=operating.heldout_false_stop_count,
        heldout_upper_pfa=operating.heldout_upper_pfa,
    )
    return FiniteHorizonSeedResult(
        metrics=metrics,
        assumptions_hold=(
            metrics.calibration_horizon_count == calibration_count
            and metrics.heldout_horizon_count == heldout_count
            and (metrics.calibrated_threshold is None or metrics.heldout_upper_pfa is not None)
        ),
    )
