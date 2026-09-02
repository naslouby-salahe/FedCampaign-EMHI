from dataclasses import dataclass
from math import exp, log, tanh

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    ContextMethodName,
    NuisanceTransformName,
)
from fedcampaign_emhi.domain.types import (
    Attenuation,
    AttenuationDifference,
    Boolean,
    ClientCount,
    ClientId,
    ClientIndex,
    DetectorScore,
    EffectCoefficient,
    InnovationCoordinate,
    LatentState,
    Probability,
    ScoreShift,
    SeedCount,
    SeedValue,
)
from fedcampaign_emhi.emhi.contexts import (
    exact_exclusion_members,
    inclusive_context_members,
    leave_one_out_context_members,
    partial_coalition_context_members,
)
from fedcampaign_emhi.synthetic.generators import (
    equally_spaced_loadings,
    generate_common_mode_scores,
    generate_unit_variance_autoregressive_latent,
)


def analytic_direct_derivative() -> EffectCoefficient:
    return 1.0


def apply_persistent_perturbation(
    baseline_scores: tuple[DetectorScore, ...],
    target_indices: tuple[ClientIndex, ...],
    perturbation: ScoreShift,
) -> tuple[DetectorScore, ...]:
    perturbed: list[DetectorScore] = list(baseline_scores)
    for index in target_indices:
        perturbed[index] = perturbed[index] + perturbation
    return tuple(perturbed)


def coalition_mean(scores: tuple[DetectorScore, ...]) -> DetectorScore:
    if not scores:
        raise ValueError("coalition mean requires at least one client")
    return sum(scores) / len(scores)


def transform_nuisance(
    statistic: DetectorScore | LatentState, transform: NuisanceTransformName
) -> InnovationCoordinate:
    if transform is NuisanceTransformName.LINEAR:
        return statistic
    if transform is NuisanceTransformName.TANH:
        return tanh(2.0 * statistic)
    return log(1.0 + exp(statistic)) - log(2.0)


def scalar_innovation_fixture(
    coalition_scores: tuple[DetectorScore, ...],
    context_scores: tuple[DetectorScore, ...],
    transform: NuisanceTransformName,
) -> InnovationCoordinate:
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


@dataclass(frozen=True)
class SelfExplanationMeasurement:
    cell: SelfExclusionCell
    response_mean: DetectorScore
    nuisance_mean: InnovationCoordinate
    innovation_mean: InnovationCoordinate
    direct_derivative: EffectCoefficient
    nuisance_derivative: EffectCoefficient
    innovation_derivative: EffectCoefficient
    attenuation: Attenuation


@dataclass(frozen=True)
class PerturbationResponse:
    perturbation: ScoreShift
    response_mean: DetectorScore
    nuisance_mean: InnovationCoordinate
    innovation_mean: InnovationCoordinate


def _response_for(
    perturbation_responses: tuple[PerturbationResponse, ...], perturbation: ScoreShift
) -> PerturbationResponse:
    return next(
        response for response in perturbation_responses if response.perturbation == perturbation
    )


@dataclass(frozen=True)
class SelfExplanationSeedResult:
    measurements: tuple[SelfExplanationMeasurement, ...]
    primary_exact_nuisance_derivative: EffectCoefficient
    primary_attenuation_contrast: AttenuationDifference


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
    exact_derivative: EffectCoefficient, margin_fraction_of_direct: Probability
) -> Boolean:
    direct = analytic_direct_derivative()
    return abs(exact_derivative) <= margin_fraction_of_direct * abs(direct)


def material_attenuation_criterion(
    attenuation_contrast: AttenuationDifference,
    minimum_attenuation_difference: AttenuationDifference,
) -> Boolean:
    return attenuation_contrast >= minimum_attenuation_difference


def primary_directional_test_passes(adjusted_p_value: Probability, alpha: Probability) -> Boolean:
    return adjusted_p_value < alpha


def _context_indices(
    context_method: ContextMethodName,
    client_ids: tuple[ClientId, ...],
    coalition_ids: tuple[ClientId, ...],
) -> tuple[ClientIndex, ...]:
    if context_method is ContextMethodName.ORACLE_OUTSIDE_LATENT_CONTEXT:
        return ()
    if context_method is ContextMethodName.EXACT_COALITION_EXCLUSION:
        members = exact_exclusion_members(client_ids, coalition_ids)
    elif context_method is ContextMethodName.INCLUSIVE_CONTEXT:
        members = inclusive_context_members(client_ids, coalition_ids)
    elif context_method is ContextMethodName.LEAVE_ONE_OUT_INSUFFICIENT_EXCLUSION:
        members = leave_one_out_context_members(client_ids, coalition_ids)
    elif context_method is ContextMethodName.PARTIAL_COALITION_EXCLUSION:
        if len(coalition_ids) == 1:
            members = exact_exclusion_members(client_ids, coalition_ids)
        else:
            members = partial_coalition_context_members(client_ids, coalition_ids)
    else:
        raise ValueError(f"unsupported self-explanation context method: {context_method.value}")
    return tuple(client_ids.index(member) for member in members)


def _ols_slope(
    predictors: tuple[ScoreShift, ...], responses: tuple[InnovationCoordinate, ...]
) -> EffectCoefficient:
    if len(predictors) != len(responses) or len(predictors) < 2:
        raise ValueError("OLS slope requires paired predictor and response values")
    predictor_mean = sum(predictors) / len(predictors)
    response_mean = sum(responses) / len(responses)
    denominator = sum((predictor - predictor_mean) ** 2 for predictor in predictors)
    if denominator == 0.0:
        raise ValueError("OLS slope requires nonconstant perturbations")
    numerator = sum(
        (predictor - predictor_mean) * (response - response_mean)
        for predictor, response in zip(predictors, responses, strict=True)
    )
    return numerator / denominator


def evaluate_self_explanation_seed(
    config: ScientificConfig, seed: SeedValue
) -> SelfExplanationSeedResult:
    plan = enumerate_self_exclusion_grid(config)
    sample_sizes = config.synthetic.sample_sizes
    epoch_count = (
        sample_sizes.self_explanation_lag_settling_epochs_discarded
        + sample_sizes.self_explanation_epochs_per_perturbation
        + 1
    )
    client_count_maximum = max(config.robustness.scalability_client_counts)
    client_ids = tuple(f"synthetic-client-{index}" for index in range(client_count_maximum))
    latent = generate_unit_variance_autoregressive_latent(
        epoch_count, config.generators.common_mode.latent_ar_coefficient, seed
    )
    loadings = equally_spaced_loadings(
        client_count_maximum,
        config.generators.common_mode.client_loading_minimum,
        config.generators.common_mode.client_loading_maximum,
    )
    base_scores = generate_common_mode_scores(
        latent,
        loadings,
        config.generators.common_mode.client_noise_standard_deviation,
        seed,
    )
    measurements: list[SelfExplanationMeasurement] = []
    primary_exact_derivative: EffectCoefficient | None = None
    primary_attenuation_contrast: AttenuationDifference | None = None
    primary = config.experiments.self_explanation_exclusion_validation.primary_condition
    for cell in plan.cells:
        selected_ids = client_ids[: cell.client_count]
        coalition_ids = selected_ids[: int(cell.coalition_order)]
        coalition_indices = tuple(selected_ids.index(member) for member in coalition_ids)
        context_indices = _context_indices(cell.context_method, selected_ids, coalition_ids)
        perturbation_responses: list[PerturbationResponse] = []
        for perturbation in config.generators.self_explanation.perturbations:
            responses: list[DetectorScore] = []
            nuisances: list[InnovationCoordinate] = []
            innovations: list[InnovationCoordinate] = []
            for epoch in range(
                sample_sizes.self_explanation_lag_settling_epochs_discarded + 1,
                epoch_count,
            ):
                current = apply_persistent_perturbation(
                    base_scores[epoch], coalition_indices, perturbation
                )
                response = coalition_mean(tuple(current[index] for index in coalition_indices))
                if cell.context_method is ContextMethodName.ORACLE_OUTSIDE_LATENT_CONTEXT:
                    nuisance = transform_nuisance(latent[epoch - 1], cell.nuisance_transform)
                else:
                    lagged = apply_persistent_perturbation(
                        base_scores[epoch - 1], coalition_indices, perturbation
                    )
                    nuisance = transform_nuisance(
                        coalition_mean(tuple(lagged[index] for index in context_indices)),
                        cell.nuisance_transform,
                    )
                responses.append(response)
                nuisances.append(nuisance)
                innovations.append(response - nuisance)
            perturbation_responses.append(
                PerturbationResponse(
                    perturbation=perturbation,
                    response_mean=sum(responses) / len(responses),
                    nuisance_mean=sum(nuisances) / len(nuisances),
                    innovation_mean=sum(innovations) / len(innovations),
                )
            )
        resolved_responses = tuple(perturbation_responses)
        direct_derivative = _ols_slope(
            config.generators.self_explanation.derivative_regression_perturbations,
            tuple(
                _response_for(resolved_responses, perturbation).response_mean
                for perturbation in config.generators.self_explanation.derivative_regression_perturbations
            ),
        )
        nuisance_derivative = _ols_slope(
            config.generators.self_explanation.derivative_regression_perturbations,
            tuple(
                _response_for(resolved_responses, perturbation).nuisance_mean
                for perturbation in config.generators.self_explanation.derivative_regression_perturbations
            ),
        )
        innovation_derivative = _ols_slope(
            config.generators.self_explanation.derivative_regression_perturbations,
            tuple(
                _response_for(resolved_responses, perturbation).innovation_mean
                for perturbation in config.generators.self_explanation.derivative_regression_perturbations
            ),
        )
        attenuation = 1.0 - (
            abs(innovation_derivative)
            / (abs(direct_derivative) + config.numerics.metric_denominator_floor)
        )
        measurements.append(
            SelfExplanationMeasurement(
                cell=cell,
                response_mean=_response_for(resolved_responses, cell.perturbation).response_mean,
                nuisance_mean=_response_for(resolved_responses, cell.perturbation).nuisance_mean,
                innovation_mean=_response_for(
                    resolved_responses, cell.perturbation
                ).innovation_mean,
                direct_derivative=direct_derivative,
                nuisance_derivative=nuisance_derivative,
                innovation_derivative=innovation_derivative,
                attenuation=attenuation,
            )
        )
    matching = [
        measurement
        for measurement in measurements
        if measurement.cell.client_count == primary.client_count
        and int(measurement.cell.coalition_order) == primary.coalition_order
        and measurement.cell.nuisance_transform is primary.nuisance_transform
        and measurement.cell.perturbation == 0.0
    ]
    if set(primary.comparison) != {
        ContextMethodName.EXACT_COALITION_EXCLUSION,
        ContextMethodName.INCLUSIVE_CONTEXT,
    }:
        raise ValueError(
            "primary_condition.comparison must declare exactly the exact-exclusion and "
            "inclusive-context methods compared by the self-explanation attenuation hypothesis"
        )
    exact = next(
        measurement
        for measurement in matching
        if measurement.cell.context_method is ContextMethodName.EXACT_COALITION_EXCLUSION
    )
    inclusive = next(
        measurement
        for measurement in matching
        if measurement.cell.context_method is ContextMethodName.INCLUSIVE_CONTEXT
    )
    primary_exact_derivative = exact.nuisance_derivative
    primary_attenuation_contrast = inclusive.attenuation - exact.attenuation
    return SelfExplanationSeedResult(
        measurements=tuple(measurements),
        primary_exact_nuisance_derivative=primary_exact_derivative,
        primary_attenuation_contrast=primary_attenuation_contrast,
    )
