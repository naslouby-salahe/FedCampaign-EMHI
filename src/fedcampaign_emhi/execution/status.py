from dataclasses import dataclass, replace

from fedcampaign_emhi.analysis.multiplicity import (
    multiplicity_contract as analysis_multiplicity_multiplicity_contract,
)
from fedcampaign_emhi.analysis.statistics import (
    statistics_contract as analysis_statistics_statistics_contract,
)
from fedcampaign_emhi.analysis.summaries import (
    summaries_contract as analysis_summaries_summaries_contract,
)
from fedcampaign_emhi.artifacts.dependencies import (
    dependencies_contract as artifacts_dependencies_dependencies_contract,
)
from fedcampaign_emhi.artifacts.provenance import (
    provenance_contract as artifacts_provenance_provenance_contract,
)
from fedcampaign_emhi.artifacts.records import (
    records_contract as artifacts_records_records_contract,
)
from fedcampaign_emhi.artifacts.storage import (
    storage_contract as artifacts_storage_storage_contract,
)
from fedcampaign_emhi.artifacts.validation import (
    validation_contract as artifacts_validation_validation_contract,
)
from fedcampaign_emhi.comparators.composition import (
    composition_contract as comparators_composition_composition_contract,
)
from fedcampaign_emhi.comparators.conditional_hofd import (
    conditional_hofd_contract as comparators_conditional_hofd_conditional_hofd_contract,
)
from fedcampaign_emhi.comparators.conditional_log_linear import (
    conditional_log_linear_contract as comparators_conditional_log_linear_conditional_log_linear_contract,
)
from fedcampaign_emhi.comparators.connected_information import (
    connected_information_contract as comparators_connected_information_connected_information_contract,
)
from fedcampaign_emhi.comparators.d_vine import (
    d_vine_contract as comparators_d_vine_d_vine_contract,
)
from fedcampaign_emhi.comparators.fedavg_autoencoder import (
    fedavg_autoencoder_contract as comparators_fedavg_autoencoder_fedavg_autoencoder_contract,
)
from fedcampaign_emhi.comparators.global_factor_residual import (
    global_factor_residual_contract as comparators_global_factor_residual_global_factor_residual_contract,
)
from fedcampaign_emhi.comparators.lancaster import (
    lancaster_contract as comparators_lancaster_lancaster_contract,
)
from fedcampaign_emhi.comparators.multistream_cusum import (
    multistream_cusum_contract as comparators_multistream_cusum_multistream_cusum_contract,
)
from fedcampaign_emhi.comparators.pair_dependence import (
    pair_dependence_contract as comparators_pair_dependence_pair_dependence_contract,
)
from fedcampaign_emhi.comparators.rank_fusion import (
    rank_fusion_contract as comparators_rank_fusion_rank_fusion_contract,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.datasets.campaigns import (
    campaigns_contract as datasets_campaigns_campaigns_contract,
)
from fedcampaign_emhi.datasets.edge_iiotset import (
    package_contract as datasets_edge_iiotset_package_contract,
)
from fedcampaign_emhi.datasets.edge_iiotset.canonicalization import (
    canonicalization_contract as datasets_edge_iiotset_canonicalization_canonicalization_contract,
)
from fedcampaign_emhi.datasets.edge_iiotset.ground_truth import (
    ground_truth_contract as datasets_edge_iiotset_ground_truth_ground_truth_contract,
)
from fedcampaign_emhi.datasets.edge_iiotset.loading import (
    loading_contract as datasets_edge_iiotset_loading_loading_contract,
)
from fedcampaign_emhi.datasets.edge_iiotset.validation import (
    validation_contract as datasets_edge_iiotset_validation_validation_contract,
)
from fedcampaign_emhi.datasets.partitions import epoch_index
from fedcampaign_emhi.datasets.preprocessing import chronological_partition_lengths
from fedcampaign_emhi.datasets.ton_iot_network import (
    package_contract as datasets_ton_iot_network_package_contract,
)
from fedcampaign_emhi.datasets.ton_iot_network.canonicalization import (
    canonicalization_contract as datasets_ton_iot_network_canonicalization_canonicalization_contract,
)
from fedcampaign_emhi.datasets.ton_iot_network.ground_truth import (
    ground_truth_contract as datasets_ton_iot_network_ground_truth_ground_truth_contract,
)
from fedcampaign_emhi.datasets.ton_iot_network.loading import (
    loading_contract as datasets_ton_iot_network_loading_loading_contract,
)
from fedcampaign_emhi.datasets.ton_iot_network.validation import (
    validation_contract as datasets_ton_iot_network_validation_validation_contract,
)
from fedcampaign_emhi.detection.fitting import (
    fitting_contract as detection_fitting_fitting_contract,
)
from fedcampaign_emhi.detection.local_policy import (
    local_policy_contract as detection_local_policy_local_policy_contract,
)
from fedcampaign_emhi.detection.scoring import (
    scoring_contract as detection_scoring_scoring_contract,
)
from fedcampaign_emhi.domain.enums import ExecutionRole, ExperimentName, ExperimentState
from fedcampaign_emhi.domain.types import ModuleContract, SeedCount
from fedcampaign_emhi.emhi.contexts import histogram_bin_index
from fedcampaign_emhi.emhi.evidence import signed_evidence_factor
from fedcampaign_emhi.emhi.innovation_calibration import (
    innovation_calibration_contract as emhi_innovation_calibration_innovation_calibration_contract,
)
from fedcampaign_emhi.emhi.innovations import (
    innovations_contract as emhi_innovations_innovations_contract,
)
from fedcampaign_emhi.emhi.ranks import clip_rank
from fedcampaign_emhi.emhi.sequential import (
    sequential_contract as emhi_sequential_sequential_contract,
)
from fedcampaign_emhi.emhi.thresholds import operating_point_unavailable_outcome
from fedcampaign_emhi.evaluation.benign_horizons import (
    benign_horizons_contract as evaluation_benign_horizons_benign_horizons_contract,
)
from fedcampaign_emhi.evaluation.campaign_replay import (
    campaign_replay_contract as evaluation_campaign_replay_campaign_replay_contract,
)
from fedcampaign_emhi.evaluation.records import (
    records_contract as evaluation_records_records_contract,
)
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
from fedcampaign_emhi.models.isolation_forest import (
    isolation_forest_contract as models_isolation_forest_isolation_forest_contract,
)
from fedcampaign_emhi.models.one_class_svm import (
    one_class_svm_contract as models_one_class_svm_one_class_svm_contract,
)
from fedcampaign_emhi.runtime.logging import logging_contract as runtime_logging_logging_contract
from fedcampaign_emhi.synthetic.common_mode import (
    common_mode_contract as synthetic_common_mode_common_mode_contract,
)
from fedcampaign_emhi.synthetic.context_boundaries import (
    context_boundaries_contract as synthetic_context_boundaries_context_boundaries_contract,
)
from fedcampaign_emhi.synthetic.controlled_campaigns import (
    controlled_campaigns_contract as synthetic_controlled_campaigns_controlled_campaigns_contract,
)
from fedcampaign_emhi.synthetic.pure_order import (
    pure_order_contract as synthetic_pure_order_pure_order_contract,
)
from fedcampaign_emhi.synthetic.robustness import (
    robustness_contract as synthetic_robustness_robustness_contract,
)
from fedcampaign_emhi.synthetic.self_explanation import (
    self_explanation_contract as synthetic_self_explanation_self_explanation_contract,
)
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


def module_contracts() -> tuple[ModuleContract, ...]:
    production_functions = (
        epoch_index,
        chronological_partition_lengths,
        clip_rank,
        histogram_bin_index,
        operating_point_unavailable_outcome,
        signed_evidence_factor,
    )
    if not production_functions:
        raise RuntimeError("production function surface is empty")
    return (
        analysis_multiplicity_multiplicity_contract(),
        analysis_statistics_statistics_contract(),
        analysis_summaries_summaries_contract(),
        artifacts_dependencies_dependencies_contract(),
        artifacts_provenance_provenance_contract(),
        artifacts_records_records_contract(),
        artifacts_storage_storage_contract(),
        artifacts_validation_validation_contract(),
        comparators_composition_composition_contract(),
        comparators_conditional_hofd_conditional_hofd_contract(),
        comparators_conditional_log_linear_conditional_log_linear_contract(),
        comparators_connected_information_connected_information_contract(),
        comparators_d_vine_d_vine_contract(),
        comparators_fedavg_autoencoder_fedavg_autoencoder_contract(),
        comparators_global_factor_residual_global_factor_residual_contract(),
        comparators_lancaster_lancaster_contract(),
        comparators_multistream_cusum_multistream_cusum_contract(),
        comparators_pair_dependence_pair_dependence_contract(),
        comparators_rank_fusion_rank_fusion_contract(),
        datasets_campaigns_campaigns_contract(),
        datasets_ton_iot_network_package_contract(),
        datasets_ton_iot_network_package_contract(),
        datasets_ton_iot_network_canonicalization_canonicalization_contract(),
        datasets_ton_iot_network_ground_truth_ground_truth_contract(),
        datasets_ton_iot_network_loading_loading_contract(),
        datasets_ton_iot_network_validation_validation_contract(),
        datasets_edge_iiotset_package_contract(),
        datasets_edge_iiotset_package_contract(),
        datasets_edge_iiotset_canonicalization_canonicalization_contract(),
        datasets_edge_iiotset_ground_truth_ground_truth_contract(),
        datasets_edge_iiotset_loading_loading_contract(),
        datasets_edge_iiotset_validation_validation_contract(),
        detection_fitting_fitting_contract(),
        detection_local_policy_local_policy_contract(),
        detection_scoring_scoring_contract(),
        emhi_innovation_calibration_innovation_calibration_contract(),
        emhi_innovations_innovations_contract(),
        emhi_sequential_sequential_contract(),
        evaluation_benign_horizons_benign_horizons_contract(),
        evaluation_campaign_replay_campaign_replay_contract(),
        evaluation_records_records_contract(),
        evaluation_scalability_scalability_contract(),
        evaluation_validation_validation_contract(),
        models_autoencoder_autoencoder_contract(),
        models_isolation_forest_isolation_forest_contract(),
        models_one_class_svm_one_class_svm_contract(),
        runtime_logging_logging_contract(),
        synthetic_common_mode_common_mode_contract(),
        synthetic_context_boundaries_context_boundaries_contract(),
        synthetic_controlled_campaigns_controlled_campaigns_contract(),
        synthetic_pure_order_pure_order_contract(),
        synthetic_robustness_robustness_contract(),
        synthetic_self_explanation_self_explanation_contract(),
        synthetic_validation_validation_contract(),
    )
