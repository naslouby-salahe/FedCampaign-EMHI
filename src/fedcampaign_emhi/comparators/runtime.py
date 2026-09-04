from dataclasses import dataclass
from math import log
from pathlib import Path
from typing import cast

from fedcampaign_emhi.artifacts.provenance import (
    evidence_export_boundary_digest,
    material_fingerprint,
)
from fedcampaign_emhi.artifacts.records import StrongComparatorCompositionRecord
from fedcampaign_emhi.artifacts.storage import build_artifact_layout, payload_digest
from fedcampaign_emhi.comparators.contracts import comparator_method_contracts, native_target_order
from fedcampaign_emhi.comparators.dependence import (
    DVineFittedCorrelations,
    GlobalFactorFittedBasis,
    cosine_equivalence_criterion,
    d_vine_conditional_reference_score,
    empirical_triple_joint_counts,
    fit_d_vine_correlations,
    fit_global_factor_basis,
    fit_lancaster_triple_reference,
    fit_pair_dependence_reference,
    fit_pairwise_maxent_table,
    floored_probability_table,
    global_factor_residual_score,
    hofd_atom_rows,
    jeffreys_smoothed_probabilities,
    lancaster_triple_moment,
    lancaster_triple_nonconformity,
    nrmse_equivalence_criterion,
    pair_dependence_moment,
    pair_dependence_nonconformity,
    pfa_prerequisite_criterion,
    stopping_time_equivalence_criterion,
    target_coalition_for_order,
)
from fedcampaign_emhi.comparators.fusion import (
    CompositionSelectionInputs,
    materialize_composition_record,
    max_rank_fusion,
    mean_rank_fusion,
    selection_rule_identity,
)
from fedcampaign_emhi.comparators.sequential import (
    global_cusum_score,
    next_cusum_state,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration, ScientificConfig
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import CoalitionOrder, ExperimentName, MethodName
from fedcampaign_emhi.domain.types import (
    BinCount,
    BinIndex,
    CusumState,
    DependenceMoment,
    DetectorScore,
    ProbabilityMass,
    RankValue,
    StandardDeviation,
)
from fedcampaign_emhi.emhi.projection import proper_subset_design_row
from fedcampaign_emhi.emhi.structure import tensor_representation
from fedcampaign_emhi.runtime import log_stage


@dataclass(frozen=True)
class ComparatorFittedState:
    pair_dependence_mean: DependenceMoment | None = None
    pair_dependence_deviation: StandardDeviation | None = None
    lancaster_triple_mean: DependenceMoment | None = None
    lancaster_triple_deviation: StandardDeviation | None = None
    d_vine: DVineFittedCorrelations | None = None
    connected_information_bin_count: BinCount | None = None
    connected_information_smoothed_table: (
        tuple[tuple[tuple[ProbabilityMass, ...], ...], ...] | None
    ) = None
    connected_information_maxent_table: (
        tuple[tuple[tuple[ProbabilityMass, ...], ...], ...] | None
    ) = None
    log_linear_bin_count: BinCount | None = None
    log_linear_maxent_table: tuple[tuple[tuple[ProbabilityMass, ...], ...], ...] | None = None
    global_factor: GlobalFactorFittedBasis | None = None


@log_stage("comparators.runtime")
def fit_comparator_state(
    method_name: MethodName,
    nuisance_rows: tuple[tuple[RankValue, ...], ...],
    config: ScientificConfig,
) -> ComparatorFittedState | None:
    if method_name is MethodName.CONDITIONAL_PAIR_DEPENDENCE:
        pairs = tuple((row[0], row[1]) for row in nuisance_rows)
        mean, deviation = fit_pair_dependence_reference(pairs)
        return ComparatorFittedState(pair_dependence_mean=mean, pair_dependence_deviation=deviation)
    if method_name is MethodName.EXCLUSION_MATCHED_LANCASTER_TRIPLE:
        triples = tuple((row[0], row[1], row[2]) for row in nuisance_rows)
        mean, deviation = fit_lancaster_triple_reference(triples)
        return ComparatorFittedState(
            lancaster_triple_mean=mean, lancaster_triple_deviation=deviation
        )
    if method_name is MethodName.D_VINE_CONDITIONAL_REFERENCE:
        triples = tuple((row[0], row[1], row[2]) for row in nuisance_rows)
        return ComparatorFittedState(
            d_vine=fit_d_vine_correlations(triples, config.context.rank_clip_epsilon)
        )
    if method_name is MethodName.CONNECTED_INFORMATION_REFERENCE:
        triples = tuple((row[0], row[1], row[2]) for row in nuisance_rows)
        bin_count = config.comparators.connected_information.bins_per_client
        counts = empirical_triple_joint_counts(triples, bin_count)
        smoothed = jeffreys_smoothed_probabilities(
            counts, config.comparators.connected_information.jeffreys_pseudocount_per_cell
        )
        maxent = fit_pairwise_maxent_table(
            smoothed,
            config.comparators.connected_information.ipf_max_iterations,
            config.comparators.connected_information.maximum_marginal_absolute_error,
        )
        return ComparatorFittedState(
            connected_information_bin_count=bin_count,
            connected_information_smoothed_table=smoothed,
            connected_information_maxent_table=maxent,
        )
    if method_name is MethodName.CONDITIONAL_LOG_LINEAR_REFERENCE:
        triples = tuple((row[0], row[1], row[2]) for row in nuisance_rows)
        bin_count = config.comparators.conditional_log_linear.bins_per_client
        counts = empirical_triple_joint_counts(triples, bin_count)
        floored = floored_probability_table(
            counts, config.comparators.conditional_log_linear.probability_floor
        )
        maxent = fit_pairwise_maxent_table(
            floored,
            config.comparators.conditional_log_linear.max_iterations,
            config.comparators.conditional_log_linear.maximum_fitted_marginal_absolute_error,
        )
        return ComparatorFittedState(log_linear_bin_count=bin_count, log_linear_maxent_table=maxent)
    if method_name is MethodName.GLOBAL_FACTOR_RESIDUAL_REFERENCE:
        return ComparatorFittedState(
            global_factor=fit_global_factor_basis(
                nuisance_rows,
                config.comparators.global_factor_residual.cumulative_variance_target,
                config.comparators.global_factor_residual.fallback_rank,
                config.comparators.global_factor_residual.candidate_ranks,
            )
        )
    return None


def comparator_methods_with_runtime() -> tuple[MethodName, ...]:
    return tuple(contract.method_name for contract in comparator_method_contracts())


def resolve_comparator_scoring_method(
    loaded: LoadedScientificConfiguration, repository: Path, method_name: MethodName
) -> MethodName:
    if method_name is not MethodName.SELECTED_STRONG_COMPARATOR_COMPOSITION:
        return method_name
    layout = build_artifact_layout(loaded, repository)
    filename = loaded.values.experiments.strong_comparator_composition_challenge.artifact_filename
    path = (
        layout.experiment_outputs_root(ExperimentName.STRONG_COMPARATOR_COMPOSITION_CHALLENGE)
        / "artifacts"
        / "derived"
        / filename
    )
    if not path.is_file():
        raise ValueError("selected strong comparator requires a validated composition artifact")
    record = StrongComparatorCompositionRecord.model_validate_json(path.read_bytes())
    payload = record.model_dump(mode="json", exclude={"dependency_fingerprint", "content_digest"})
    if payload_digest(cast(YamlNode, payload)) != record.content_digest:
        raise ValueError("selected strong comparator artifact content digest is invalid")
    if record.dependency_fingerprint != material_fingerprint(
        evidence_export_boundary_digest(loaded.values), record.source_artifact_hashes
    ):
        raise ValueError("selected strong comparator artifact dependency fingerprint is stale")
    if record.selected_method not in record.eligible_candidates:
        raise ValueError("selected strong comparator artifact selected an ineligible candidate")
    if native_target_order(record.selected_method) is not record.selected_native_order:
        raise ValueError("selected strong comparator artifact native-order mapping is invalid")
    return record.selected_method


def _rank_bin(rank: RankValue, bin_count: BinCount) -> BinIndex:
    return min(int(rank * bin_count), bin_count - 1)


def _connected_information_score(
    ranks: tuple[RankValue, ...], fitted_state: ComparatorFittedState | None
) -> DetectorScore:
    if len(ranks) != 3:
        raise ValueError("connected information requires three ranks")
    if (
        fitted_state is None
        or fitted_state.connected_information_bin_count is None
        or fitted_state.connected_information_smoothed_table is None
        or fitted_state.connected_information_maxent_table is None
    ):
        raise ValueError("connected-information reference requires a fitted comparator state")
    bin_count = fitted_state.connected_information_bin_count
    indexes = tuple(_rank_bin(rank, bin_count) for rank in ranks)
    numerator = fitted_state.connected_information_smoothed_table[indexes[0]][indexes[1]][
        indexes[2]
    ]
    denominator = fitted_state.connected_information_maxent_table[indexes[0]][indexes[1]][
        indexes[2]
    ]
    return abs(log(numerator / denominator))


def _log_linear_score(
    ranks: tuple[RankValue, ...], fitted_state: ComparatorFittedState | None
) -> DetectorScore:
    if len(ranks) != 3:
        raise ValueError("conditional log-linear reference requires three ranks")
    if (
        fitted_state is None
        or fitted_state.log_linear_bin_count is None
        or (fitted_state.log_linear_maxent_table is None)
    ):
        raise ValueError("conditional log-linear reference requires a fitted comparator state")
    bin_count = fitted_state.log_linear_bin_count
    indexes = tuple(_rank_bin(rank, bin_count) for rank in ranks)
    probability = fitted_state.log_linear_maxent_table[indexes[0]][indexes[1]][indexes[2]]
    return -log(probability)


def _hofd_score(ranks: tuple[RankValue, ...], config: ScientificConfig) -> DetectorScore:
    tensor = tensor_representation(ranks, config.basis.primary_size)
    design = proper_subset_design_row(ranks, config.basis.primary_size)
    residual = hofd_atom_rows(
        (tensor,),
        (design,),
        config.comparators.exclusion_matched_conditional_hofd.ridge_penalty,
        config.comparators.exclusion_matched_conditional_hofd.relative_singular_cutoff,
    )[0]
    return sum(value * value for value in residual) ** 0.5


def score_comparator_ranks(
    method_name: MethodName,
    ranks: tuple[RankValue, ...],
    config: ScientificConfig,
    previous_cusum_state: tuple[CusumState, ...] = (),
    fitted_state: ComparatorFittedState | None = None,
) -> tuple[DetectorScore, tuple[CusumState, ...]]:
    if not ranks:
        raise ValueError("comparator scoring requires at least one rank")
    if method_name in _EMHI_REQUIRING_FITTED_ARTIFACT:
        raise ValueError("EMHI methods require a fitted EMHI artifact")
    if method_name is MethodName.RAW_MEAN_RANK_FUSION:
        return _raw_mean_scorer(ranks, config, previous_cusum_state, fitted_state)
    if method_name is MethodName.RAW_MAX_RANK_FUSION:
        return _raw_max_scorer(ranks, config, previous_cusum_state, fitted_state)
    if method_name is MethodName.CONDITIONAL_PAIR_DEPENDENCE:
        return _pair_dependence_scorer(ranks, config, previous_cusum_state, fitted_state)
    if method_name is MethodName.EXCLUSION_MATCHED_LANCASTER_TRIPLE:
        return _lancaster_scorer(ranks, config, previous_cusum_state, fitted_state)
    if method_name is MethodName.CONNECTED_INFORMATION_REFERENCE:
        return _connected_information_scorer(ranks, config, previous_cusum_state, fitted_state)
    if method_name is MethodName.D_VINE_CONDITIONAL_REFERENCE:
        return _d_vine_scorer(ranks, config, previous_cusum_state, fitted_state)
    if method_name is MethodName.CONDITIONAL_LOG_LINEAR_REFERENCE:
        return _log_linear_scorer(ranks, config, previous_cusum_state, fitted_state)
    if method_name is MethodName.EXCLUSION_MATCHED_CONDITIONAL_HOFD:
        return _hofd_scorer(ranks, config, previous_cusum_state, fitted_state)
    if method_name is MethodName.GLOBAL_FACTOR_RESIDUAL_REFERENCE:
        return _global_factor_scorer(ranks, config, previous_cusum_state, fitted_state)
    if method_name is MethodName.MULTISTREAM_CUSUM_REFERENCE:
        return _multistream_cusum_scorer(ranks, config, previous_cusum_state, fitted_state)
    if method_name is MethodName.FEDAVG_AUTOENCODER_REFERENCE:
        return _raw_mean_scorer(ranks, config, previous_cusum_state, fitted_state)
    raise ValueError(f"unsupported comparator method {method_name.value}")


_EMHI_REQUIRING_FITTED_ARTIFACT = frozenset(
    {
        MethodName.FULL_FEDCAMPAIGN_EMHI,
        MethodName.EXCLUSION_MATCHED_ORDER_ONE_EMHI,
        MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI,
        MethodName.INCLUSIVE_CONTEXT_FULL_HIERARCHY,
        MethodName.LEAVE_ONE_OUT_INSUFFICIENT_EXCLUSION,
        MethodName.PARTIAL_COALITION_EXCLUSION,
        MethodName.NO_PROPER_SUBSET_PURIFICATION,
        MethodName.NO_OUTSIDE_CONTEXT_FULL_HIERARCHY,
    }
)


def _raw_mean_scorer(
    ranks: tuple[RankValue, ...],
    config: ScientificConfig,
    previous_cusum_state: tuple[CusumState, ...],
    fitted_state: ComparatorFittedState | None,
) -> tuple[DetectorScore, tuple[CusumState, ...]]:
    return mean_rank_fusion(ranks), previous_cusum_state


def _raw_max_scorer(
    ranks: tuple[RankValue, ...],
    config: ScientificConfig,
    previous_cusum_state: tuple[CusumState, ...],
    fitted_state: ComparatorFittedState | None,
) -> tuple[DetectorScore, tuple[CusumState, ...]]:
    return max_rank_fusion(ranks), previous_cusum_state


def _pair_dependence_scorer(
    ranks: tuple[RankValue, ...],
    config: ScientificConfig,
    previous_cusum_state: tuple[CusumState, ...],
    fitted_state: ComparatorFittedState | None,
) -> tuple[DetectorScore, tuple[CusumState, ...]]:
    if len(ranks) < 2:
        raise ValueError("pair comparator requires two ranks")
    if (
        fitted_state is None
        or fitted_state.pair_dependence_mean is None
        or fitted_state.pair_dependence_deviation is None
    ):
        raise ValueError("pair-dependence reference requires a fitted comparator state")
    moment = pair_dependence_moment(ranks[0], ranks[1])
    score = pair_dependence_nonconformity(
        moment,
        fitted_state.pair_dependence_mean,
        fitted_state.pair_dependence_deviation,
        config.numerics.metric_denominator_floor,
    )
    return score, previous_cusum_state


def _lancaster_scorer(
    ranks: tuple[RankValue, ...],
    config: ScientificConfig,
    previous_cusum_state: tuple[CusumState, ...],
    fitted_state: ComparatorFittedState | None,
) -> tuple[DetectorScore, tuple[CusumState, ...]]:
    if len(ranks) < 3:
        raise ValueError("Lancaster comparator requires three ranks")
    if (
        fitted_state is None
        or fitted_state.lancaster_triple_mean is None
        or fitted_state.lancaster_triple_deviation is None
    ):
        raise ValueError("Lancaster-triple reference requires a fitted comparator state")
    moment = lancaster_triple_moment(ranks[0], ranks[1], ranks[2])
    return (
        lancaster_triple_nonconformity(
            moment,
            fitted_state.lancaster_triple_mean,
            fitted_state.lancaster_triple_deviation,
            config.numerics.metric_denominator_floor,
        ),
        previous_cusum_state,
    )


def _connected_information_scorer(
    ranks: tuple[RankValue, ...],
    config: ScientificConfig,
    previous_cusum_state: tuple[CusumState, ...],
    fitted_state: ComparatorFittedState | None,
) -> tuple[DetectorScore, tuple[CusumState, ...]]:
    return _connected_information_score(ranks, fitted_state), previous_cusum_state


def _d_vine_scorer(
    ranks: tuple[RankValue, ...],
    config: ScientificConfig,
    previous_cusum_state: tuple[CusumState, ...],
    fitted_state: ComparatorFittedState | None,
) -> tuple[DetectorScore, tuple[CusumState, ...]]:
    if len(ranks) < 3:
        raise ValueError("D-vine comparator requires three ranks")
    if fitted_state is None or fitted_state.d_vine is None:
        raise ValueError("D-vine conditional reference requires a fitted comparator state")
    score = d_vine_conditional_reference_score(
        (ranks[0], ranks[1], ranks[2]), fitted_state.d_vine, config.context.rank_clip_epsilon
    )
    return score, previous_cusum_state


def _log_linear_scorer(
    ranks: tuple[RankValue, ...],
    config: ScientificConfig,
    previous_cusum_state: tuple[CusumState, ...],
    fitted_state: ComparatorFittedState | None,
) -> tuple[DetectorScore, tuple[CusumState, ...]]:
    return _log_linear_score(ranks, fitted_state), previous_cusum_state


def _hofd_scorer(
    ranks: tuple[RankValue, ...],
    config: ScientificConfig,
    previous_cusum_state: tuple[CusumState, ...],
    fitted_state: ComparatorFittedState | None,
) -> tuple[DetectorScore, tuple[CusumState, ...]]:
    return _hofd_score(ranks, config), previous_cusum_state


def _global_factor_scorer(
    ranks: tuple[RankValue, ...],
    config: ScientificConfig,
    previous_cusum_state: tuple[CusumState, ...],
    fitted_state: ComparatorFittedState | None,
) -> tuple[DetectorScore, tuple[CusumState, ...]]:
    if fitted_state is None or fitted_state.global_factor is None:
        raise ValueError("global factor residual reference requires a fitted comparator state")
    return global_factor_residual_score(ranks, fitted_state.global_factor), previous_cusum_state


def _multistream_cusum_scorer(
    ranks: tuple[RankValue, ...],
    config: ScientificConfig,
    previous_cusum_state: tuple[CusumState, ...],
    fitted_state: ComparatorFittedState | None,
) -> tuple[DetectorScore, tuple[CusumState, ...]]:
    states = tuple(
        next_cusum_state(
            previous,
            rank,
            config.comparators.multistream_cusum.rank_center,
            config.comparators.multistream_cusum.drift_subtraction,
        )
        for previous, rank in zip(
            previous_cusum_state
            or tuple(config.comparators.multistream_cusum.initial_state for _ in ranks),
            ranks,
            strict=True,
        )
    )
    return global_cusum_score(states), states


def validate_comparator_runtime_contracts(config: ScientificConfig) -> None:
    methods = comparator_methods_with_runtime()
    if len(methods) != len(set(methods)):
        raise ValueError("comparator runtime contract contains duplicate methods")
    nrmse_equivalence_criterion(0.0, config.materiality.hofd_equivalence.atom_nrmse_upper_margin)
    cosine_equivalence_criterion(1.0, config.materiality.hofd_equivalence.minimum_cosine_similarity)
    stopping_time_equivalence_criterion(
        0.0,
        0.0,
        config.materiality.hofd_equivalence.stopping_time_difference_interval_epochs[0],
        config.materiality.hofd_equivalence.stopping_time_difference_interval_epochs[1],
    )
    pfa_prerequisite_criterion(0.0, config.evidence.calibrated_finite_horizon.target_pfa)
    target_coalition_for_order(
        CoalitionOrder(config.study.maximum_coalition_order),
        config.experiments.pure_order_separation_validation.primary_client_count,
    )
    selection = config.experiments.strong_comparator_composition_challenge
    materialize_composition_record(
        selection.candidates[0],
        selection.artifact_filename,
    )
    selection_rule_identity(
        CompositionSelectionInputs(
            reference_theta=config.generators.pure_polynomial.primary_reference_theta,
            error_tie_tolerance=selection.error_tie_tolerance_standardized_units,
            runtime_tie_tolerance=selection.runtime_tie_tolerance_seconds,
            calibration_horizons_per_seed=(
                config.synthetic.sample_sizes.finite_horizon_calibration_horizons_per_seed
            ),
            heldout_null_horizons_per_seed=(
                config.synthetic.sample_sizes.finite_horizon_heldout_null_horizons_per_seed
            ),
            timed_scoring_rows=(
                config.synthetic.sample_sizes.pure_order_independent_evaluation_samples_per_condition_seed
            ),
            artifact_filename=selection.artifact_filename,
        )
    )
