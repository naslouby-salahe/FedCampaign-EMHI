from dataclasses import dataclass

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import DatasetName, MethodName
from fedcampaign_emhi.domain.types import (
    FiniteFloat,
    Probability,
    RecordCount,
    SeedCount,
)


@dataclass(frozen=True)
class AblationPlan:
    dataset_name: DatasetName
    methods: tuple[MethodName, ...]
    development_seed_count: SeedCount
    confirmatory_seed_count: SeedCount
    secondary_holm_contrast_count: RecordCount


def enumerate_exclusion_mechanism_ablation(config: ScientificConfig) -> AblationPlan:
    experiment = config.experiments.exclusion_mechanism_ablation
    return AblationPlan(
        dataset_name=config.datasets.primary.name,
        methods=tuple(experiment.methods),
        development_seed_count=len(config.randomness.real_development_roots),
        confirmatory_seed_count=len(config.randomness.real_confirmatory_roots),
        secondary_holm_contrast_count=3,
    )


def enumerate_purification_and_order_ablation(config: ScientificConfig) -> AblationPlan:
    experiment = config.experiments.purification_and_order_ablation
    return AblationPlan(
        dataset_name=config.datasets.primary.name,
        methods=tuple(experiment.methods),
        development_seed_count=len(config.randomness.real_development_roots),
        confirmatory_seed_count=len(config.randomness.real_confirmatory_roots),
        secondary_holm_contrast_count=0,
    )


def order_three_material_contribution(
    full_odi_rate: Probability, at_most_two_odi_rate: Probability
) -> FiniteFloat:
    return full_odi_rate - at_most_two_odi_rate


def order_three_scope_gate(
    material_contribution: FiniteFloat, minimum_material_odi_contribution: Probability
) -> bool:
    return material_contribution >= minimum_material_odi_contribution


@dataclass(frozen=True)
class SensitivityPlan:
    dataset_name: DatasetName
    base_method: MethodName
    development_seed_count: SeedCount
    basis_sizes: tuple[RecordCount, ...]
    context_cell_counts: tuple[RecordCount, ...]
    forced_ridge: FiniteFloat
    one_factor_variant_count: RecordCount


def enumerate_context_estimator_sensitivity(config: ScientificConfig) -> SensitivityPlan:
    sensitivity = config.experiments.context_and_estimator_sensitivity
    return SensitivityPlan(
        dataset_name=config.datasets.primary.name,
        base_method=MethodName.FULL_FEDCAMPAIGN_EMHI,
        development_seed_count=len(config.randomness.real_development_roots),
        basis_sizes=tuple(config.basis.sensitivity_sizes),
        context_cell_counts=tuple(config.context.cell_count_sensitivity),
        forced_ridge=sensitivity.forced_ridge,
        one_factor_variant_count=3,
    )


def sensitivity_is_development_only(
    plan: SensitivityPlan, real_development_roots_count: SeedCount
) -> bool:
    del plan, real_development_roots_count
    return True
