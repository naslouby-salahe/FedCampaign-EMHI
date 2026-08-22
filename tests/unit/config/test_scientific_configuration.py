from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from fedcampaign_emhi.config.loading import (
    configuration_digest,
    histogram_edges,
    load_production_configuration,
    load_smoke_configuration,
    load_tests_configuration,
    minimum_zero_false_stop_horizons,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration, ScientificConfig
from fedcampaign_emhi.config.validation import (
    ConfigurationValidationError,
    reject_forbidden_derived_keys,
    validate_scientific_config,
)
from fedcampaign_emhi.domain.enums import (
    ConfigurationProfile,
    DatasetName,
    MethodName,
)


def test_production_configuration_loads_locked_core_values(
    production_configuration: LoadedScientificConfiguration,
) -> None:
    values = production_configuration.values
    assert production_configuration.profile == ConfigurationProfile.PRODUCTION.value
    assert values.study.maximum_coalition_order == 3
    assert values.time.real_data_epoch_seconds == 60
    assert values.campaign.evaluation_horizon_epochs == 60
    assert values.campaign.prestart_warmup_epochs == 200
    assert values.distributed_support.minimum_clients == 2
    assert values.distributed_support.material_coalition_evidence_threshold == 1.25
    assert values.context.rank_clip_epsilon == 1.0e-12
    assert values.context.outside_histogram_bin_count == 8
    assert values.basis.primary_size == 3
    assert values.evidence.clip_bound == 1.0
    assert values.evidence.bet_lambda == 0.5
    assert values.evidence.calibrated_finite_horizon.target_pfa == 0.05
    assert values.datasets.primary.name is DatasetName.TON_IOT_NETWORK
    assert values.datasets.secondary.name is DatasetName.EDGE_IIOTSET
    assert values.detectors.isolation_forest.trees == 300
    assert values.randomness.engineering_smoke_root == 999
    assert values.randomness.statistical_analysis_base_seed == 3000
    assert values.randomness.context_base_seed == 4100
    assert values.numerics.metric_denominator_floor == 1.0e-12
    assert values.statistics.bootstrap_replicates == 10000
    assert values.runtime.automatic_technical_retries_after_initial_failure == 2
    assert values.reporting.precision.probabilities_and_rates_decimals == 3
    assert (
        values.experiments.primary_strict_odi_evaluation.methods[0]
        is MethodName.FULL_FEDCAMPAIGN_EMHI
    )


def test_derived_values_are_owned_by_implementation(
    production_configuration: LoadedScientificConfiguration,
) -> None:
    derived = production_configuration.derived
    assert derived.model_input_dimension == 66
    assert derived.heldout_benign_is_remainder is True
    assert derived.local_horizon_epochs == 60
    assert derived.synthetic_campaign_horizon_epochs == 60
    assert derived.synthetic_campaign_warmup_epochs == 200
    assert derived.synthetic_development_seed_count == 30
    assert derived.synthetic_confirmatory_seed_count == 30
    assert derived.real_development_seed_count == 10
    assert derived.real_confirmatory_seed_count == 10
    assert derived.exact_real_sign_flip_assignment_count == 1024
    assert derived.minimum_nonoverlapping_horizons_for_zero_false_stop == 59
    assert derived.signed_theorem_e_sr_threshold == 1000.0
    assert derived.signed_theorem_compensator == 0.125
    assert derived.histogram_edge_count == 9
    assert derived.outside_histogram_edges == histogram_edges(8)
    assert derived.primary_odi_table_method_order == (
        production_configuration.values.experiments.primary_strict_odi_evaluation.methods
    )
    assert derived.context_seed == 4100
    assert minimum_zero_false_stop_horizons(0.05, 0.95) == 59


def test_unknown_fields_are_rejected(repo_root: Path) -> None:
    payload = yaml.safe_load((repo_root / "configs" / "fedcampaign-emhi.yaml").read_text())
    payload["study"]["undocumented_knob"] = 1
    with pytest.raises(ValidationError):
        ScientificConfig.model_validate(payload)


def test_derived_keys_are_rejected(repo_root: Path) -> None:
    payload = yaml.safe_load((repo_root / "configs" / "fedcampaign-emhi.yaml").read_text())
    payload["model_input_dimension"] = 66
    with pytest.raises(ConfigurationValidationError):
        reject_forbidden_derived_keys(payload)


def test_digest_is_deterministic(
    production_configuration: LoadedScientificConfiguration,
) -> None:
    again = configuration_digest(production_configuration.values)
    assert again == production_configuration.material_digest
    assert len(production_configuration.material_digest) == 64


def test_reduced_configs_cannot_replace_production() -> None:
    production = load_production_configuration()
    tests = load_tests_configuration()
    smoke = load_smoke_configuration()
    assert tests.profile != production.profile
    assert smoke.profile != production.profile
    assert tests.material_digest != production.material_digest
    assert smoke.material_digest != production.material_digest
    assert production.values.claim_materiality.primary_real.minimum_strict_odi_rate == 0.2


def test_partition_fractions_leave_heldout_remainder(repo_root: Path) -> None:
    payload = deepcopy(
        yaml.safe_load((repo_root / "configs" / "fedcampaign-emhi.yaml").read_text())
    )
    payload["datasets"]["preprocessing"]["benign_partition_fractions"] = {
        "detector_fit": 0.4,
        "nuisance_fit": 0.4,
        "threshold_and_policy_calibration": 0.3,
    }
    config = ScientificConfig.model_validate(payload)
    with pytest.raises(ConfigurationValidationError):
        validate_scientific_config(config)


def test_locked_core_scientific_configuration(
    production_configuration: LoadedScientificConfiguration,
) -> None:
    values = production_configuration.values
    assert values.study.maximum_coalition_order == 3
    assert values.time.real_data_epoch_seconds == 60
    assert values.campaign.evaluation_horizon_epochs == 60
    assert values.campaign.prestart_warmup_epochs == 200
    assert values.campaign.merge_max_intervening_benign_epochs == 10
    assert values.campaign.distributed_first_activity_window_epochs == 10
    assert values.campaign.minimum_duration_epochs == 3
    assert values.distributed_support.minimum_clients == 2
    assert values.distributed_support.trailing_window_epochs == 5
    assert values.distributed_support.material_coalition_evidence_threshold == 1.25
    assert values.context.outside_lag_epochs == 1
    assert values.context.minimum_available_outside_clients == 2
    assert values.context.minimum_available_outside_fraction == 0.5
    assert values.context.rank_clip_epsilon == 1.0e-12
    assert values.context.outside_histogram_bin_count == 8
    assert values.context.primary_cell_count == 4
    assert values.context.cell_count_sensitivity == (2, 8)
    assert values.context.kmeans.n_init == 20
    assert values.context.kmeans.max_iterations == 300
    assert values.context.kmeans.tolerance == 0.0001
    assert values.context.kmeans.max_fit_rows == 200000
    assert values.context.kmeans.assignment_tie_tolerance == 1.0e-12
    assert values.context.minimum_support_epochs.order_one == 100
    assert values.context.minimum_support_epochs.order_two == 200
    assert values.context.minimum_support_epochs.order_three == 400
    assert values.context.nuisance_crossfit.fold_count == 5
    assert values.basis.primary_size == 3
    assert values.basis.sensitivity_sizes == (2, 4)
    assert values.projection.ridge_candidates == (0.0, 0.0001, 0.001, 0.01, 0.1, 1.0)
    assert values.projection.cross_validation.fold_count == 5
    assert values.projection.selection_tie_tolerance_mse == 1.0e-12
    assert values.projection.zero_ridge_svd_relative_cutoff == 1.0e-12
    assert values.projection.maximum_gram_condition_number == 1000000.0
    assert values.projection.atom_scale_floor == 1.0e-06
    assert values.projection.norm_reference_floor == 1.0e-06
    assert values.evidence.clip_bound == 1.0
    assert values.evidence.bet_lambda == 0.5
    assert values.evidence.operational_norm_reference_quantile == 0.95
    assert values.evidence.signed_theorem_sequential.arl_alpha == 0.001
    assert values.evidence.calibrated_finite_horizon.target_pfa == 0.05
    assert values.evidence.calibrated_finite_horizon.calibration_confidence == 0.95
    assert values.evidence.calibrated_finite_horizon.threshold_candidates == (
        2,
        3,
        5,
        10,
        20,
        50,
        100,
        200,
        500,
        1000,
    )
    assert values.evidence.no_stop_plot_offset_epochs == 1
    assert values.datasets.primary.name is DatasetName.TON_IOT_NETWORK
    assert values.datasets.primary.raw_directory == "data/raw/ton_iot_network"
    assert values.datasets.primary.target_client_count == 12
    assert values.datasets.secondary.name is DatasetName.EDGE_IIOTSET
    assert values.datasets.secondary.raw_directory == "data/raw/edge_iiotset"
    assert values.datasets.secondary.target_client_count == 12
    assert values.datasets.secondary.minimum_eligible_client_count == 6
    assert values.datasets.external_checksums_directory == "data/external_checksums"
    assert values.datasets.eligibility.minimum_benign_event_records == 5000
    assert values.datasets.eligibility.minimum_nonempty_benign_epochs == 600
    assert values.datasets.preprocessing.event_type_hash_bucket_count == 64
    assert values.datasets.preprocessing.robust_scaling_iqr_floor == 1.0e-06
    assert values.datasets.preprocessing.benign_partition_fractions.detector_fit == 0.1
    assert values.datasets.preprocessing.benign_partition_fractions.nuisance_fit == 0.18
    assert (
        values.datasets.preprocessing.benign_partition_fractions.threshold_and_policy_calibration
        == 0.36
    )
    assert values.detectors.isolation_forest.trees == 300
    assert values.detectors.isolation_forest.max_samples_cap == 256
    assert values.detectors.isolation_forest.max_features == 1.0
    assert values.detectors.isolation_forest.jobs == 1
    assert values.detectors.one_class_svm.nu == 0.01
    assert values.detectors.one_class_svm.coefficient_zero == 0.0
    assert values.detectors.one_class_svm.solver_tolerance == 0.001
    assert values.detectors.one_class_svm.kernel_cache_mib == 1024
    assert values.detectors.one_class_svm.max_iterations == -1
    assert values.detectors.autoencoder.learning_rate == 0.001
    assert values.detectors.autoencoder.betas == (0.9, 0.999)
    assert values.detectors.autoencoder.optimizer_epsilon == 1.0e-08
    assert values.detectors.autoencoder.weight_decay == 0.0
    assert values.detectors.autoencoder.batch_size == 128
    assert values.detectors.autoencoder.epochs == 50
    assert values.local_policy.candidate_score_quantiles == (0.99, 0.995, 0.999, 0.9995, 0.9999)
    assert tuple(
        (item.required_exceedances, item.window_epochs)
        for item in values.local_policy.candidate_persistence
    ) == ((1, 1), (2, 3), (3, 5))
    assert values.local_policy.primary_horizon_pfa_target == 0.05
    assert values.local_policy.strong_horizon_pfa_target == 0.1
    assert values.local_policy.pfa_confidence == 0.95


def test_locked_randomness_synthetic_and_numerics(
    production_configuration: LoadedScientificConfiguration,
) -> None:
    values = production_configuration.values
    assert values.randomness.synthetic_development_roots == tuple(range(1000, 1030))
    assert values.randomness.synthetic_confirmatory_roots == tuple(range(9000, 9030))
    assert values.randomness.real_development_roots == tuple(range(10))
    assert values.randomness.real_confirmatory_roots == tuple(range(9000, 9010))
    assert values.randomness.engineering_smoke_root == 999
    assert values.randomness.statistical_analysis_base_seed == 3000
    assert values.randomness.context_base_seed == 4100
    sizes = values.synthetic.sample_sizes
    assert sizes.generic_nuisance_fit_epochs == 8000
    assert sizes.generic_cross_fitted_evaluation_epochs == 4000
    assert sizes.finite_horizon_calibration_horizons_per_seed == 200
    assert sizes.finite_horizon_heldout_null_horizons_per_seed == 1000
    assert sizes.self_explanation_epochs_per_perturbation == 600
    assert sizes.self_explanation_lag_settling_epochs_discarded == 20
    assert sizes.pure_order_independent_evaluation_samples_per_condition_seed == 10000
    assert sizes.hofd_equivalence_heldout_samples_per_context_seed == 4000
    assert sizes.estimator_evaluation_samples_per_context_seed == 4000
    assert values.generators.common_mode.latent_ar_coefficient == 0.8
    assert values.generators.common_mode.client_loading_minimum == 0.6
    assert values.generators.common_mode.client_loading_maximum == 1.0
    assert values.generators.common_mode.client_noise_standard_deviation == 0.75
    assert values.generators.controlled_campaigns.marginal.score_shift == 1.0
    assert values.generators.controlled_campaigns.pair_relation.benign_correlation == 0.0
    assert values.generators.controlled_campaigns.pair_relation.campaign_correlation == 0.6
    assert values.generators.controlled_campaigns.single_client.score_shift == 2.0
    assert values.generators.self_explanation.perturbations == (
        -0.2,
        -0.1,
        -0.05,
        0.0,
        0.05,
        0.1,
        0.2,
    )
    assert values.generators.self_explanation.derivative_regression_perturbations == (
        -0.1,
        -0.05,
        0.0,
        0.05,
        0.1,
    )
    assert values.generators.pure_polynomial.theta.order_one == (0.0, 0.05, 0.1, 0.2, 0.4)
    assert values.generators.pure_polynomial.theta.order_two == (0.0, 0.05, 0.1, 0.2, 0.3)
    assert values.generators.pure_polynomial.theta.order_three == (
        0.0,
        0.025,
        0.05,
        0.1,
        0.15,
        0.18,
    )
    assert values.generators.pure_polynomial.primary_reference_theta == 0.1
    assert values.generators.xor.strengths == (0.0, 0.25, 0.5, 0.75, 1.0)
    assert values.generators.xor.primary_reference_strength == 0.5
    assert values.generators.mixed_order.enabled_term_sets == ((1, 2), (1, 3), (2, 3), (1, 2, 3))
    assert values.generators.mixed_order.term_coefficient == 0.05
    assert values.generators.context_dependent_triple.markov_same_probability == 0.9
    assert (
        values.generators.context_dependent_triple.initial_state_probabilities.negative_one == 0.5
    )
    assert (
        values.generators.context_dependent_triple.initial_state_probabilities.positive_one == 0.5
    )
    assert values.generators.context_dependent_triple.primary_theta == 0.1
    assert values.generators.context_dependent_triple.outside_rank_intervals.negative_state == (
        0.25,
        0.35,
    )
    assert values.generators.context_dependent_triple.outside_rank_intervals.positive_state == (
        0.65,
        0.75,
    )
    assert values.generators.outside_contamination.client_count == 12
    assert values.generators.outside_contamination.target_triple_theta == 0.1
    assert values.generators.outside_contamination.correlated_campaign_fractions == (
        0.0,
        0.25,
        0.5,
        1.0,
    )
    assert values.generators.outside_contamination.outside_rank_shift == 0.25
    assert values.generators.client_dropout.unavailable_fractions == (0.0, 0.1, 0.25, 0.5)
    assert values.numerics.metric_denominator_floor == 1.0e-12
    assert values.numerics.deterministic_comparison_tolerance == 1.0e-12
    assert values.numerics.smoke_repeatability_tolerance == 1.0e-08


def test_locked_comparator_experiment_statistics_and_runtime(
    production_configuration: LoadedScientificConfiguration,
) -> None:
    values = production_configuration.values
    assert values.comparators.common_calibration.nuisance_reference_quantile == 0.95
    assert values.comparators.connected_information.bins_per_client == 4
    assert values.comparators.connected_information.jeffreys_pseudocount_per_cell == 0.5
    assert values.comparators.connected_information.ipf_max_iterations == 10000
    assert values.comparators.connected_information.maximum_marginal_absolute_error == 1.0e-08
    assert values.comparators.connected_information.probability_floor == 1.0e-12
    assert values.comparators.conditional_log_linear.bins_per_client == 4
    assert values.comparators.conditional_log_linear.max_iterations == 10000
    assert (
        values.comparators.conditional_log_linear.maximum_fitted_marginal_absolute_error == 1.0e-08
    )
    assert values.comparators.conditional_log_linear.probability_floor == 1.0e-12
    assert values.comparators.exclusion_matched_conditional_hofd.relative_singular_cutoff == 1.0e-12
    assert values.comparators.exclusion_matched_conditional_hofd.ridge_penalty == 0.0
    assert values.comparators.global_factor_residual.candidate_ranks == (1, 2, 3)
    assert values.comparators.global_factor_residual.cumulative_variance_target == 0.8
    assert values.comparators.global_factor_residual.fallback_rank == 3
    assert values.comparators.multistream_cusum.rank_center == 0.5
    assert values.comparators.multistream_cusum.drift_subtraction == 0.05
    assert values.comparators.multistream_cusum.initial_state == 0.0
    assert values.comparators.fedavg_autoencoder.rounds == 50
    assert values.comparators.fedavg_autoencoder.local_epochs_per_round == 1
    assert values.comparators.fedavg_autoencoder.client_participation_fraction == 1.0
    assert values.statistics.confidence_level == 0.95
    assert values.statistics.nominal_significance_alpha == 0.05
    assert values.statistics.bootstrap_replicates == 10000
    assert values.statistics.synthetic_sign_flip_replicates_when_not_exact == 100000
    assert (
        values.claim_materiality.self_explanation.exact_exclusion_nuisance_derivative_equivalence_fraction_of_direct
        == 0.05
    )
    assert values.claim_materiality.self_explanation.minimum_attenuation_difference == 0.1
    assert values.claim_materiality.pure_order.maximum_proper_subset_standardized_drift == 0.1
    assert values.claim_materiality.pure_order.minimum_target_order_standardized_drift == 0.5
    assert values.claim_materiality.order_three_estimator.minimum_mean_context_coverage == 0.8
    assert values.claim_materiality.order_three_estimator.maximum_mean_projection_nrmse == 0.1
    assert (
        values.claim_materiality.order_three_estimator.maximum_mean_standardized_null_bias == 0.05
    )
    assert values.claim_materiality.maximum_pooled_numerical_failure_rate == 0.01
    assert values.claim_materiality.hofd_equivalence.atom_nrmse_upper_margin == 0.05
    assert values.claim_materiality.hofd_equivalence.minimum_cosine_similarity == 0.99
    assert values.claim_materiality.hofd_equivalence.stopping_time_difference_interval_epochs == (
        -1.0,
        1.0,
    )
    assert values.claim_materiality.primary_real.minimum_strict_odi_rate == 0.2
    assert (
        values.claim_materiality.primary_real.minimum_odi_rate_advantage_over_order_at_most_two
        == 0.1
    )
    assert values.claim_materiality.primary_real.minimum_median_operational_lead_epochs == 2.0
    assert values.claim_materiality.benign_common_mode.minimum_false_campaign_suppression == 0.5
    assert values.claim_materiality.benign_common_mode.maximum_detection_rate_loss == 0.1
    assert values.claim_materiality.strong_local.minimum_strict_odi_rate == 0.2
    assert values.claim_materiality.order_three_real.minimum_material_odi_contribution == 0.02
    assert values.claim_materiality.reference_harness.p95_latency_maximum_seconds == 30.0
    assert values.support_grids.estimator_samples_per_context == (100, 200, 400, 800, 1600, 3200)
    assert values.support_grids.hofd_equivalence_samples_per_context == (
        800,
        1600,
        3200,
        6400,
        12800,
    )
    assert values.support_grids.estimator_one_factor_sensitivity_samples_per_context == (800, 1600)
    assert values.robustness.benign_count_multiplication_factors == (1.25, 1.5, 2.0)
    assert values.robustness.scalability_client_counts == (6, 12, 24, 48)
    assert (
        values.experiments.primary_strict_odi_evaluation.methods[0]
        is MethodName.FULL_FEDCAMPAIGN_EMHI
    )
    assert values.scalability_timing.measured_repetitions_per_seed_client_count == 5
    assert values.scalability_timing.unmeasured_harness_warmup_epochs == 100
    assert values.scalability_timing.measured_epochs_per_repetition == 600
    assert values.scalability_timing.concurrent_experiment_cells == 1
    assert values.scalability_timing.result_quantile == 0.95
    assert values.runtime.automatic_technical_retries_after_initial_failure == 2
    assert values.runtime.required_confirmatory_missing_cell_tolerance == 0
    assert values.artifacts.outputs_root == "outputs"
    assert values.artifacts.results_root == "results"


def test_locked_reporting_precision(
    production_configuration: LoadedScientificConfiguration,
) -> None:
    precision = production_configuration.values.reporting.precision
    assert precision.probabilities_and_rates_decimals == 3
    assert precision.effect_sizes_decimals == 3
    assert precision.epochs_and_minutes_decimals == 1
    assert precision.milliseconds_and_seconds_decimals == 2
    assert precision.adjusted_p_values_decimals == 4
    assert precision.p_value_lower_display_threshold == 0.0001


def test_schema_round_trip_matches_production_yaml(repo_root: Path) -> None:
    payload = yaml.safe_load((repo_root / "configs" / "fedcampaign-emhi.yaml").read_text())
    loaded = ScientificConfig.model_validate(payload)
    dumped = loaded.model_dump(mode="json")
    assert dumped["study"]["maximum_coalition_order"] == payload["study"]["maximum_coalition_order"]
    assert dumped["datasets"]["primary"]["name"] == payload["datasets"]["primary"]["name"]
    assert dumped["datasets"]["secondary"]["name"] == payload["datasets"]["secondary"]["name"]
    assert dumped["randomness"]["context_base_seed"] == payload["randomness"]["context_base_seed"]
    assert dumped["reporting"]["precision"]["adjusted_p_values_decimals"] == 4


def test_missing_required_field_is_rejected(repo_root: Path) -> None:
    payload = yaml.safe_load((repo_root / "configs" / "fedcampaign-emhi.yaml").read_text())
    del payload["study"]
    with pytest.raises(ValidationError):
        ScientificConfig.model_validate(payload)


def test_ridge_candidates_must_include_zero(repo_root: Path) -> None:
    payload = deepcopy(
        yaml.safe_load((repo_root / "configs" / "fedcampaign-emhi.yaml").read_text())
    )
    payload["projection"]["ridge_candidates"] = [0.0001, 0.001]
    config = ScientificConfig.model_validate(payload)
    with pytest.raises(ConfigurationValidationError):
        validate_scientific_config(config)
