from dataclasses import dataclass

from fedcampaign_emhi.comparators.runtime import score_comparator_ranks
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import (
    ExecutionRole,
    ExperimentName,
    MethodName,
)
from fedcampaign_emhi.domain.types import (
    ClientCount,
    ClientId,
    ComponentName,
    FiniteFloat,
    SeedValue,
)
from fedcampaign_emhi.synthetic.common_mode import (
    equally_spaced_loadings,
    generate_common_mode_scores,
    generate_unit_variance_autoregressive_latent,
)
from fedcampaign_emhi.synthetic.controlled_campaigns import (
    apply_marginal_score_shift,
    gaussian_copula_pair,
)
from fedcampaign_emhi.synthetic.pure_order import (
    enumerate_pure_order_grid,
    sample_independent_uniform_ranks,
    validate_generator_purity,
)
from fedcampaign_emhi.synthetic.robustness import (
    contaminated_outside_clients,
    dropout_coalition_is_active,
)
from fedcampaign_emhi.synthetic.self_explanation import (
    evaluate_self_explanation_seed,
    exact_nuisance_derivative_within_margin,
    material_attenuation_gate,
)


@dataclass(frozen=True)
class SyntheticCellOutcome:
    failed_checks: tuple[ComponentName, ...]
    method_score: FiniteFloat | None
    evidence: YamlNode = None


def synthetic_role_seeds(
    loaded: LoadedScientificConfiguration, role: ExecutionRole
) -> tuple[SeedValue, ...]:
    if role is ExecutionRole.CONFIRMATORY:
        return loaded.values.randomness.synthetic_confirmatory_roots
    return loaded.values.randomness.synthetic_development_roots


def _client_ids(count: ClientCount) -> tuple[ClientId, ...]:
    return tuple(f"synthetic-client-{index}" for index in range(count))


def run_synthetic_cell(
    loaded: LoadedScientificConfiguration,
    experiment_name: ExperimentName,
    seed: SeedValue,
    method_name: MethodName | None,
) -> SyntheticCellOutcome:
    config = loaded.values
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
        )
    if experiment_name is ExperimentName.PURE_ORDER_SEPARATION_VALIDATION:
        failures: list[ComponentName] = []
        records: list[YamlNode] = []
        for cell in enumerate_pure_order_grid(config):
            report = validate_generator_purity(
                cell.generator,
                cell.effect,
                cell.effect,
                frozenset({cell.target_order}),
                config.numerics.deterministic_comparison_tolerance,
            )
            if not report.is_valid:
                failures.append(f"generator:{cell.generator.value}")
            records.append(
                {
                    "generator": cell.generator.value,
                    "effect": cell.effect,
                    "method": cell.method.value,
                    "target_order": int(cell.target_order),
                    "purity_valid": report.is_valid,
                }
            )
        return SyntheticCellOutcome(
            tuple(sorted(set(failures))),
            None,
            {"condition_count": len(records), "conditions": records},
        )
    failures: list[ComponentName] = []
    clients = _client_ids(3)
    ranks = sample_independent_uniform_ranks(len(clients), seed)
    latent = generate_unit_variance_autoregressive_latent(
        8, config.generators.common_mode.latent_ar_coefficient, seed
    )
    loadings = equally_spaced_loadings(
        len(clients),
        config.generators.common_mode.client_loading_minimum,
        config.generators.common_mode.client_loading_maximum,
    )
    scores = generate_common_mode_scores(
        latent,
        loadings,
        config.generators.common_mode.client_noise_standard_deviation,
        seed,
    )
    if len(scores) != len(latent) or any(len(row) != len(clients) for row in scores):
        failures.append("common-mode shape")
    shifted = apply_marginal_score_shift(
        (0.0, 0.0, 0.0), clients, config.generators.controlled_campaigns.marginal.score_shift
    )
    if len(shifted) != len(clients):
        failures.append("controlled marginal campaign")
    pair = gaussian_copula_pair(
        config.generators.controlled_campaigns.pair_relation.campaign_correlation, seed
    )
    if any(rank < 0.0 or rank > 1.0 for rank in pair):
        failures.append("copula rank range")
    if experiment_name is ExperimentName.OUTSIDE_CAMPAIGN_CONTAMINATION_BOUNDARY:
        contaminated_outside_clients(
            clients, config.generators.outside_contamination.correlated_campaign_fractions[0]
        )
    if experiment_name is ExperimentName.CLIENT_DROPOUT_AND_CONTEXT_SPARSITY_BOUNDARY:
        dropout_coalition_is_active(
            clients[:1],
            clients,
            clients,
            config.context.minimum_available_outside_clients,
            config.context.minimum_available_outside_fraction,
        )
    method_score: FiniteFloat | None = None
    if method_name is not None and method_name not in {
        MethodName.FULL_FEDCAMPAIGN_EMHI,
        MethodName.EXCLUSION_MATCHED_ORDER_ONE_EMHI,
        MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI,
        MethodName.INCLUSIVE_CONTEXT_FULL_HIERARCHY,
        MethodName.LEAVE_ONE_OUT_INSUFFICIENT_EXCLUSION,
        MethodName.PARTIAL_COALITION_EXCLUSION,
        MethodName.NO_PROPER_SUBSET_PURIFICATION,
        MethodName.NO_OUTSIDE_CONTEXT_FULL_HIERARCHY,
    }:
        try:
            method_score = score_comparator_ranks(method_name, ranks, config)[0]
        except ValueError as error:
            failures.append(f"method:{method_name.value}:{error}")
    return SyntheticCellOutcome(tuple(failures), method_score)
