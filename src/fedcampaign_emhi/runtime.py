import hashlib
import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from time import perf_counter
from typing import ParamSpec, TypeVar

import rfc8785

from fedcampaign_emhi.config.loading import load_production_configuration, repository_root
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.types import (
    Boolean,
    ComponentName,
    ConfigurationDigest,
    DeterministicUtf8Bytes,
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


STRUCTURED_LOG_ROOT_LOGGER_NAME = "fedcampaign_emhi"
_structured_logging_configured = False


def configure_structured_logging() -> None:
    global _structured_logging_configured
    if _structured_logging_configured:
        return
    root = logging.getLogger(STRUCTURED_LOG_ROOT_LOGGER_NAME)
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root.addHandler(handler)
    root.propagate = False
    _structured_logging_configured = True


def component_logger(component_name: ComponentName) -> logging.Logger:
    return logging.getLogger(f"{STRUCTURED_LOG_ROOT_LOGGER_NAME}.{component_name}")


_StageParams = ParamSpec("_StageParams")
_StageResult = TypeVar("_StageResult")


def log_stage(
    component_name: ComponentName,
) -> Callable[[Callable[_StageParams, _StageResult]], Callable[_StageParams, _StageResult]]:
    def decorator(
        func: Callable[_StageParams, _StageResult],
    ) -> Callable[_StageParams, _StageResult]:
        @wraps(func)
        def wrapper(*args: _StageParams.args, **kwargs: _StageParams.kwargs) -> _StageResult:
            logger = component_logger(component_name)
            started = perf_counter()
            logger.info("stage_started function=%s", func.__qualname__)
            try:
                result = func(*args, **kwargs)
            except Exception as error:
                logger.info(
                    "stage_failed function=%s elapsed_seconds=%.6f error=%s",
                    func.__qualname__,
                    perf_counter() - started,
                    error,
                )
                raise
            logger.info(
                "stage_completed function=%s elapsed_seconds=%.6f",
                func.__qualname__,
                perf_counter() - started,
            )
            return result

        return wrapper

    return decorator
