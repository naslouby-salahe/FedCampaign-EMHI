from dataclasses import dataclass
from math import exp, log, tanh

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    ContextMethodName,
    NuisanceTransformName,
)
from fedcampaign_emhi.domain.types import (
    ClientCount,
    ClientIndex,
    FiniteFloat,
    Probability,
    ScoreShift,
    SeedCount,
)


def analytic_direct_derivative() -> FiniteFloat:
    return 1.0


def apply_persistent_perturbation(
    baseline_scores: tuple[FiniteFloat, ...],
    target_indices: tuple[ClientIndex, ...],
    perturbation: ScoreShift,
) -> tuple[FiniteFloat, ...]:
    perturbed: list[FiniteFloat] = list(baseline_scores)
    for index in target_indices:
        perturbed[index] = perturbed[index] + perturbation
    return tuple(perturbed)


def coalition_mean(scores: tuple[FiniteFloat, ...]) -> FiniteFloat:
    if not scores:
        raise ValueError("coalition mean requires at least one client")
    return sum(scores) / len(scores)


def transform_nuisance(statistic: FiniteFloat, transform: NuisanceTransformName) -> FiniteFloat:
    if transform is NuisanceTransformName.LINEAR:
        return statistic
    if transform is NuisanceTransformName.TANH:
        return tanh(2.0 * statistic)
    return log(1.0 + exp(statistic)) - log(2.0)


def scalar_innovation_fixture(
    coalition_scores: tuple[FiniteFloat, ...],
    context_scores: tuple[FiniteFloat, ...],
    transform: NuisanceTransformName,
) -> FiniteFloat:
    response = coalition_mean(coalition_scores)
    nuisance = transform_nuisance(coalition_mean(context_scores), transform)
    return response - nuisance


@dataclass(frozen=True)
class SelfExclusionCell:
    client_count: ClientCount
    coalition_order: CoalitionOrder
    perturbation: ScoreShift
    nuisance_transform: NuisanceTransformName
    context_method: ContextMethodName


@dataclass(frozen=True)
class SelfExclusionPlan:
    cells: tuple[SelfExclusionCell, ...]
    development_seed_count: SeedCount
    confirmatory_seed_count: SeedCount


NUISANCE_TRANSFORMS: tuple[NuisanceTransformName, ...] = (
    NuisanceTransformName.LINEAR,
    NuisanceTransformName.TANH,
    NuisanceTransformName.SOFTPLUS,
)


def enumerate_self_exclusion_grid(config: ScientificConfig) -> SelfExclusionPlan:
    experiment = config.experiments.self_explanation_exclusion_validation
    maximum_order = CoalitionOrder(config.study.maximum_coalition_order)
    orders = tuple(order for order in CoalitionOrder if order <= maximum_order)
    cells: list[SelfExclusionCell] = []
    for client_count in config.robustness.scalability_client_counts:
        for order in orders:
            for perturbation in config.generators.self_explanation.perturbations:
                for transform in NUISANCE_TRANSFORMS:
                    for context_method in experiment.context_methods:
                        cells.append(
                            SelfExclusionCell(
                                client_count=client_count,
                                coalition_order=order,
                                perturbation=perturbation,
                                nuisance_transform=transform,
                                context_method=context_method,
                            )
                        )
    return SelfExclusionPlan(
        cells=tuple(cells),
        development_seed_count=len(config.randomness.synthetic_development_roots),
        confirmatory_seed_count=len(config.randomness.synthetic_confirmatory_roots),
    )


def exact_nuisance_derivative_within_margin(
    exact_derivative: FiniteFloat, margin_fraction_of_direct: Probability
) -> bool:
    direct = analytic_direct_derivative()
    return abs(exact_derivative) <= margin_fraction_of_direct * abs(direct)


def material_attenuation_gate(
    attenuation_contrast: FiniteFloat, minimum_attenuation_difference: FiniteFloat
) -> bool:
    return attenuation_contrast >= minimum_attenuation_difference


def primary_directional_test_passes(adjusted_p_value: Probability, alpha: Probability) -> bool:
    return adjusted_p_value < alpha
