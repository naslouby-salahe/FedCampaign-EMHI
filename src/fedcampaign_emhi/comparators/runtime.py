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
    cosine_equivalence_criterion,
    gaussian_h_function,
    global_factor_residual_scores,
    hofd_atom_rows,
    ipf_converged,
    iterative_proportional_fitting_step,
    jeffreys_smoothed_probabilities,
    lancaster_triple_moment,
    lancaster_triple_nonconformity,
    lexicographic_vine_order,
    log_linear_design_column_count,
    nrmse_equivalence_criterion,
    pair_dependence_moment,
    pair_dependence_nonconformity,
    pfa_prerequisite_criterion,
    selected_factor_rank,
    stopping_time_equivalence_criterion,
    target_coalition_for_order,
    uniform_probability_table,
)
from fedcampaign_emhi.comparators.federated import (
    fedavg_weighted_mean,
    federated_autoencoder_widths,
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
    ClientId,
    CusumState,
    DetectorScore,
    RankValue,
)
from fedcampaign_emhi.emhi.projection import proper_subset_design_row
from fedcampaign_emhi.emhi.structure import tensor_representation


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
    ranks: tuple[RankValue, ...], config: ScientificConfig
) -> DetectorScore:
    if len(ranks) != 3:
        raise ValueError("connected information requires three ranks")
    bin_count = config.comparators.connected_information.bins_per_client
    counts = [[[0.0 for _ in range(bin_count)] for _ in range(bin_count)] for _ in range(bin_count)]
    counts[_rank_bin(ranks[0], bin_count)][_rank_bin(ranks[1], bin_count)][
        _rank_bin(ranks[2], bin_count)
    ] = 1.0
    smoothed = jeffreys_smoothed_probabilities(
        tuple(tuple(tuple(row) for row in layer) for layer in counts),
        config.comparators.connected_information.jeffreys_pseudocount_per_cell,
    )
    uniform = uniform_probability_table(bin_count)
    target_pair = tuple(
        tuple(sum(uniform[i][j][k] for k in range(bin_count)) for j in range(bin_count))
        for i in range(bin_count)
    )
    fitted = iterative_proportional_fitting_step(uniform, target_pair)
    if not ipf_converged(
        fitted,
        target_pair,
        config.comparators.connected_information.maximum_marginal_absolute_error,
    ):
        raise ValueError("connected-information IPF did not converge")
    indexes = tuple(_rank_bin(rank, bin_count) for rank in ranks)
    numerator = smoothed[indexes[0]][indexes[1]][indexes[2]]
    denominator = fitted[indexes[0]][indexes[1]][indexes[2]]
    return abs(log(numerator / denominator))


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
) -> tuple[DetectorScore, tuple[CusumState, ...]]:
    if not ranks:
        raise ValueError("comparator scoring requires at least one rank")
    if method_name is MethodName.RAW_MEAN_RANK_FUSION:
        return mean_rank_fusion(ranks), previous_cusum_state
    if method_name is MethodName.RAW_MAX_RANK_FUSION:
        return max_rank_fusion(ranks), previous_cusum_state
    if method_name is MethodName.CONDITIONAL_PAIR_DEPENDENCE:
        if len(ranks) < 2:
            raise ValueError("pair comparator requires two ranks")
        moment = pair_dependence_moment(ranks[0], ranks[1])
        score = pair_dependence_nonconformity(
            moment,
            0.0,
            1.0,
            config.numerics.metric_denominator_floor,
        )
        return score, previous_cusum_state
    if method_name is MethodName.EXCLUSION_MATCHED_LANCASTER_TRIPLE:
        if len(ranks) < 3:
            raise ValueError("Lancaster comparator requires three ranks")
        moment = lancaster_triple_moment(ranks[0], ranks[1], ranks[2])
        return (
            lancaster_triple_nonconformity(
                moment,
                0.0,
                1.0,
                config.numerics.metric_denominator_floor,
            ),
            previous_cusum_state,
        )
    if method_name is MethodName.CONNECTED_INFORMATION_REFERENCE:
        return _connected_information_score(ranks, config), previous_cusum_state
    if method_name is MethodName.D_VINE_CONDITIONAL_REFERENCE:
        if len(ranks) < 3:
            raise ValueError("D-vine comparator requires three ranks")
        ordered: tuple[ClientId, ...] = tuple(f"client-{index}" for index in range(len(ranks)))
        lexicographic_vine_order(ordered[:3])
        left = gaussian_h_function(ranks[0], ranks[1], 0.0, config.context.rank_clip_epsilon)
        right = gaussian_h_function(ranks[2], ranks[1], 0.0, config.context.rank_clip_epsilon)
        return abs(left - right), previous_cusum_state
    if method_name is MethodName.CONDITIONAL_LOG_LINEAR_REFERENCE:
        log_linear_design_column_count(config.basis.primary_size)
        return abs(mean_rank_fusion(ranks) - 0.5), previous_cusum_state
    if method_name is MethodName.EXCLUSION_MATCHED_CONDITIONAL_HOFD:
        return _hofd_score(ranks, config), previous_cusum_state
    if method_name is MethodName.GLOBAL_FACTOR_RESIDUAL_REFERENCE:
        factor_rank = selected_factor_rank(
            (1.0,),
            config.comparators.global_factor_residual.cumulative_variance_target,
            config.comparators.global_factor_residual.fallback_rank,
            config.comparators.global_factor_residual.candidate_ranks,
        )
        return global_factor_residual_scores((tuple(ranks),), factor_rank)[0], previous_cusum_state
    if method_name is MethodName.MULTISTREAM_CUSUM_REFERENCE:
        states = tuple(
            next_cusum_state(
                previous,
                rank,
                config.comparators.multistream_cusum.rank_center,
                config.comparators.multistream_cusum.drift_subtraction,
            )
            for previous, rank in zip(
                previous_cusum_state or tuple(0.0 for _ in ranks), ranks, strict=True
            )
        )
        return global_cusum_score(states), states
    if method_name is MethodName.FEDAVG_AUTOENCODER_REFERENCE:
        federated_autoencoder_widths(config.datasets.preprocessing.event_type_hash_bucket_count + 2)
        averaged = fedavg_weighted_mean(
            tuple((rank,) for rank in ranks),
            tuple(1 for _ in ranks),
        )
        return averaged[0], previous_cusum_state
    if method_name in {
        MethodName.FULL_FEDCAMPAIGN_EMHI,
        MethodName.EXCLUSION_MATCHED_ORDER_ONE_EMHI,
        MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI,
        MethodName.INCLUSIVE_CONTEXT_FULL_HIERARCHY,
        MethodName.LEAVE_ONE_OUT_INSUFFICIENT_EXCLUSION,
        MethodName.PARTIAL_COALITION_EXCLUSION,
        MethodName.NO_PROPER_SUBSET_PURIFICATION,
        MethodName.NO_OUTSIDE_CONTEXT_FULL_HIERARCHY,
    }:
        raise ValueError("EMHI methods require a fitted EMHI artifact")
    raise ValueError(f"unsupported comparator method {method_name.value}")


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
