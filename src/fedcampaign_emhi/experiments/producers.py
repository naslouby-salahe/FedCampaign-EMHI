from dataclasses import dataclass

from fedcampaign_emhi.comparators.hofd_equivalence import (
    cosine_equivalence_gate,
    nrmse_equivalence_gate,
    paired_atom_metrics,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    ExecutionRole,
    ExperimentName,
    GeneratorName,
    MethodName,
)
from fedcampaign_emhi.domain.types import (
    ClientCount,
    ClientId,
    ComponentName,
    FiniteFloat,
    SeedValue,
)
from fedcampaign_emhi.emhi.basis import tensor_representation
from fedcampaign_emhi.emhi.innovation_calibration import calibrate_innovations_on_nuisance_fit
from fedcampaign_emhi.emhi.innovations import projection_residual
from fedcampaign_emhi.emhi.projection import proper_subset_design_row, ridge_coefficient_matrix
from fedcampaign_emhi.synthetic.context_boundaries import primary_feasibility_context_support
from fedcampaign_emhi.synthetic.feasibility import (
    EstimatorFeasibilityMetrics,
    evaluate_estimator_feasibility_seed,
)
from fedcampaign_emhi.synthetic.pure_order import (
    enumerate_pure_order_grid,
    fitted_method_pure_order_metrics,
    sample_independent_uniform_ranks,
    validate_generator_purity,
)
from fedcampaign_emhi.synthetic.robustness import (
    availability_mask,
    contaminate_rank,
    contaminated_outside_clients,
    dropout_coalition_is_active,
    outside_contamination_targets,
)
from fedcampaign_emhi.synthetic.self_explanation import (
    evaluate_self_explanation_seed,
    exact_nuisance_derivative_within_margin,
    material_attenuation_gate,
)
from fedcampaign_emhi.synthetic.sequential import (
    SignedTheoremSeedMetrics,
    evaluate_signed_theorem_seed,
)


@dataclass(frozen=True)
class SelfExplanationSeedMetrics:
    primary_exact_nuisance_derivative: FiniteFloat
    primary_attenuation_contrast: FiniteFloat


@dataclass(frozen=True)
class PureOrderSeedMetrics:
    maximum_proper_subset_standardized_drift: FiniteFloat
    target_order_standardized_drift: FiniteFloat


@dataclass(frozen=True)
class EstimatorFeasibilitySeedMetrics:
    primary: EstimatorFeasibilityMetrics


@dataclass(frozen=True)
class SyntheticCellOutcome:
    failed_checks: tuple[ComponentName, ...]
    method_score: FiniteFloat | None
    evidence: YamlNode = None
    self_explanation_metrics: SelfExplanationSeedMetrics | None = None
    pure_order_metrics: PureOrderSeedMetrics | None = None
    signed_theorem_metrics: SignedTheoremSeedMetrics | None = None
    estimator_feasibility_metrics: EstimatorFeasibilitySeedMetrics | None = None


_MISSING_CONTRACT_SPECIFIC_PRODUCERS = frozenset(
    {
        ExperimentName.STRONG_COMPARATOR_COMPOSITION_CHALLENGE,
    }
)


def _evaluate_hofd_equivalence_seed(
    loaded: LoadedScientificConfiguration,
    seed: SeedValue,
) -> SyntheticCellOutcome:
    """Compare the fitted EMHI residual with the exclusion-matched HOFD residual.

    Each configured support level is an independent held-out condition.  EMHI
    uses its configured cross-fitted calibration route; HOFD uses its declared
    ridge/SVD route on the identical rank rows.  This keeps the comparison
    paired without silently substituting a proxy scorer.
    """
    config = loaded.values
    experiment = config.experiments.exclusion_matched_hofd_equivalence
    materiality = config.claim_materiality.hofd_equivalence
    client_count = config.experiments.pure_order_separation_validation.primary_client_count
    condition_records: list[YamlNode] = []
    failures: list[ComponentName] = []
    for support in experiment.primary_support_levels:
        calibration_rows = tuple(
            sample_independent_uniform_ranks(client_count, seed + index)[:3]
            for index in range(support)
        )
        heldout_count = (
            config.synthetic.sample_sizes.hofd_equivalence_heldout_samples_per_context_seed
        )
        heldout_rows = tuple(
            sample_independent_uniform_ranks(client_count, seed + support + index)[:3]
            for index in range(heldout_count)
        )
        calibration_design_rows = tuple(
            proper_subset_design_row(row, config.basis.primary_size) for row in calibration_rows
        )
        calibration_tensors = tuple(
            tensor_representation(row, config.basis.primary_size) for row in calibration_rows
        )
        calibration = calibrate_innovations_on_nuisance_fit(
            calibration_design_rows,
            calibration_tensors,
            config.projection.ridge_candidates,
            config.projection.cross_validation.fold_count,
            config.projection.selection_tie_tolerance_mse,
            config.projection.zero_ridge_svd_relative_cutoff,
            config.projection.atom_scale_floor,
        )
        if calibration is None:
            failures.append(f"HOFD equivalence calibration support {support}")
            continue
        heldout_design_rows = tuple(
            proper_subset_design_row(row, config.basis.primary_size) for row in heldout_rows
        )
        heldout_tensors = tuple(
            tensor_representation(row, config.basis.primary_size) for row in heldout_rows
        )
        emhi_atoms = tuple(
            projection_residual(tensor, calibration.complete_nuisance_coefficients, design)
            for tensor, design in zip(heldout_tensors, heldout_design_rows, strict=True)
        )
        hofd_coefficients = ridge_coefficient_matrix(
            calibration_design_rows,
            calibration_tensors,
            config.comparators.exclusion_matched_conditional_hofd.ridge_penalty,
            config.comparators.exclusion_matched_conditional_hofd.relative_singular_cutoff,
        )
        hofd_atoms = tuple(
            projection_residual(tensor, hofd_coefficients, design)
            for tensor, design in zip(heldout_tensors, heldout_design_rows, strict=True)
        )
        metrics = paired_atom_metrics(
            emhi_atoms,
            hofd_atoms,
            config.numerics.metric_denominator_floor,
        )
        nrmse_passes = nrmse_equivalence_gate(metrics.nrmse, materiality.atom_nrmse_upper_margin)
        cosine_passes = cosine_equivalence_gate(
            metrics.cosine_similarity, materiality.minimum_cosine_similarity
        )
        if not nrmse_passes:
            failures.append(f"HOFD atom NRMSE support {support}")
        if not cosine_passes:
            failures.append(f"HOFD atom cosine support {support}")
        condition_records.append(
            {
                "support_per_context": support,
                "heldout_samples": heldout_count,
                "atom_nrmse": metrics.nrmse,
                "atom_cosine_similarity": metrics.cosine_similarity,
                "nrmse_equivalence_passes": nrmse_passes,
                "cosine_equivalence_passes": cosine_passes,
            }
        )
    return SyntheticCellOutcome(
        tuple(failures),
        None,
        {
            "comparison": "paired exclusion-matched EMHI and HOFD atom residuals",
            "context_cell_count": experiment.context_cell_count,
            "conditions": condition_records,
        },
    )


def _synthetic_robustness_client_ids(client_count: ClientCount) -> tuple[ClientId, ...]:
    return tuple(f"synthetic-robustness-{index}" for index in range(client_count))


def _evaluate_outside_contamination_seed(
    loaded: LoadedScientificConfiguration, seed: SeedValue
) -> SyntheticCellOutcome:
    config = loaded.values
    specification = config.generators.outside_contamination
    client_ids = _synthetic_robustness_client_ids(specification.client_count)
    target = outside_contamination_targets(client_ids)
    outside = tuple(client_id for client_id in client_ids if client_id not in target)
    records: list[YamlNode] = []
    for fraction in specification.correlated_campaign_fractions:
        contaminated = contaminated_outside_clients(outside, fraction)
        transformed = tuple(
            contaminate_rank(
                sample_independent_uniform_ranks(specification.client_count, seed + index)[0],
                specification.outside_rank_shift,
                config.context.rank_clip_epsilon,
            )
            for index, _client_id in enumerate(contaminated)
        )
        records.append(
            {
                "correlated_campaign_fraction": fraction,
                "contaminated_outside_client_ids": contaminated,
                "transformed_rank_count": len(transformed),
            }
        )
    return SyntheticCellOutcome(
        (),
        None,
        {"target_client_ids": target, "contamination_conditions": records},
    )


def _evaluate_dropout_sparsity_seed(
    loaded: LoadedScientificConfiguration, seed: SeedValue
) -> SyntheticCellOutcome:
    config = loaded.values
    client_ids = _synthetic_robustness_client_ids(
        config.generators.outside_contamination.client_count
    )
    target = outside_contamination_targets(client_ids)
    records: list[YamlNode] = []
    for fraction in config.generators.client_dropout.unavailable_fractions:
        available = availability_mask(client_ids, fraction, seed)
        records.append(
            {
                "unavailable_fraction": fraction,
                "available_client_ids": available,
                "target_coalition_active": dropout_coalition_is_active(
                    target,
                    available,
                    client_ids,
                    config.context.minimum_available_outside_clients,
                    config.context.minimum_available_outside_fraction,
                ),
            }
        )
    return SyntheticCellOutcome((), None, {"dropout_conditions": records})


def synthetic_role_seeds(
    loaded: LoadedScientificConfiguration, role: ExecutionRole
) -> tuple[SeedValue, ...]:
    if role is ExecutionRole.CONFIRMATORY:
        return loaded.values.randomness.synthetic_confirmatory_roots
    return loaded.values.randomness.synthetic_development_roots


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
                },
                "condition_evaluations": [
                    {
                        "identifier": evaluation.condition.identifier,
                        "order": int(evaluation.condition.order),
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
                    }
                    for evaluation in evaluations
                ],
            },
            None,
            None,
            None,
            EstimatorFeasibilitySeedMetrics(metrics),
        )
    if experiment_name in _MISSING_CONTRACT_SPECIFIC_PRODUCERS:
        return SyntheticCellOutcome(
            ("missing contract-specific synthetic producer",),
            None,
            {
                "implementation_state": "missing_contract_specific_producer",
                "required_experiment": experiment_name.value,
            },
        )
    if experiment_name is ExperimentName.SEQUENTIAL_EVIDENCE_VALIDATION:
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
    if experiment_name is ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION:
        result = evaluate_self_explanation_seed(config, seed)
        failures: list[ComponentName] = []
        materiality = config.claim_materiality.self_explanation
        if not exact_nuisance_derivative_within_margin(
            result.primary_exact_nuisance_derivative,
            materiality.exact_exclusion_nuisance_derivative_equivalence_fraction_of_direct,
        ):
            failures.append("self-explanation exact nuisance derivative")
        if not material_attenuation_gate(
            result.primary_attenuation_contrast,
            materiality.minimum_attenuation_difference,
        ):
            failures.append("self-explanation material attenuation")
        return SyntheticCellOutcome(
            tuple(failures),
            None,
            {
                "grid_cell_count": len(result.measurements),
                "primary_exact_nuisance_derivative": result.primary_exact_nuisance_derivative,
                "primary_attenuation_contrast": result.primary_attenuation_contrast,
                "measurements": [
                    {
                        "client_count": measurement.cell.client_count,
                        "coalition_order": int(measurement.cell.coalition_order),
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
    if experiment_name is ExperimentName.PURE_ORDER_SEPARATION_VALIDATION:
        if method_name is None:
            raise ValueError("pure-order scoring requires a declared method")
        failures: list[ComponentName] = []
        records: list[YamlNode] = []
        primary_metrics: PureOrderSeedMetrics | None = None
        primary = config.experiments.pure_order_separation_validation.primary_condition
        emhi_methods = frozenset(
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
            if method_name not in emhi_methods:
                records.append(
                    {
                        "generator": cell.generator.value,
                        "effect": cell.effect,
                        "method": cell.method.value,
                        "target_order": int(cell.target_order),
                        "enabled_orders": [int(order) for order in sorted(cell.enabled_orders)],
                        "purity_valid": report.is_valid,
                        "scoring_state": "awaiting_execution_layer_native_comparator_scorer",
                    }
                )
                continue
            metrics = fitted_method_pure_order_metrics(config, cell, seed)
            if (
                method_name is primary.method
                and cell.generator is primary.generator
                and cell.target_order == CoalitionOrder(primary.coalition_order)
                and cell.effect == config.generators.pure_polynomial.primary_reference_theta
            ):
                primary_metrics = PureOrderSeedMetrics(
                    metrics.maximum_proper_subset_standardized_drift,
                    metrics.target_order_standardized_drift,
                )
                if not metrics.proper_subset_scoring_available:
                    failures.append("missing fitted proper-subset pure-order scores")
            records.append(
                {
                    "generator": cell.generator.value,
                    "effect": cell.effect,
                    "method": cell.method.value,
                    "target_order": int(cell.target_order),
                    "enabled_orders": [int(order) for order in sorted(cell.enabled_orders)],
                    "purity_valid": report.is_valid,
                    "maximum_proper_subset_standardized_drift": metrics.maximum_proper_subset_standardized_drift,
                    "target_order_standardized_drift": metrics.target_order_standardized_drift,
                    "proper_subset_scoring_available": metrics.proper_subset_scoring_available,
                }
            )
        if method_name is primary.method and primary_metrics is None:
            failures.append("missing primary fitted pure-order score")
        failures.append("missing exact-exclusion fitted pure-order artifact scorer")
        failures.append("missing exact-exclusion fitted pure-order artifact grid")
        if method_name not in emhi_methods:
            failures.append("missing native comparator pure-order grid")
        return SyntheticCellOutcome(
            tuple(sorted(set(failures))),
            None,
            {
                "condition_count": len(records),
                "conditions": records,
                "implementation_state": "partial_projection_scorer_not_claim_eligible",
            },
            pure_order_metrics=primary_metrics,
        )
    raise ValueError(f"unsupported synthetic experiment {experiment_name.value}")
