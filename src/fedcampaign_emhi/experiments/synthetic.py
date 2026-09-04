from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt
from pathlib import Path
from time import perf_counter

from fedcampaign_emhi.artifacts.records import (
    BenignHorizonRecord,
    BenignPartitionRecord,
    ClientDetectorScoreStream,
    ClientMarginalRankStream,
    DatasetSplitRecord,
    DetectorScoreArtifactRecord,
    EMHIFitArtifactRecord,
    MarginalRankArtifactRecord,
)
from fedcampaign_emhi.comparators.contracts import native_target_order
from fedcampaign_emhi.comparators.dependence import (
    cosine_equivalence_criterion,
    nrmse_equivalence_criterion,
    pfa_prerequisite_criterion,
)
from fedcampaign_emhi.comparators.runtime import fit_comparator_state, score_comparator_ranks
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration, ScientificConfig
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    ContextMethodName,
    DatasetName,
    DetectorFamily,
    ExecutionRole,
    ExperimentName,
    GeneratorName,
    MethodName,
)
from fedcampaign_emhi.domain.types import (
    AttenuationDifference,
    BasisSize,
    Boolean,
    ClientCount,
    ClientId,
    ComponentName,
    DetectorScore,
    EffectCoefficient,
    EpochCount,
    EpochIndexValue,
    EvidenceFactor,
    InnovationCoordinate,
    InnovationDeviation,
    InnovationMean,
    NuisanceCoefficient,
    NumericalFloor,
    OperationalNormReference,
    Probability,
    ProjectionNrmse,
    RankValue,
    RecordCount,
    ScoreShift,
    SeedValue,
    StandardizedDrift,
    StoppingTimeDifferenceEpochs,
    ThresholdValue,
)
from fedcampaign_emhi.emhi.calibration import (
    build_emhi_fit_artifact,
    calibrate_innovations_on_nuisance_fit,
    moments_from_held_fold_innovations,
)
from fedcampaign_emhi.emhi.evidence import (
    operational_evidence_factor,
    operational_norm_reference_quantile,
)
from fedcampaign_emhi.emhi.innovations import center_and_scale_atom, projection_residual
from fedcampaign_emhi.emhi.projection import proper_subset_design_row, ridge_coefficient_matrix
from fedcampaign_emhi.emhi.sequential import (
    initial_global_state,
    next_global_state,
    threshold_predicate,
)
from fedcampaign_emhi.emhi.structure import build_marginal_rank_artifact, tensor_representation
from fedcampaign_emhi.emhi.thresholds import (
    clopper_pearson_one_sided_upper_bound,
    select_calibrated_threshold,
)
from fedcampaign_emhi.evaluation.metrics import (
    abstention_rate,
    atom_cosine_similarity,
    atom_nrmse,
    campaign_detection_rate,
    paired_detection_indicator_difference,
    paired_stopping_time_difference,
    target_order_drift,
)
from fedcampaign_emhi.evaluation.scalability import scalability_client_ids
from fedcampaign_emhi.evaluation.sequential import (
    CalibratedGlobalOperatingPoint,
    calibrate_global_operating_point,
    coalition_evidence_at_epoch,
    global_stop_epoch,
    sequential_trajectory,
    trajectory_context_coverage,
)
from fedcampaign_emhi.runtime import deterministic_digest, log_stage
from fedcampaign_emhi.synthetic.feasibility import (
    EstimatorFeasibilityMetrics,
    evaluate_estimator_feasibility_seed,
    primary_feasibility_context_support,
)
from fedcampaign_emhi.synthetic.generators import (
    availability_mask,
    contaminate_rank,
    contaminated_outside_clients,
    dropout_coalition_is_active,
    outside_contamination_targets,
)
from fedcampaign_emhi.synthetic.pure_order import (
    PureOrderCell,
    enumerate_pure_order_grid,
    sample_generator_row,
    sample_independent_uniform_ranks,
    sample_mixed_order_ranks,
    validate_generator_purity,
)
from fedcampaign_emhi.synthetic.self_explanation import (
    evaluate_self_explanation_seed,
    exact_nuisance_derivative_within_margin,
    material_attenuation_criterion,
)
from fedcampaign_emhi.synthetic.sequential import (
    SignedTheoremSeedMetrics,
    evaluate_signed_theorem_seed,
)


@dataclass(frozen=True)
class SelfExplanationObservation:
    execution_role: ExecutionRole
    seed: SeedValue
    metric: SelfExplanationSeedMetrics
    diagnostic_path: Path


@dataclass(frozen=True)
class PureOrderObservation:
    execution_role: ExecutionRole
    seed: SeedValue
    metric: PureOrderSeedMetrics
    diagnostic_path: Path


@dataclass(frozen=True)
class EstimatorFeasibilityObservation:
    execution_role: ExecutionRole
    seed: SeedValue
    metric: EstimatorFeasibilitySeedMetrics
    diagnostic_path: Path


@dataclass(frozen=True)
class SelfExplanationSeedMetrics:
    primary_exact_nuisance_derivative: EffectCoefficient
    primary_attenuation_contrast: AttenuationDifference


@dataclass(frozen=True)
class PureOrderSeedMetrics:
    maximum_proper_subset_standardized_drift: StandardizedDrift
    target_order_standardized_drift: StandardizedDrift


@dataclass(frozen=True)
class EstimatorFeasibilitySeedMetrics:
    primary: EstimatorFeasibilityMetrics


@dataclass(frozen=True)
class HofdEquivalenceConditionMetrics:
    coalition_order: CoalitionOrder
    support_per_context: RecordCount
    atom_nrmse: ProjectionNrmse
    atom_cosine_similarity: Probability
    stopping_time_difference: StoppingTimeDifferenceEpochs | None
    detection_indicator_difference: Probability
    pfa_prerequisite_passes: Boolean


@dataclass(frozen=True)
class HofdEquivalenceSeedMetrics:
    conditions: tuple[HofdEquivalenceConditionMetrics, ...]


@dataclass(frozen=True)
class HofdEquivalenceObservation:
    execution_role: ExecutionRole
    seed: SeedValue
    metric: HofdEquivalenceSeedMetrics
    diagnostic_path: Path


@dataclass(frozen=True)
class SyntheticCellOutcome:
    failed_checks: tuple[ComponentName, ...]
    method_score: DetectorScore | None
    evidence: YamlNode = None
    self_explanation_metrics: SelfExplanationSeedMetrics | None = None
    pure_order_metrics: PureOrderSeedMetrics | None = None
    signed_theorem_metrics: SignedTheoremSeedMetrics | None = None
    estimator_feasibility_metrics: EstimatorFeasibilitySeedMetrics | None = None
    hofd_metrics: HofdEquivalenceSeedMetrics | None = None


def _pure_polynomial_generator(order: CoalitionOrder) -> GeneratorName:
    if order is CoalitionOrder.ONE:
        return GeneratorName.PURE_ORDER_ONE
    if order is CoalitionOrder.TWO:
        return GeneratorName.PURE_ORDER_TWO
    return GeneratorName.PURE_CONTINUOUS_TRIPLE


def _standardized_atoms_for_rows(
    rows: tuple[tuple[RankValue, ...], ...],
    coefficients: tuple[tuple[NuisanceCoefficient, ...], ...],
    means: tuple[InnovationMean, ...],
    deviations: tuple[InnovationDeviation, ...],
    basis_size: BasisSize,
    scale_floor: NumericalFloor,
) -> tuple[tuple[InnovationCoordinate, ...], ...]:
    atoms: list[tuple[InnovationCoordinate, ...]] = []
    for row in rows:
        tensor = tensor_representation(row, basis_size)
        design = proper_subset_design_row(row, basis_size)
        residual = projection_residual(tensor, coefficients, design)
        atoms.append(center_and_scale_atom(residual, means, deviations, scale_floor))
    return tuple(atoms)


def _operational_factors_for_rows(
    rows: tuple[tuple[RankValue, ...], ...],
    coefficients: tuple[tuple[NuisanceCoefficient, ...], ...],
    means: tuple[InnovationMean, ...],
    deviations: tuple[InnovationDeviation, ...],
    norm_reference: OperationalNormReference,
    basis_size: BasisSize,
    config: ScientificConfig,
) -> tuple[EvidenceFactor, ...]:
    atoms = _standardized_atoms_for_rows(
        rows,
        coefficients,
        means,
        deviations,
        basis_size,
        config.projection.atom_scale_floor,
    )
    return tuple(
        operational_evidence_factor(
            atom,
            norm_reference,
            config.projection.norm_reference_floor,
            config.evidence.clip_bound,
            config.evidence.bet_lambda,
        )
        for atom in atoms
    )


def _first_eprocess_stop(
    factors: tuple[EvidenceFactor, ...], threshold: ThresholdValue
) -> EpochIndexValue | None:
    state = initial_global_state()
    for index, factor in enumerate(factors):
        state = next_global_state(state, factor)
        if threshold_predicate(state, threshold):
            return index
    return None


def _calibrate_eprocess_threshold(
    calibration_horizons: tuple[tuple[EvidenceFactor, ...], ...],
    heldout_horizons: tuple[tuple[EvidenceFactor, ...], ...],
    config: ScientificConfig,
) -> tuple[ThresholdValue | None, Probability | None, RecordCount]:
    candidates = config.evidence.calibrated_finite_horizon.threshold_candidates
    stop_counts = tuple(
        sum(
            1
            for horizon in calibration_horizons
            if _first_eprocess_stop(horizon, candidate) is not None
        )
        for candidate in candidates
    )
    selected = select_calibrated_threshold(
        candidates,
        stop_counts,
        len(calibration_horizons),
        config.evidence.calibrated_finite_horizon.calibration_confidence,
        config.evidence.calibrated_finite_horizon.target_pfa,
    )
    if selected is None or not heldout_horizons:
        return None, None, 0
    heldout_false_stops = sum(
        1 for horizon in heldout_horizons if _first_eprocess_stop(horizon, selected) is not None
    )
    upper = clopper_pearson_one_sided_upper_bound(
        heldout_false_stops,
        len(heldout_horizons),
        config.evidence.calibrated_finite_horizon.calibration_confidence,
    )
    return selected, upper, heldout_false_stops


@log_stage("experiments.synthetic")
def _evaluate_hofd_equivalence_seed(
    loaded: LoadedScientificConfiguration,
    seed: SeedValue,
) -> SyntheticCellOutcome:
    config = loaded.values
    experiment = config.experiments.exclusion_matched_hofd_equivalence
    materiality = config.materiality.hofd_equivalence
    client_count = config.experiments.pure_order_separation_validation.primary_client_count
    heldout_count = config.synthetic.sample_sizes.hofd_equivalence_heldout_samples_per_context_seed
    horizon_length = config.campaign.evaluation_horizon_epochs
    calibration_count = config.synthetic.sample_sizes.finite_horizon_calibration_horizons_per_seed
    heldout_horizon_count = (
        config.synthetic.sample_sizes.finite_horizon_heldout_null_horizons_per_seed
    )
    orders = tuple(
        order for order in CoalitionOrder if order <= config.study.maximum_coalition_order
    )
    supports = tuple(
        sorted(
            {
                *experiment.primary_support_levels,
                *config.support_grids.hofd_equivalence_samples_per_context,
            }
        )
    )
    condition_records: list[YamlNode] = []
    condition_metrics: list[HofdEquivalenceConditionMetrics] = []
    failures: list[ComponentName] = []
    offset = 0
    for order in orders:
        width = order
        cell = PureOrderCell(
            generator=_pure_polynomial_generator(order),
            effect=config.generators.pure_polynomial.primary_reference_theta,
            method=MethodName.FULL_FEDCAMPAIGN_EMHI,
            target_order=order,
            enabled_orders=frozenset((order,)),
        )
        for support in supports:
            nuisance_rows = tuple(
                sample_independent_uniform_ranks(client_count, seed + offset + index)[:width]
                for index in range(support)
            )
            offset += support
            heldout_rows = tuple(
                sample_generator_row(cell, client_count, seed + offset + index)[:width]
                for index in range(heldout_count)
            )
            offset += heldout_count
            nuisance_design = tuple(
                proper_subset_design_row(row, config.basis.primary_size) for row in nuisance_rows
            )
            nuisance_tensors = tuple(
                tensor_representation(row, config.basis.primary_size) for row in nuisance_rows
            )
            calibration = calibrate_innovations_on_nuisance_fit(
                nuisance_design,
                nuisance_tensors,
                config.projection.ridge_candidates,
                config.projection.cross_validation.fold_count,
                config.projection.selection_tie_tolerance_mse,
                config.projection.zero_ridge_svd_relative_cutoff,
                config.projection.atom_scale_floor,
            )
            if calibration is None:
                failures.append(f"HOFD equivalence calibration order {width} support {support}")
                continue
            heldout_design = tuple(
                proper_subset_design_row(row, config.basis.primary_size) for row in heldout_rows
            )
            heldout_tensors = tuple(
                tensor_representation(row, config.basis.primary_size) for row in heldout_rows
            )
            emhi_atoms = tuple(
                projection_residual(tensor, calibration.complete_nuisance_coefficients, design)
                for tensor, design in zip(heldout_tensors, heldout_design, strict=True)
            )
            hofd_coefficients = ridge_coefficient_matrix(
                nuisance_design,
                nuisance_tensors,
                config.comparators.exclusion_matched_conditional_hofd.ridge_penalty,
                config.comparators.exclusion_matched_conditional_hofd.relative_singular_cutoff,
            )
            hofd_atoms = tuple(
                projection_residual(tensor, hofd_coefficients, design)
                for tensor, design in zip(heldout_tensors, heldout_design, strict=True)
            )
            nrmse = atom_nrmse(emhi_atoms, hofd_atoms, config.numerics.metric_denominator_floor)
            cosine = atom_cosine_similarity(
                emhi_atoms, hofd_atoms, config.numerics.metric_denominator_floor
            )
            nrmse_passes = nrmse_equivalence_criterion(
                nrmse,
                materiality.atom_nrmse_upper_margin,
            )
            cosine_passes = cosine_equivalence_criterion(
                cosine,
                materiality.minimum_cosine_similarity,
            )

            hofd_nuisance_atoms = tuple(
                projection_residual(tensor, hofd_coefficients, design)
                for tensor, design in zip(nuisance_tensors, nuisance_design, strict=True)
            )
            hofd_moments = moments_from_held_fold_innovations(hofd_nuisance_atoms)
            if hofd_moments is None:
                failures.append(f"HOFD sequential moments order {width} support {support}")
                continue
            hofd_means, hofd_deviations = hofd_moments
            emhi_norm = operational_norm_reference_quantile(
                calibration.standardized_held_fold_innovations,
                config.evidence.operational_norm_reference_quantile,
            )
            hofd_norm = operational_norm_reference_quantile(
                tuple(
                    center_and_scale_atom(
                        atom,
                        hofd_means,
                        hofd_deviations,
                        config.projection.atom_scale_floor,
                    )
                    for atom in hofd_nuisance_atoms
                ),
                config.evidence.operational_norm_reference_quantile,
            )
            null_horizons = tuple(
                tuple(
                    sample_independent_uniform_ranks(
                        client_count, seed + offset + horizon_index * horizon_length + epoch_index
                    )[:width]
                    for epoch_index in range(horizon_length)
                )
                for horizon_index in range(calibration_count + heldout_horizon_count)
            )
            offset += (calibration_count + heldout_horizon_count) * horizon_length
            emhi_null = tuple(
                _operational_factors_for_rows(
                    horizon,
                    calibration.complete_nuisance_coefficients,
                    calibration.coordinate_means,
                    calibration.coordinate_deviations,
                    emhi_norm,
                    config.basis.primary_size,
                    config,
                )
                for horizon in null_horizons
            )
            hofd_null = tuple(
                _operational_factors_for_rows(
                    horizon,
                    hofd_coefficients,
                    hofd_means,
                    hofd_deviations,
                    hofd_norm,
                    config.basis.primary_size,
                    config,
                )
                for horizon in null_horizons
            )
            emhi_threshold, emhi_pfa, _emhi_false = _calibrate_eprocess_threshold(
                emhi_null[:calibration_count], emhi_null[calibration_count:], config
            )
            hofd_threshold, hofd_pfa, _hofd_false = _calibrate_eprocess_threshold(
                hofd_null[:calibration_count], hofd_null[calibration_count:], config
            )
            pfa_ok = (
                emhi_pfa is not None
                and hofd_pfa is not None
                and pfa_prerequisite_criterion(
                    emhi_pfa, config.evidence.calibrated_finite_horizon.target_pfa
                )
                and pfa_prerequisite_criterion(
                    hofd_pfa, config.evidence.calibrated_finite_horizon.target_pfa
                )
            )
            effect_horizon = tuple(
                sample_generator_row(cell, client_count, seed + offset + epoch_index)[:width]
                for epoch_index in range(horizon_length)
            )
            offset += horizon_length
            emhi_effect = _operational_factors_for_rows(
                effect_horizon,
                calibration.complete_nuisance_coefficients,
                calibration.coordinate_means,
                calibration.coordinate_deviations,
                emhi_norm,
                config.basis.primary_size,
                config,
            )
            hofd_effect = _operational_factors_for_rows(
                effect_horizon,
                hofd_coefficients,
                hofd_means,
                hofd_deviations,
                hofd_norm,
                config.basis.primary_size,
                config,
            )
            emhi_stop = (
                None
                if emhi_threshold is None
                else _first_eprocess_stop(emhi_effect, emhi_threshold)
            )
            hofd_stop = (
                None
                if hofd_threshold is None
                else _first_eprocess_stop(hofd_effect, hofd_threshold)
            )
            stop_difference = (
                None
                if emhi_stop is None or hofd_stop is None
                else paired_stopping_time_difference(emhi_stop, hofd_stop)
            )
            detection_difference = paired_detection_indicator_difference(
                emhi_stop is not None, hofd_stop is not None
            )
            condition_metrics.append(
                HofdEquivalenceConditionMetrics(
                    coalition_order=order,
                    support_per_context=support,
                    atom_nrmse=nrmse,
                    atom_cosine_similarity=cosine,
                    stopping_time_difference=stop_difference,
                    detection_indicator_difference=detection_difference,
                    pfa_prerequisite_passes=pfa_ok,
                )
            )
            condition_records.append(
                {
                    "coalition_order": width,
                    "support_per_context": support,
                    "heldout_samples": heldout_count,
                    "atom_nrmse": nrmse,
                    "atom_cosine_similarity": cosine,
                    "nrmse_equivalence_passes": nrmse_passes,
                    "cosine_equivalence_passes": cosine_passes,
                    "emhi_null_pfa": emhi_pfa,
                    "hofd_null_pfa": hofd_pfa,
                    "pfa_prerequisite_passes": pfa_ok,
                    "emhi_stop_epoch": emhi_stop,
                    "hofd_stop_epoch": hofd_stop,
                    "stopping_time_difference": stop_difference,
                    "detection_indicator_difference": detection_difference,
                }
            )
    return SyntheticCellOutcome(
        tuple(failures),
        None,
        {
            "comparison": "paired exclusion-matched EMHI and HOFD atoms and sequential routes",
            "context_cell_count": experiment.context_cell_count,
            "conditions": condition_records,
        },
        hofd_metrics=HofdEquivalenceSeedMetrics(tuple(condition_metrics)),
    )


def _synthetic_robustness_client_ids(client_count: ClientCount) -> tuple[ClientId, ...]:
    return scalability_client_ids(client_count)


def _context_dependent_triple_cell(
    config: ScientificConfig, effect: EffectCoefficient
) -> PureOrderCell:
    return PureOrderCell(
        generator=GeneratorName.CONTEXT_DEPENDENT_PURE_TRIPLE,
        effect=effect,
        method=MethodName.FULL_FEDCAMPAIGN_EMHI,
        target_order=CoalitionOrder.THREE,
        enabled_orders=frozenset((CoalitionOrder.THREE,)),
        context_negative_state_probability=(
            config.generators.context_dependent_triple.initial_state_probabilities.negative_one
        ),
    )


def _rank_rows_as_emhi_artifacts(
    config: ScientificConfig,
    client_ids: tuple[ClientId, ...],
    rows: tuple[tuple[RankValue, ...], ...],
    nuisance_count: RecordCount,
    seed: SeedValue,
    producer: ComponentName,
) -> tuple[DetectorScoreArtifactRecord, MarginalRankArtifactRecord, EMHIFitArtifactRecord]:
    fingerprint = deterministic_digest({"producer": producer, "seed": seed})
    epochs = tuple(range(len(rows)))
    scores = DetectorScoreArtifactRecord(
        dataset_name=DatasetName.TON_IOT_NETWORK,
        root_seed=seed,
        selected_client_ids=client_ids,
        client_streams=tuple(
            ClientDetectorScoreStream(
                client_id=client_id,
                detector_family=DetectorFamily.ISOLATION_FOREST,
                detector_seed=seed,
                epoch_indexes=epochs,
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
        has_sufficient_clients=True,
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
    return scores, ranks, fit


def _contaminate_row(
    row: tuple[RankValue, ...],
    client_ids: tuple[ClientId, ...],
    contaminated_ids: frozenset[ClientId],
    outside_rank_shift: ScoreShift,
    rank_clip_epsilon: NumericalFloor,
) -> tuple[RankValue, ...]:
    return tuple(
        contaminate_rank(rank, outside_rank_shift, rank_clip_epsilon)
        if client_id in contaminated_ids
        else rank
        for client_id, rank in zip(client_ids, row, strict=True)
    )


def _target_order_standardized_drift(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    target_ids: tuple[ClientId, ...],
    null_epochs: tuple[EpochIndexValue, ...],
    alternative_epochs: tuple[EpochIndexValue, ...],
) -> StandardizedDrift | None:
    coalition_fit = next(
        (
            candidate
            for candidate in fit.coalition_fits
            if candidate.coalition_client_ids == target_ids
        ),
        None,
    )
    if coalition_fit is None:
        return None
    null_scores = tuple(
        coalition_evidence_at_epoch(config, ranks, fit, coalition_fit, epoch)
        for epoch in null_epochs
    )
    alternative_scores = tuple(
        coalition_evidence_at_epoch(config, ranks, fit, coalition_fit, epoch)
        for epoch in alternative_epochs
    )
    if any(value is None for value in (*null_scores, *alternative_scores)):
        return None
    resolved_null = tuple(value for value in null_scores if value is not None)
    resolved_alternative = tuple(value for value in alternative_scores if value is not None)
    mean = sum(resolved_null) / len(resolved_null)
    deviation = sqrt(sum((value - mean) ** 2 for value in resolved_null) / len(resolved_null))
    return target_order_drift(
        sum(resolved_alternative) / len(resolved_alternative),
        mean,
        deviation,
        config.numerics.metric_denominator_floor,
    )


@log_stage("experiments.synthetic")
def _evaluate_outside_contamination_seed(
    loaded: LoadedScientificConfiguration, seed: SeedValue
) -> SyntheticCellOutcome:
    config = loaded.values
    specification = config.generators.outside_contamination
    client_ids = _synthetic_robustness_client_ids(specification.client_count)
    target = outside_contamination_targets(client_ids)
    outside = tuple(client_id for client_id in client_ids if client_id not in set(target))
    cell = _context_dependent_triple_cell(config, specification.target_triple_theta)
    nuisance_count = config.synthetic.sample_sizes.generic_nuisance_fit_epochs
    evaluation_count = (
        config.synthetic.sample_sizes.pure_order_independent_evaluation_samples_per_condition_seed
    )
    warmup = config.campaign.prestart_warmup_epochs
    horizon = config.campaign.evaluation_horizon_epochs
    campaign_length = warmup + horizon
    calibration_count = config.synthetic.sample_sizes.finite_horizon_calibration_horizons_per_seed
    heldout_count = config.synthetic.sample_sizes.finite_horizon_heldout_null_horizons_per_seed
    fractions = specification.correlated_campaign_fractions
    prefix_count = (
        nuisance_count + evaluation_count + ((calibration_count + heldout_count) * campaign_length)
    )
    uncontaminated: list[tuple[RankValue, ...]] = [
        sample_generator_row(cell, specification.client_count, seed + index)
        for index in range(prefix_count)
    ]
    campaign_blocks: list[tuple[tuple[RankValue, ...], ...]] = []
    for fraction in fractions:
        contaminated_ids = frozenset(contaminated_outside_clients(outside, fraction))
        block = tuple(
            _contaminate_row(
                sample_generator_row(
                    cell,
                    specification.client_count,
                    seed + len(uncontaminated) + (len(campaign_blocks) * campaign_length) + index,
                ),
                client_ids,
                contaminated_ids,
                specification.outside_rank_shift,
                config.context.rank_clip_epsilon,
            )
            for index in range(campaign_length)
        )
        campaign_blocks.append(block)
    rows = tuple(uncontaminated) + tuple(row for block in campaign_blocks for row in block)
    _scores, ranks, fit = _rank_rows_as_emhi_artifacts(
        config,
        client_ids,
        rows,
        nuisance_count,
        seed,
        "outside-campaign-contamination",
    )
    calibration_start = nuisance_count + evaluation_count

    def _horizons(origin: EpochIndexValue, count: RecordCount) -> tuple[BenignHorizonRecord, ...]:
        return tuple(
            BenignHorizonRecord(
                start_epoch=origin + (index * campaign_length) + warmup,
                epoch_indexes=tuple(
                    range(
                        origin + (index * campaign_length) + warmup,
                        origin + ((index + 1) * campaign_length),
                    )
                ),
            )
            for index in range(count)
        )

    operating = calibrate_global_operating_point(
        config,
        ranks,
        fit,
        BenignPartitionRecord(
            dataset_name=DatasetName.TON_IOT_NETWORK,
            calibration_horizons=_horizons(calibration_start, calibration_count),
            heldout_horizons=_horizons(
                calibration_start + (calibration_count * campaign_length),
                heldout_count,
            ),
        ),
    )
    null_epochs = tuple(range(nuisance_count, nuisance_count + evaluation_count))
    campaign_origin = calibration_start + ((calibration_count + heldout_count) * campaign_length)
    records: list[YamlNode] = []
    for index, fraction in enumerate(fractions):
        start = campaign_origin + (index * campaign_length)
        scored = tuple(range(start + warmup, start + campaign_length))
        trajectory = sequential_trajectory(config, ranks, fit, scored)
        coverage = trajectory_context_coverage(trajectory)
        stop = (
            None
            if operating.threshold is None
            else global_stop_epoch(trajectory, operating.threshold)
        )
        drift = _target_order_standardized_drift(
            config,
            ranks,
            fit,
            target,
            null_epochs,
            scored,
        )
        records.append(
            {
                "correlated_campaign_fraction": fraction,
                "contaminated_outside_client_ids": list(
                    contaminated_outside_clients(outside, fraction)
                ),
                "target_order_drift": drift,
                "detection_rate": campaign_detection_rate((stop,), horizon),
                "context_coverage": coverage,
                "abstention_rate": abstention_rate(coverage),
                "null_pfa": operating.heldout_upper_pfa,
            }
        )
    return SyntheticCellOutcome(
        (),
        None,
        {"target_client_ids": list(target), "contamination_conditions": records},
    )


@log_stage("experiments.synthetic")
def _evaluate_dropout_sparsity_seed(
    loaded: LoadedScientificConfiguration, seed: SeedValue
) -> SyntheticCellOutcome:
    config = loaded.values
    cell = _context_dependent_triple_cell(
        config, config.generators.context_dependent_triple.primary_theta
    )
    nuisance_count = config.synthetic.sample_sizes.generic_nuisance_fit_epochs
    warmup = config.campaign.prestart_warmup_epochs
    horizon = config.campaign.evaluation_horizon_epochs
    campaign_length = warmup + horizon
    calibration_count = config.synthetic.sample_sizes.finite_horizon_calibration_horizons_per_seed
    heldout_count = config.synthetic.sample_sizes.finite_horizon_heldout_null_horizons_per_seed
    records: list[YamlNode] = []
    for client_count in config.robustness.scalability_client_counts:
        client_ids = _synthetic_robustness_client_ids(client_count)
        target = outside_contamination_targets(client_ids)
        prefix_count = nuisance_count + ((calibration_count + heldout_count) * campaign_length)
        rows = tuple(
            sample_generator_row(cell, client_count, seed + client_count + index)
            for index in range(prefix_count + campaign_length)
        )
        _scores, ranks, fit = _rank_rows_as_emhi_artifacts(
            config,
            client_ids,
            rows,
            nuisance_count,
            seed + client_count,
            "client-dropout-sparsity",
        )

        def _horizons(
            origin: EpochIndexValue, count: RecordCount
        ) -> tuple[BenignHorizonRecord, ...]:
            return tuple(
                BenignHorizonRecord(
                    start_epoch=origin + (index * campaign_length) + warmup,
                    epoch_indexes=tuple(
                        range(
                            origin + (index * campaign_length) + warmup,
                            origin + ((index + 1) * campaign_length),
                        )
                    ),
                )
                for index in range(count)
            )

        operating = calibrate_global_operating_point(
            config,
            ranks,
            fit,
            BenignPartitionRecord(
                dataset_name=DatasetName.TON_IOT_NETWORK,
                calibration_horizons=_horizons(nuisance_count, calibration_count),
                heldout_horizons=_horizons(
                    nuisance_count + (calibration_count * campaign_length),
                    heldout_count,
                ),
            ),
        )
        campaign_origin = prefix_count
        scored = tuple(range(campaign_origin + warmup, campaign_origin + campaign_length))

        for fraction in config.generators.client_dropout.unavailable_fractions:
            records.append(
                _dropout_sparsity_record(
                    config,
                    ranks,
                    fit,
                    operating,
                    target,
                    client_ids,
                    scored,
                    client_count,
                    seed,
                    fraction,
                    horizon,
                    nuisance_count,
                )
            )
    return SyntheticCellOutcome((), None, {"dropout_conditions": records})


def _dropout_sparsity_record(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    operating: CalibratedGlobalOperatingPoint,
    target: tuple[ClientId, ...],
    client_ids: tuple[ClientId, ...],
    scored: tuple[EpochIndexValue, ...],
    client_count: ClientCount,
    seed: SeedValue,
    fraction: Probability,
    horizon: EpochCount,
    nuisance_count: EpochCount,
) -> YamlNode:
    available_by_epoch = {
        epoch: frozenset(availability_mask(client_ids, fraction, seed + epoch)) for epoch in scored
    }
    active_epochs = 0
    for epoch in scored:
        available = tuple(available_by_epoch[epoch])
        if dropout_coalition_is_active(
            target,
            available,
            client_ids,
            config.context.minimum_available_outside_clients,
            config.context.minimum_available_outside_fraction,
        ):
            active_epochs += 1
    coverage = active_epochs / len(scored)
    filtered_streams = tuple(
        ClientMarginalRankStream(
            client_id=stream.client_id,
            nuisance_reference_scores=stream.nuisance_reference_scores,
            epoch_indexes=tuple(
                epoch
                for epoch, _rank in zip(stream.epoch_indexes, stream.ranks, strict=True)
                if epoch not in available_by_epoch or stream.client_id in available_by_epoch[epoch]
            ),
            ranks=tuple(
                rank
                for epoch, rank in zip(stream.epoch_indexes, stream.ranks, strict=True)
                if epoch not in available_by_epoch or stream.client_id in available_by_epoch[epoch]
            ),
        )
        for stream in ranks.client_streams
    )
    filtered_ranks = ranks.model_copy(update={"client_streams": filtered_streams})
    started = perf_counter()
    trajectory = sequential_trajectory(config, filtered_ranks, fit, scored)
    latency = perf_counter() - started
    stop = (
        None if operating.threshold is None else global_stop_epoch(trajectory, operating.threshold)
    )
    drift = _target_order_standardized_drift(
        config,
        ranks,
        fit,
        target,
        tuple(range(nuisance_count)),
        scored,
    )
    return {
        "client_count": client_count,
        "unavailable_fraction": fraction,
        "context_coverage": coverage,
        "abstention_rate": abstention_rate(coverage),
        "standardized_null_bias": drift,
        "detection_rate": campaign_detection_rate((stop,), horizon),
        "latency_seconds": latency,
        "null_pfa": operating.heldout_upper_pfa,
        "operating_point_available": operating.threshold is not None,
    }


def composition_reference_cell(
    method_name: MethodName, order: CoalitionOrder, config: ScientificConfig
) -> PureOrderCell:
    generator = (
        GeneratorName.PURE_ORDER_TWO
        if order is CoalitionOrder.TWO
        else GeneratorName.PURE_CONTINUOUS_TRIPLE
    )
    return PureOrderCell(
        generator=generator,
        effect=config.generators.pure_polynomial.primary_reference_theta,
        method=method_name,
        target_order=order,
        enabled_orders=frozenset((order,)),
    )


def composition_reference_rows(
    cell: PureOrderCell, client_count: ClientCount, seed: SeedValue, sample_count: RecordCount
) -> tuple[tuple[RankValue, ...], ...]:
    return tuple(
        sample_generator_row(cell, client_count, seed + sample_count + index)
        for index in range(sample_count)
    )


def synthetic_role_seeds(
    loaded: LoadedScientificConfiguration, role: ExecutionRole
) -> tuple[SeedValue, ...]:
    if role is ExecutionRole.CONFIRMATORY:
        return loaded.values.randomness.synthetic_confirmatory_roots
    return loaded.values.randomness.synthetic_development_roots


@log_stage("experiments.synthetic")
def run_synthetic_cell(
    loaded: LoadedScientificConfiguration,
    experiment_name: ExperimentName,
    seed: SeedValue,
    method_name: MethodName | None,
    execution_role: ExecutionRole = ExecutionRole.CONFIRMATORY,
) -> SyntheticCellOutcome:
    config = loaded.values
    if experiment_name is ExperimentName.OUTSIDE_CAMPAIGN_CONTAMINATION_BOUNDARY:
        return _evaluate_outside_contamination_seed(loaded, seed)
    if experiment_name is ExperimentName.CLIENT_DROPOUT_AND_CONTEXT_SPARSITY_BOUNDARY:
        return _evaluate_dropout_sparsity_seed(loaded, seed)
    if experiment_name is ExperimentName.EXCLUSION_MATCHED_HOFD_EQUIVALENCE:
        if method_name not in {
            MethodName.FULL_FEDCAMPAIGN_EMHI,
            MethodName.EXCLUSION_MATCHED_CONDITIONAL_HOFD,
        }:
            raise ValueError("HOFD equivalence requires a declared paired method")
        return _evaluate_hofd_equivalence_seed(loaded, seed)
    if experiment_name is ExperimentName.ESTIMATOR_SUPPORT_AND_CONTEXT_FEASIBILITY:
        return _estimator_feasibility_outcome(config, seed, execution_role)
    if experiment_name is ExperimentName.STRONG_COMPARATOR_COMPOSITION_CHALLENGE:
        return _strong_comparator_outcome(config, seed, method_name)
    if experiment_name is ExperimentName.SEQUENTIAL_EVIDENCE_VALIDATION:
        return _sequential_evidence_outcome(config, seed)
    if experiment_name is ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION:
        return _self_explanation_outcome(config, seed)
    if experiment_name is ExperimentName.PURE_ORDER_SEPARATION_VALIDATION:
        return _pure_order_outcome(config, seed, method_name)
    raise ValueError(f"unsupported synthetic experiment {experiment_name.value}")


def _estimator_feasibility_outcome(
    config: ScientificConfig, seed: SeedValue, execution_role: ExecutionRole
) -> SyntheticCellOutcome:
    sequence = primary_feasibility_context_support(config, seed)
    evaluations = evaluate_estimator_feasibility_seed(config, seed, execution_role)
    primary = next(
        evaluation
        for evaluation in evaluations
        if evaluation.condition.identifier == "primary-order-three"
    )
    metrics = primary.metrics
    return SyntheticCellOutcome(
        (),
        None,
        {
            "primary_support_substrate_rows": len(sequence.ranks),
            "primary_order_three": {
                "conditional_rank_mae": metrics.conditional_rank_mae,
                "projection_nrmse": metrics.projection_nrmse,
                "standardized_null_bias": metrics.standardized_null_bias,
                "context_coverage": metrics.context_coverage,
                "abstention_rate": metrics.abstention_rate,
                "condition_number": metrics.condition_number,
                "numerical_failure": metrics.numerical_failure,
                "numerical_failure_rate": metrics.numerical_failure_rate,
            },
            "condition_evaluations": [
                {
                    "identifier": evaluation.condition.identifier,
                    "order": evaluation.condition.order,
                    "support_per_context": evaluation.condition.support_per_context,
                    "basis_size": evaluation.condition.basis_size,
                    "cell_count": evaluation.condition.cell_count,
                    "forced_no_abstention": evaluation.condition.forced_no_abstention,
                    "conditional_rank_mae": evaluation.metrics.conditional_rank_mae,
                    "projection_nrmse": evaluation.metrics.projection_nrmse,
                    "standardized_null_bias": evaluation.metrics.standardized_null_bias,
                    "context_coverage": evaluation.metrics.context_coverage,
                    "abstention_rate": evaluation.metrics.abstention_rate,
                    "condition_number": evaluation.metrics.condition_number,
                    "numerical_failure": evaluation.metrics.numerical_failure,
                    "numerical_failure_rate": evaluation.metrics.numerical_failure_rate,
                }
                for evaluation in evaluations
            ],
        },
        None,
        None,
        None,
        EstimatorFeasibilitySeedMetrics(metrics),
    )


def _strong_comparator_outcome(
    config: ScientificConfig, seed: SeedValue, method_name: MethodName | None
) -> SyntheticCellOutcome:
    if method_name is None:
        raise ValueError("strong comparator selection requires a declared candidate")
    order = native_target_order(method_name)
    if order is None:
        raise ValueError("strong comparator candidate has no native target order")
    client_count = config.experiments.pure_order_separation_validation.primary_client_count
    sample_count = (
        config.synthetic.sample_sizes.pure_order_independent_evaluation_samples_per_condition_seed
    )
    cell = composition_reference_cell(method_name, order, config)
    nuisance = tuple(
        sample_independent_uniform_ranks(client_count, seed + index)
        for index in range(sample_count)
    )
    alternatives = composition_reference_rows(cell, client_count, seed, sample_count)
    fitted_state = fit_comparator_state(method_name, tuple(row[:order] for row in nuisance), config)
    null_scores = tuple(
        score_comparator_ranks(method_name, row[:order], config, (), fitted_state)[0]
        for row in nuisance
    )
    alternative_scores = tuple(
        score_comparator_ranks(method_name, row[:order], config, (), fitted_state)[0]
        for row in alternatives
    )
    mean = sum(null_scores) / len(null_scores)
    deviation = (sum((value - mean) ** 2 for value in null_scores) / len(null_scores)) ** 0.5
    if deviation <= config.numerics.metric_denominator_floor:
        return SyntheticCellOutcome(
            ("strong comparator nuisance variation is not usable",),
            None,
            {"implementation_state": "unusable_nuisance_standardization"},
        )
    standardized_score = (sum(alternative_scores) / len(alternative_scores) - mean) / deviation
    mixed_diagnostics: list[YamlNode] = []
    mixed_failures: list[ComponentName] = []
    remaining = client_count - CoalitionOrder.THREE
    for term_index, term_set in enumerate(config.generators.mixed_order.enabled_term_sets):
        enabled = frozenset(CoalitionOrder(term) for term in term_set)
        row = sample_mixed_order_ranks(
            enabled,
            config.generators.mixed_order.term_coefficient,
            remaining,
            seed + sample_count + term_index,
        )
        mixed_score, _state = score_comparator_ranks(
            method_name, row[:order], config, (), fitted_state
        )
        finite = isfinite(mixed_score)
        mixed_diagnostics.append(
            {
                "enabled_orders": sorted(enabled),
                "finite_native_order_score": finite,
                "native_order_score": mixed_score,
            }
        )
        if not finite:
            mixed_failures.append(f"mixed-order diagnostic {sorted(enabled)}")
    return SyntheticCellOutcome(
        tuple(mixed_failures),
        standardized_score,
        {
            "implementation_state": "native_order_score_complete",
            "native_target_order": order,
            "standardized_target_order_score": standardized_score,
            "standardized_target_order_error": abs(
                standardized_score - config.generators.pure_polynomial.primary_reference_theta
            ),
            "mixed_order_diagnostics": mixed_diagnostics,
        },
    )


def _sequential_evidence_outcome(config: ScientificConfig, seed: SeedValue) -> SyntheticCellOutcome:
    result = evaluate_signed_theorem_seed(config, seed)
    failed_checks: tuple[ComponentName, ...] = (
        () if result.assumptions_hold else ("signed-theorem mechanical assumptions",)
    )
    return SyntheticCellOutcome(
        failed_checks,
        None,
        {
            "signed_theorem": {
                "restricted_arl": result.metrics.restricted_arl,
                "stopped_trajectory_count": result.metrics.stopped_trajectory_count,
                "trajectory_count": result.metrics.trajectory_count,
                "maximum_trajectory_epochs": result.metrics.maximum_trajectory_epochs,
                "e_sr_threshold": result.metrics.threshold,
                "compensator": result.metrics.compensator,
                "assumptions_hold": result.assumptions_hold,
            }
        },
        None,
        None,
        result.metrics,
    )


def _self_explanation_outcome(config: ScientificConfig, seed: SeedValue) -> SyntheticCellOutcome:
    result = evaluate_self_explanation_seed(config, seed)
    materiality = config.materiality.self_explanation
    exact_derivative_within_margin = exact_nuisance_derivative_within_margin(
        result.primary_exact_nuisance_derivative,
        materiality.exact_exclusion_nuisance_derivative_equivalence_fraction_of_direct,
    )
    attenuation_is_material = material_attenuation_criterion(
        result.primary_attenuation_contrast,
        materiality.minimum_attenuation_difference,
    )
    return SyntheticCellOutcome(
        (),
        None,
        {
            "grid_cell_count": len(result.measurements),
            "primary_exact_nuisance_derivative": result.primary_exact_nuisance_derivative,
            "primary_attenuation_contrast": result.primary_attenuation_contrast,
            "exact_nuisance_derivative_within_margin": exact_derivative_within_margin,
            "attenuation_is_material": attenuation_is_material,
            "measurements": [
                {
                    "client_count": measurement.cell.client_count,
                    "coalition_order": measurement.cell.coalition_order,
                    "perturbation": measurement.cell.perturbation,
                    "nuisance_transform": measurement.cell.nuisance_transform.value,
                    "context_method": measurement.cell.context_method.value,
                    "response_mean": measurement.response_mean,
                    "nuisance_mean": measurement.nuisance_mean,
                    "innovation_mean": measurement.innovation_mean,
                    "direct_derivative": measurement.direct_derivative,
                    "nuisance_derivative": measurement.nuisance_derivative,
                    "innovation_derivative": measurement.innovation_derivative,
                    "attenuation": measurement.attenuation,
                }
                for measurement in result.measurements
            ],
        },
        SelfExplanationSeedMetrics(
            primary_exact_nuisance_derivative=result.primary_exact_nuisance_derivative,
            primary_attenuation_contrast=result.primary_attenuation_contrast,
        ),
    )


def _pure_order_outcome(
    config: ScientificConfig, seed: SeedValue, method_name: MethodName | None
) -> SyntheticCellOutcome:
    if method_name is None:
        raise ValueError("pure-order scoring requires a declared method")
    failures: list[ComponentName] = []
    records: list[YamlNode] = []
    pure_generators = frozenset(
        {
            GeneratorName.PURE_ORDER_ONE,
            GeneratorName.PURE_ORDER_TWO,
            GeneratorName.PURE_CONTINUOUS_TRIPLE,
            GeneratorName.XOR_PARITY_TRIPLE,
        }
    )
    for cell in enumerate_pure_order_grid(config):
        if cell.method is not method_name:
            continue
        report = validate_generator_purity(
            cell.generator,
            cell.effect,
            cell.effect,
            cell.enabled_orders,
            config.numerics.deterministic_comparison_tolerance,
        )
        if cell.generator in pure_generators and not report.is_valid:
            failures.append(f"generator:{cell.generator.value}")
        records.append(
            {
                "generator": cell.generator.value,
                "effect": cell.effect,
                "method": cell.method.value,
                "target_order": cell.target_order,
                "enabled_orders": sorted(cell.enabled_orders),
                "purity_valid": report.is_valid,
                "scoring_state": "execution-layer-fitted-grid",
            }
        )
    return SyntheticCellOutcome(
        tuple(sorted(set(failures))),
        None,
        {
            "condition_count": len(records),
            "conditions": records,
            "implementation_state": "execution-layer-grid",
        },
        pure_order_metrics=None,
    )
