from dataclasses import dataclass

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import DatasetName, MethodName
from fedcampaign_emhi.domain.types import SeedCount


@dataclass(frozen=True)
class SecondaryGeneralizationPlan:
    dataset_name: DatasetName
    methods: tuple[MethodName, ...]
    development_seed_count: SeedCount
    confirmatory_seed_count: SeedCount


def enumerate_secondary_generalization_plan(
    config: ScientificConfig,
) -> SecondaryGeneralizationPlan:
    experiment = config.experiments.secondary_controlled_trace_generalization
    return SecondaryGeneralizationPlan(
        dataset_name=config.datasets.secondary.name,
        methods=tuple(experiment.methods),
        development_seed_count=len(config.randomness.real_development_roots),
        confirmatory_seed_count=len(config.randomness.real_confirmatory_roots),
    )


def secondary_interpretation_is_validation_only(plan: SecondaryGeneralizationPlan) -> bool:
    del plan
    return True
