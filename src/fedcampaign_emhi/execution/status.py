from dataclasses import dataclass, replace

from fedcampaign_emhi.analysis.claims import evaluate_threshold_claim
from fedcampaign_emhi.analysis.multiplicity import holm_adjusted_p_values, holm_placeholder_p_value
from fedcampaign_emhi.analysis.statistics import (
    controlled_experimental_unit,
    exact_sign_pattern,
    monte_carlo_sign_flip_p_value,
    pairing_selected_clients,
    real_experimental_unit,
    seed_level_aggregate,
    sign_flip_p_value,
    two_sided_sign_flip_p_value,
)
from fedcampaign_emhi.analysis.summaries import (
    summaries_contract as analysis_summaries_summaries_contract,
)
from fedcampaign_emhi.artifacts.dependencies import descendant_ids
from fedcampaign_emhi.artifacts.provenance import manifests_are_compatible, material_fingerprint
from fedcampaign_emhi.artifacts.storage import file_sha256, payload_digest, write_atomic_json
from fedcampaign_emhi.artifacts.validation import inspect_artifact, may_reuse
from fedcampaign_emhi.comparators.composition import select_strongest_comparator
from fedcampaign_emhi.comparators.conditional_hofd import hofd_atom_rows
from fedcampaign_emhi.comparators.conditional_log_linear import log_linear_includes_triple
from fedcampaign_emhi.comparators.connected_information import uniform_probability_table
from fedcampaign_emhi.comparators.d_vine import gaussian_h_function, lexicographic_vine_order
from fedcampaign_emhi.comparators.fedavg_autoencoder import (
    fedavg_weighted_mean,
    optimizer_state_resets_each_round,
)
from fedcampaign_emhi.comparators.global_factor_residual import selected_factor_rank
from fedcampaign_emhi.comparators.lancaster import lancaster_triple_moment
from fedcampaign_emhi.comparators.multistream_cusum import next_cusum_state
from fedcampaign_emhi.comparators.pair_dependence import pair_dependence_moment
from fedcampaign_emhi.comparators.rank_fusion import max_rank_fusion, mean_rank_fusion
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.datasets.campaigns import merge_malicious_runs
from fedcampaign_emhi.datasets.edge_iiotset.canonicalization import (
    canonical_event_type as edge_iiotset_canonical_event_type,
)
from fedcampaign_emhi.datasets.edge_iiotset.ground_truth import edge_iiotset_ground_truth
from fedcampaign_emhi.datasets.edge_iiotset.loading import load_edge_iiotset_csv
from fedcampaign_emhi.datasets.edge_iiotset.validation import (
    schema_is_executable as edge_iiotset_schema_is_executable,
)
from fedcampaign_emhi.datasets.partitions import epoch_index
from fedcampaign_emhi.datasets.preprocessing import chronological_partition_lengths
from fedcampaign_emhi.datasets.ton_iot_network.canonicalization import (
    canonical_event_type as ton_iot_network_canonical_event_type,
)
from fedcampaign_emhi.datasets.ton_iot_network.canonicalization import (
    event_type_hash_bucket,
)
from fedcampaign_emhi.datasets.ton_iot_network.ground_truth import ton_iot_network_ground_truth
from fedcampaign_emhi.datasets.ton_iot_network.loading import load_ton_iot_network_csv
from fedcampaign_emhi.datasets.ton_iot_network.validation import (
    schema_is_executable as ton_iot_network_schema_is_executable,
)
from fedcampaign_emhi.detection.fitting import (
    fitting_contract as detection_fitting_fitting_contract,
)
from fedcampaign_emhi.detection.local_policy import first_local_stop_epoch, persistence_is_triggered
from fedcampaign_emhi.detection.scoring import oriented_score_stream
from fedcampaign_emhi.domain.enums import ExecutionRole, ExperimentName, ExperimentState
from fedcampaign_emhi.domain.types import ModuleContract, SeedCount
from fedcampaign_emhi.emhi.contexts import histogram_bin_index
from fedcampaign_emhi.emhi.evidence import signed_evidence_factor
from fedcampaign_emhi.emhi.innovation_calibration import (
    innovation_calibration_contract as emhi_innovation_calibration_innovation_calibration_contract,
)
from fedcampaign_emhi.emhi.innovations import center_and_scale_atom
from fedcampaign_emhi.emhi.ranks import clip_rank
from fedcampaign_emhi.emhi.sequential import (
    first_global_stop_epoch,
    next_global_state,
    statistical_stop,
)
from fedcampaign_emhi.emhi.thresholds import operating_point_unavailable_outcome
from fedcampaign_emhi.evaluation.benign_horizons import (
    benign_horizons_contract as evaluation_benign_horizons_benign_horizons_contract,
)
from fedcampaign_emhi.evaluation.campaign_replay import (
    campaign_replay_contract as evaluation_campaign_replay_campaign_replay_contract,
)
from fedcampaign_emhi.evaluation.records import global_detection_without_odi, odi_evaluation_record
from fedcampaign_emhi.evaluation.scalability import (
    scalability_contract as evaluation_scalability_scalability_contract,
)
from fedcampaign_emhi.evaluation.validation import (
    validation_contract as evaluation_validation_validation_contract,
)
from fedcampaign_emhi.execution.planning import plan_experiments
from fedcampaign_emhi.models.autoencoder import (
    autoencoder_contract as models_autoencoder_autoencoder_contract,
)
from fedcampaign_emhi.models.isolation_forest import isolation_forest_anomaly_scores
from fedcampaign_emhi.models.one_class_svm import one_class_svm_anomaly_scores
from fedcampaign_emhi.runtime.logging import logging_contract as runtime_logging_logging_contract
from fedcampaign_emhi.synthetic.common_mode import equally_spaced_loadings
from fedcampaign_emhi.synthetic.context_boundaries import next_markov_state
from fedcampaign_emhi.synthetic.controlled_campaigns import (
    apply_single_client_score_shift,
    marginal_campaign_targets,
)
from fedcampaign_emhi.synthetic.pure_order import (
    polynomial_density_is_valid,
    polynomial_scale,
    pure_order_one_response,
)
from fedcampaign_emhi.synthetic.robustness import contaminated_outside_count, round_half_up
from fedcampaign_emhi.synthetic.self_explanation import analytic_direct_derivative
from fedcampaign_emhi.synthetic.validation import (
    validation_contract as synthetic_validation_validation_contract,
)


@dataclass(frozen=True)
class ExperimentStatus:
    experiment_name: ExperimentName
    state: ExperimentState
    development_seed_count: SeedCount
    confirmatory_seed_count: SeedCount


def project_status(loaded: LoadedScientificConfiguration) -> tuple[ExperimentStatus, ...]:
    statuses: list[ExperimentStatus] = []
    for planned in plan_experiments(loaded):
        existing_index = next(
            (
                index
                for index, item in enumerate(statuses)
                if item.experiment_name is planned.experiment_name
            ),
            None,
        )
        if existing_index is None:
            development = planned.seed_count
            confirmatory = 0
            if planned.execution_role is ExecutionRole.CONFIRMATORY:
                development = 0
                confirmatory = planned.seed_count
            statuses.append(
                ExperimentStatus(
                    experiment_name=planned.experiment_name,
                    state=planned.state,
                    development_seed_count=development,
                    confirmatory_seed_count=confirmatory,
                )
            )
            continue
        current = statuses[existing_index]
        if planned.execution_role is ExecutionRole.CONFIRMATORY:
            statuses[existing_index] = replace(current, confirmatory_seed_count=planned.seed_count)
        else:
            statuses[existing_index] = replace(
                current,
                development_seed_count=max(current.development_seed_count, planned.seed_count),
            )
    return tuple(statuses)


ARTIFACT_OWNERSHIP = "artifact identity, persistence, validation, path, and provenance"
DATASET_ADAPTER_OWNERSHIP = "dataset adapter contract"


def module_contracts() -> tuple[ModuleContract, ...]:
    production_functions = (
        epoch_index,
        chronological_partition_lengths,
        clip_rank,
        histogram_bin_index,
        operating_point_unavailable_outcome,
        signed_evidence_factor,
        descendant_ids,
        material_fingerprint,
        manifests_are_compatible,
        file_sha256,
        payload_digest,
        write_atomic_json,
        inspect_artifact,
        may_reuse,
        next_global_state,
        statistical_stop,
        holm_adjusted_p_values,
        holm_placeholder_p_value,
        exact_sign_pattern,
        sign_flip_p_value,
        monte_carlo_sign_flip_p_value,
        seed_level_aggregate,
        two_sided_sign_flip_p_value,
        controlled_experimental_unit,
        pairing_selected_clients,
        real_experimental_unit,
        edge_iiotset_canonical_event_type,
        edge_iiotset_ground_truth,
        load_edge_iiotset_csv,
        edge_iiotset_schema_is_executable,
        ton_iot_network_canonical_event_type,
        event_type_hash_bucket,
        ton_iot_network_ground_truth,
        load_ton_iot_network_csv,
        ton_iot_network_schema_is_executable,
        mean_rank_fusion,
        max_rank_fusion,
        merge_malicious_runs,
        persistence_is_triggered,
        equally_spaced_loadings,
        next_cusum_state,
        select_strongest_comparator,
        selected_factor_rank,
        center_and_scale_atom,
        isolation_forest_anomaly_scores,
        one_class_svm_anomaly_scores,
        lancaster_triple_moment,
        pair_dependence_moment,
        oriented_score_stream,
        evaluate_threshold_claim,
        pure_order_one_response,
        first_global_stop_epoch,
        first_local_stop_epoch,
        global_detection_without_odi,
        odi_evaluation_record,
        next_markov_state,
        apply_single_client_score_shift,
        marginal_campaign_targets,
        polynomial_density_is_valid,
        polynomial_scale,
        contaminated_outside_count,
        round_half_up,
        analytic_direct_derivative,
        hofd_atom_rows,
        log_linear_includes_triple,
        uniform_probability_table,
        gaussian_h_function,
        lexicographic_vine_order,
        fedavg_weighted_mean,
        optimizer_state_resets_each_round,
    )
    if not production_functions:
        raise RuntimeError("production function surface is empty")
    return (
        ModuleContract(
            module_name="fedcampaign_emhi.analysis.multiplicity",
            ownership="deterministic Holm-family correction and adjusted p-value computation",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.analysis.statistics",
            ownership="sign-flip inference, intervals, effects, and equivalence procedures",
        ),
        analysis_summaries_summaries_contract(),
        ModuleContract(
            module_name="fedcampaign_emhi.artifacts.dependencies",
            ownership=ARTIFACT_OWNERSHIP,
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.artifacts.provenance",
            ownership=ARTIFACT_OWNERSHIP,
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.artifacts.records",
            ownership=ARTIFACT_OWNERSHIP,
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.artifacts.storage",
            ownership=ARTIFACT_OWNERSHIP,
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.artifacts.validation",
            ownership=ARTIFACT_OWNERSHIP,
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.comparators.composition",
            ownership="materializes the predeclared strongest-comparator composition using fixed selection rules",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.comparators.conditional_hofd",
            ownership="exclusion-matched conditional HOFD equivalence comparison",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.comparators.conditional_log_linear",
            ownership="conditional log-linear interaction reference",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.comparators.connected_information",
            ownership="connected-information reference",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.comparators.d_vine",
            ownership="D-vine conditional-dependence reference",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.comparators.fedavg_autoencoder",
            ownership="unmatched FedAvg autoencoder comparator",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.comparators.global_factor_residual",
            ownership="PCA global-factor residualization and deterministic rank selection",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.comparators.lancaster",
            ownership="Lancaster higher-order interaction reference",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.comparators.multistream_cusum",
            ownership="roadmap-defined multistream CUSUM sequential baseline",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.comparators.pair_dependence",
            ownership="conditional order-two dependence predecessor",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.comparators.rank_fusion",
            ownership="roadmap-defined marginal rank-fusion references",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.datasets.campaigns",
            ownership="campaign merging, eligibility, warm-up, activity, and evaluation-horizon semantics",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.datasets.ton_iot_network",
            ownership="dataset adapter",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.datasets.ton_iot_network.canonicalization",
            ownership=DATASET_ADAPTER_OWNERSHIP,
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.datasets.ton_iot_network.ground_truth",
            ownership=DATASET_ADAPTER_OWNERSHIP,
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.datasets.ton_iot_network.loading",
            ownership=DATASET_ADAPTER_OWNERSHIP,
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.datasets.ton_iot_network.validation",
            ownership=DATASET_ADAPTER_OWNERSHIP,
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.datasets.edge_iiotset",
            ownership="dataset adapter",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.datasets.edge_iiotset.canonicalization",
            ownership=DATASET_ADAPTER_OWNERSHIP,
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.datasets.edge_iiotset.ground_truth",
            ownership=DATASET_ADAPTER_OWNERSHIP,
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.datasets.edge_iiotset.loading",
            ownership=DATASET_ADAPTER_OWNERSHIP,
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.datasets.edge_iiotset.validation",
            ownership=DATASET_ADAPTER_OWNERSHIP,
        ),
        detection_fitting_fitting_contract(),
        ModuleContract(
            module_name="fedcampaign_emhi.detection.local_policy",
            ownership="calibrates and evaluates primary and strong local stopping policies",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.detection.scoring",
            ownership="produces deterministic reusable detector score streams",
        ),
        emhi_innovation_calibration_innovation_calibration_contract(),
        ModuleContract(
            module_name="fedcampaign_emhi.emhi.innovations",
            ownership="purified hierarchical innovation atoms and centered/scaled representations",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.emhi.sequential",
            ownership="sequential recursion, distributed support, and stopping-time semantics",
        ),
        evaluation_benign_horizons_benign_horizons_contract(),
        evaluation_campaign_replay_campaign_replay_contract(),
        ModuleContract(
            module_name="fedcampaign_emhi.evaluation.records",
            ownership="typed immutable campaign, horizon, stop, evidence, latency, coverage, and evaluation records",
        ),
        evaluation_scalability_scalability_contract(),
        evaluation_validation_validation_contract(),
        models_autoencoder_autoencoder_contract(),
        ModuleContract(
            module_name="fedcampaign_emhi.models.isolation_forest",
            ownership="Isolation Forest construction, fitting, persistence, and anomaly-score orientation",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.models.one_class_svm",
            ownership="RBF One-Class SVM construction, fitting, persistence, and anomaly-score orientation",
        ),
        runtime_logging_logging_contract(),
        ModuleContract(
            module_name="fedcampaign_emhi.synthetic.common_mode",
            ownership="latent common-mode benign coordination and count-stress scenarios",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.synthetic.context_boundaries",
            ownership="estimator-support, context-support, and numerical-feasibility boundary scenarios",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.synthetic.controlled_campaigns",
            ownership="controlled campaign alternatives and interaction structures",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.synthetic.pure_order",
            ownership="polynomial, XOR, context-dependent, and mixed pure-order alternatives",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.synthetic.robustness",
            ownership="outside-contamination, dropout, and context-sparsity robustness scenarios",
        ),
        ModuleContract(
            module_name="fedcampaign_emhi.synthetic.self_explanation",
            ownership="exact-exclusion versus inclusive-context self-explanation experiments",
        ),
        synthetic_validation_validation_contract(),
    )
