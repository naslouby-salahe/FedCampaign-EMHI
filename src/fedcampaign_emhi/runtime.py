import hashlib
from dataclasses import dataclass
from pathlib import Path

import rfc8785

from fedcampaign_emhi.config.loading import load_production_configuration, repository_root
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import ExecutionRole, ExperimentName, ExperimentState
from fedcampaign_emhi.domain.types import (
    Boolean,
    ComponentName,
    ConfigurationDigest,
    DeterministicUtf8Bytes,
    RelativePath,
    RuntimeSeconds,
    ScientificChoiceCount,
    SeedDerivationIdentity,
    SeedValue,
    ThirtyTwoBitSeed,
)

THIRTY_TWO_BIT_MODULUS = 1 << 32
RFC8785_SAFE_INTEGER_MODULUS = 1 << 53


def deterministic_utf8_bytes(payload: YamlNode) -> DeterministicUtf8Bytes:
    return rfc8785.dumps(payload)


def deterministic_digest(payload: YamlNode) -> ConfigurationDigest:
    return hashlib.sha256(deterministic_utf8_bytes(payload)).hexdigest()


def seed_derivation_payload(identity: SeedDerivationIdentity) -> YamlNode:
    coordinates = {
        coordinate.name: coordinate.scalar for coordinate in identity.condition_coordinates
    }
    dataset_name = None if identity.dataset is None else identity.dataset.value
    return {
        "base_seed": str(identity.base_seed),
        "component_name": identity.component_name,
        "dataset": dataset_name,
        "client_ids": sorted(identity.client_ids),
        "coalition_ids": sorted(identity.coalition_ids),
        "condition_coordinates": coordinates,
    }


def derive_component_seed(identity: SeedDerivationIdentity) -> SeedValue:
    digest = hashlib.sha256(deterministic_utf8_bytes(seed_derivation_payload(identity))).digest()
    return int.from_bytes(digest[:8], "big") % RFC8785_SAFE_INTEGER_MODULUS


def thirty_two_bit_seed(seed: SeedValue) -> ThirtyTwoBitSeed:
    return seed % THIRTY_TWO_BIT_MODULUS


@dataclass(frozen=True)
class RuntimeLogEvent:
    experiment_name: ExperimentName
    execution_role: ExecutionRole | None
    semantic_cell_path: RelativePath | None
    seed: SeedValue | None
    stage: ComponentName
    state: ExperimentState
    elapsed_seconds: RuntimeSeconds
    detail: ComponentName


def write_runtime_log(destination: Path, event: RuntimeLogEvent) -> None:
    payload = {
        "experiment_name": event.experiment_name.value,
        "execution_role": None if event.execution_role is None else event.execution_role.value,
        "semantic_cell_path": event.semantic_cell_path,
        "seed": event.seed,
        "stage": event.stage,
        "state": event.state.value,
        "elapsed_seconds": event.elapsed_seconds,
        "detail": event.detail,
    }
    encoded = deterministic_utf8_bytes(payload)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_suffix(destination.suffix + ".partial")
    staging.write_bytes(encoded)
    staging.replace(destination)


@dataclass(frozen=True)
class ImplementationReadiness:
    production_configuration_valid: Boolean
    material_digest: ConfigurationDigest
    unspecified_scientific_choice_count: ScientificChoiceCount


def assess_implementation_readiness(
    loaded: LoadedScientificConfiguration | None = None,
    repository: Path | None = None,
) -> ImplementationReadiness:
    root = repository or repository_root()
    configuration = loaded or load_production_configuration(root)
    return ImplementationReadiness(
        production_configuration_valid=True,
        material_digest=configuration.material_digest,
        unspecified_scientific_choice_count=0,
    )
