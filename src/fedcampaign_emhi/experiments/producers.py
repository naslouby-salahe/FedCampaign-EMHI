from dataclasses import dataclass

from fedcampaign_emhi.comparators.runtime import score_comparator_ranks
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
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
    sample_independent_uniform_ranks,
    sample_pure_polynomial_ranks,
    validate_generator_purity,
)
from fedcampaign_emhi.synthetic.robustness import (
    contaminated_outside_clients,
    dropout_coalition_is_active,
)
from fedcampaign_emhi.synthetic.self_explanation import (
    enumerate_self_exclusion_grid,
    exact_nuisance_derivative_within_margin,
)


@dataclass(frozen=True)
class SyntheticCellOutcome:
    failed_checks: tuple[ComponentName, ...]
    method_score: FiniteFloat | None


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
    if experiment_name is ExperimentName.PURE_ORDER_SEPARATION_VALIDATION:
        report = validate_generator_purity(
            GeneratorName.PURE_CONTINUOUS_TRIPLE,
            config.generators.pure_polynomial.primary_reference_theta,
            config.generators.xor.primary_reference_strength,
            frozenset({CoalitionOrder.THREE}),
            config.numerics.deterministic_comparison_tolerance,
        )
        if not report.is_valid:
            failures.append(f"generator:{report.generator.value}")
    if experiment_name is ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION:
        if not enumerate_self_exclusion_grid(config).cells:
            failures.append("empty self-explanation grid")
        if not exact_nuisance_derivative_within_margin(
            0.0,
            config.claim_materiality.self_explanation.exact_exclusion_nuisance_derivative_equivalence_fraction_of_direct,
        ):
            failures.append("self-explanation derivative gate")
    if experiment_name is ExperimentName.PURE_ORDER_SEPARATION_VALIDATION:
        for order, theta in (
            (CoalitionOrder.ONE, config.generators.pure_polynomial.theta.order_one[0]),
            (CoalitionOrder.TWO, config.generators.pure_polynomial.theta.order_two[0]),
            (CoalitionOrder.THREE, config.generators.pure_polynomial.theta.order_three[0]),
        ):
            sample_pure_polynomial_ranks(order, theta, len(clients) - int(order), seed)
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
