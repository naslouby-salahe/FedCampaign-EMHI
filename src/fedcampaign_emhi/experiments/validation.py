from fedcampaign_emhi.comparators.composition import select_strongest_comparator
from fedcampaign_emhi.comparators.conditional_hofd import hofd_atom_rows
from fedcampaign_emhi.comparators.conditional_log_linear import log_linear_design_column_count
from fedcampaign_emhi.comparators.connected_information import uniform_probability_table
from fedcampaign_emhi.comparators.contracts import comparator_method_contracts
from fedcampaign_emhi.comparators.d_vine import lexicographic_vine_order
from fedcampaign_emhi.comparators.fedavg_autoencoder import fedavg_weighted_mean
from fedcampaign_emhi.comparators.global_factor_residual import selected_factor_rank
from fedcampaign_emhi.comparators.hofd_equivalence import enumerate_hofd_equivalence_plan
from fedcampaign_emhi.comparators.lancaster import lancaster_triple_moment
from fedcampaign_emhi.comparators.multistream_cusum import next_cusum_state
from fedcampaign_emhi.comparators.pair_dependence import pair_dependence_moment
from fedcampaign_emhi.comparators.rank_fusion import mean_rank_fusion
from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.datasets.preprocessing import epoch_feature_vector
from fedcampaign_emhi.detection.detector_assignment import assign_detector_families
from fedcampaign_emhi.detection.fitting import (
    score_autoencoder,
    score_isolation_forest,
    score_one_class_svm,
)
from fedcampaign_emhi.domain.enums import ExperimentName
from fedcampaign_emhi.domain.types import ComponentName
from fedcampaign_emhi.experiments.ablations import (
    enumerate_exclusion_mechanism_ablation,
    enumerate_purification_and_order_ablation,
)
from fedcampaign_emhi.experiments.benign_robustness import enumerate_benign_common_mode_plan
from fedcampaign_emhi.experiments.boundaries import (
    enumerate_dropout_boundary_plan,
    enumerate_outside_contamination_plan,
)
from fedcampaign_emhi.experiments.definitions import experiment_registry
from fedcampaign_emhi.experiments.primary_odi import enumerate_primary_strict_odi_plan
from fedcampaign_emhi.experiments.scalability import enumerate_scalability_plan
from fedcampaign_emhi.experiments.secondary_generalization import enumerate_secondary_generalization_plan
from fedcampaign_emhi.experiments.sensitivity import enumerate_sensitivity_cells
from fedcampaign_emhi.experiments.strong_local import enumerate_strong_local_policy_plan
from fedcampaign_emhi.synthetic.common_mode import generate_common_mode_scores
from fedcampaign_emhi.synthetic.controlled_campaigns import apply_marginal_score_shift
from fedcampaign_emhi.synthetic.robustness import availability_mask
from fedcampaign_emhi.synthetic.self_explanation import enumerate_self_exclusion_grid


_IMPLEMENTATION_PROBES = (
    select_strongest_comparator,
    hofd_atom_rows,
    log_linear_design_column_count,
    uniform_probability_table,
    lexicographic_vine_order,
    fedavg_weighted_mean,
    selected_factor_rank,
    lancaster_triple_moment,
    next_cusum_state,
    pair_dependence_moment,
    mean_rank_fusion,
    epoch_feature_vector,
    assign_detector_families,
    score_autoencoder,
    score_isolation_forest,
    score_one_class_svm,
    generate_common_mode_scores,
    apply_marginal_score_shift,
    availability_mask,
    enumerate_self_exclusion_grid,
)


def implementation_probe_names() -> tuple[ComponentName, ...]:
    return tuple(f"{probe.__module__}.{probe.__name__}" for probe in _IMPLEMENTATION_PROBES)


def assert_known_experiment(config: ScientificConfig, experiment_name: ExperimentName) -> None:
    names = {contract.experiment_name for contract in experiment_registry(config)}
    if experiment_name not in names:
        raise ValueError(f"experiment {experiment_name.value} is not in the configured registry")


def validate_scientific_implementation_registry(
    config: ScientificConfig, experiment_name: ExperimentName
) -> tuple[ComponentName, ...]:
    assert_known_experiment(config, experiment_name)
    contracts = comparator_method_contracts()
    if len({contract.method_name for contract in contracts}) != len(contracts):
        raise ValueError("comparator method contracts must have unique method ownership")
    if not implementation_probe_names():
        raise ValueError("scientific implementation registry is empty")
    if experiment_name is ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION:
        enumerate_self_exclusion_grid(config)
    elif experiment_name is ExperimentName.EXCLUSION_MATCHED_HOFD_EQUIVALENCE:
        enumerate_hofd_equivalence_plan(config)
    elif experiment_name is ExperimentName.PRIMARY_STRICT_ODI_EVALUATION:
        enumerate_primary_strict_odi_plan(config)
    elif experiment_name is ExperimentName.EXCLUSION_MECHANISM_ABLATION:
        enumerate_exclusion_mechanism_ablation(config)
    elif experiment_name is ExperimentName.PURIFICATION_AND_ORDER_ABLATION:
        enumerate_purification_and_order_ablation(config)
    elif experiment_name is ExperimentName.CONTEXT_AND_ESTIMATOR_SENSITIVITY:
        enumerate_sensitivity_cells(config)
    elif experiment_name is ExperimentName.BENIGN_COMMON_MODE_ROBUSTNESS:
        enumerate_benign_common_mode_plan(config)
    elif experiment_name is ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE:
        enumerate_strong_local_policy_plan(config)
    elif experiment_name is ExperimentName.SECONDARY_CONTROLLED_TRACE_GENERALIZATION:
        enumerate_secondary_generalization_plan(config)
    elif experiment_name is ExperimentName.OUTSIDE_CAMPAIGN_CONTAMINATION_BOUNDARY:
        enumerate_outside_contamination_plan(config)
    elif experiment_name is ExperimentName.CLIENT_DROPOUT_AND_CONTEXT_SPARSITY_BOUNDARY:
        enumerate_dropout_boundary_plan(config)
    elif experiment_name is ExperimentName.COALITION_SCALABILITY:
        enumerate_scalability_plan(config)
    return implementation_probe_names()
