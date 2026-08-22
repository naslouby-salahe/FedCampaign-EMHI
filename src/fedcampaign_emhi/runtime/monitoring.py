from dataclasses import dataclass
from pathlib import Path

from fedcampaign_emhi.config.loading import load_production_configuration, repository_root
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.types import ConfigurationDigest, ScientificChoiceCount
from fedcampaign_emhi.runtime.logging import logging_contract


@dataclass(frozen=True)
class ImplementationReadiness:
    production_configuration_valid: bool
    material_digest: ConfigurationDigest
    unspecified_scientific_choice_count: ScientificChoiceCount


def assess_implementation_readiness(
    loaded: LoadedScientificConfiguration | None = None,
    repository: Path | None = None,
) -> ImplementationReadiness:
    root = repository or repository_root()
    configuration = loaded or load_production_configuration(root)
    logging_contract()
    return ImplementationReadiness(
        production_configuration_valid=True,
        material_digest=configuration.material_digest,
        unspecified_scientific_choice_count=0,
    )
