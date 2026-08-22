from math import exp, log, tanh

from fedcampaign_emhi.domain.enums import NuisanceTransformName
from fedcampaign_emhi.domain.types import ClientIndex, FiniteFloat, ScoreShift


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
