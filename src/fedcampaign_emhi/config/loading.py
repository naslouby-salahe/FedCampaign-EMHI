from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import cast

import rfc8785
import yaml

from fedcampaign_emhi.config.schema import (
    DerivedScientificValues,
    LoadedScientificConfiguration,
    ScientificConfig,
)
from fedcampaign_emhi.config.validation import (
    ConfigurationValidationError,
    YamlNode,
    reject_forbidden_derived_keys,
)
from fedcampaign_emhi.domain.enums import ConfigurationProfile
from fedcampaign_emhi.domain.types import (
    BinCount,
    CanonicalUtf8Bytes,
    ConfidenceLevel,
    ConfigurationDigest,
    FalseAlarmRate,
    PositiveInt,
    RankValue,
)

PRODUCTION_CONFIGURATION_RELATIVE_PATH = Path("configs/fedcampaign-emhi.yaml")
TESTS_CONFIGURATION_RELATIVE_PATH = Path("configs/tests.yml")
SMOKE_CONFIGURATION_RELATIVE_PATH = Path("configs/smoke.yml")


def repository_root(start: Path | None = None) -> Path:
    cursor = (start or Path.cwd()).resolve()
    for candidate in (cursor, *cursor.parents):
        marker = candidate / "pyproject.toml"
        production = candidate / PRODUCTION_CONFIGURATION_RELATIVE_PATH
        if marker.is_file() and production.is_file():
            return candidate
    raise ConfigurationValidationError("unable to locate the FedCampaign-EMHI repository root")


def _load_mapping(path: Path) -> YamlNode:
    raw = path.read_text(encoding="utf-8")
    loaded = yaml.safe_load(raw)
    if not isinstance(loaded, dict):
        raise ConfigurationValidationError(f"{path} must contain a mapping")
    return cast(YamlNode, loaded)


def canonical_utf8(payload: YamlNode) -> CanonicalUtf8Bytes:
    return rfc8785.dumps(payload)


def configuration_digest(config: ScientificConfig) -> ConfigurationDigest:
    record: YamlNode = cast(YamlNode, config.model_dump(mode="json"))
    digest = hashlib.sha256(canonical_utf8(record)).hexdigest()
    return digest


def histogram_edges(bin_count: BinCount) -> tuple[RankValue, ...]:
    return tuple(index / bin_count for index in range(bin_count + 1))


def minimum_zero_false_stop_horizons(
    target_pfa: FalseAlarmRate, confidence: ConfidenceLevel
) -> PositiveInt:
    if target_pfa <= 0.0 or target_pfa >= 1.0:
        raise ConfigurationValidationError("target_pfa must lie in (0, 1)")
    if confidence <= 0.0 or confidence >= 1.0:
        raise ConfigurationValidationError("calibration_confidence must lie in (0, 1)")
    return math.ceil(math.log(1.0 - confidence) / math.log(1.0 - target_pfa))


def derive_scientific_values(config: ScientificConfig) -> DerivedScientificValues:
    clip_bound = config.evidence.clip_bound
    bet_lambda = config.evidence.bet_lambda
    compensator = (bet_lambda**2) * ((2.0 * clip_bound) ** 2) / 8.0
    real_confirmatory_count = len(config.randomness.real_confirmatory_roots)
    return DerivedScientificValues(
        model_input_dimension=config.datasets.preprocessing.event_type_hash_bucket_count + 2,
        heldout_benign_is_remainder=True,
        local_horizon_epochs=config.campaign.evaluation_horizon_epochs,
        synthetic_campaign_horizon_epochs=config.campaign.evaluation_horizon_epochs,
        synthetic_campaign_warmup_epochs=config.campaign.prestart_warmup_epochs,
        synthetic_development_seed_count=len(config.randomness.synthetic_development_roots),
        synthetic_confirmatory_seed_count=len(config.randomness.synthetic_confirmatory_roots),
        real_development_seed_count=len(config.randomness.real_development_roots),
        real_confirmatory_seed_count=real_confirmatory_count,
        exact_real_sign_flip_assignment_count=2**real_confirmatory_count,
        minimum_nonoverlapping_horizons_for_zero_false_stop=minimum_zero_false_stop_horizons(
            config.evidence.calibrated_finite_horizon.target_pfa,
            config.evidence.calibrated_finite_horizon.calibration_confidence,
        ),
        signed_theorem_e_sr_threshold=1.0 / config.evidence.signed_theorem_sequential.arl_alpha,
        signed_theorem_compensator=compensator,
        histogram_edge_count=config.context.outside_histogram_bin_count + 1,
        outside_histogram_edges=histogram_edges(config.context.outside_histogram_bin_count),
        primary_odi_table_method_order=config.experiments.primary_strict_odi_evaluation.methods,
        context_seed=config.randomness.context_base_seed,
    )


def load_scientific_configuration(
    path: Path,
    profile: ConfigurationProfile,
) -> LoadedScientificConfiguration:
    payload = _load_mapping(path)
    reject_forbidden_derived_keys(payload)
    config = ScientificConfig.model_validate(payload)
    derived = derive_scientific_values(config)
    digest = configuration_digest(config)
    return LoadedScientificConfiguration(
        profile=profile,
        source_path=str(path),
        values=config,
        derived=derived,
        material_digest=digest,
    )


def load_production_configuration(
    root: Path | None = None,
) -> LoadedScientificConfiguration:
    repository = root or repository_root()
    return load_scientific_configuration(
        repository / PRODUCTION_CONFIGURATION_RELATIVE_PATH,
        ConfigurationProfile.PRODUCTION,
    )


def production_configuration_context(
    root: Path | None = None,
) -> tuple[Path, LoadedScientificConfiguration]:
    repository = root or repository_root()
    return repository, load_production_configuration(repository)


def load_tests_configuration(root: Path | None = None) -> LoadedScientificConfiguration:
    repository = root or repository_root()
    return load_scientific_configuration(
        repository / TESTS_CONFIGURATION_RELATIVE_PATH,
        ConfigurationProfile.TESTS,
    )


def load_smoke_configuration(root: Path | None = None) -> LoadedScientificConfiguration:
    repository = root or repository_root()
    return load_scientific_configuration(
        repository / SMOKE_CONFIGURATION_RELATIVE_PATH,
        ConfigurationProfile.SMOKE,
    )
