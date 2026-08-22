from collections.abc import Mapping, Sequence
from math import isfinite

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.types import FiniteFloat, YamlKeyPath

type YamlNode = str | int | float | bool | Sequence[YamlNode] | Mapping[str, YamlNode] | None

FORBIDDEN_DERIVED_KEYS = frozenset(
    {
        "heldout_benign",
        "model_input_dimension",
        "local_horizon_epochs",
        "histogram_edges",
        "seed_count",
        "synthetic_campaign_horizon_epochs",
        "synthetic_campaign_warmup_epochs",
        "signed_theorem_e_sr_threshold",
        "signed_theorem_compensator",
        "minimum_nonoverlapping_horizons_for_zero_false_stop",
        "exact_real_sign_flip_assignment_count",
        "primary_odi_table_method_order",
        "derived_feature_dimension",
        "equal_order_weights",
    }
)


class ConfigurationValidationError(ValueError):
    pass


def collect_forbidden_derived_keys(
    payload: YamlNode, trail: tuple[YamlKeyPath, ...] = ()
) -> tuple[YamlKeyPath, ...]:
    discovered: list[YamlKeyPath] = []
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            location = ".".join((*trail, key))
            if key in FORBIDDEN_DERIVED_KEYS:
                discovered.append(location)
            discovered.extend(collect_forbidden_derived_keys(value, (*trail, key)))
    elif isinstance(payload, Sequence) and not isinstance(payload, str | bytes):
        for index, item in enumerate(payload):
            discovered.extend(collect_forbidden_derived_keys(item, (*trail, str(index))))
    return tuple(discovered)


def reject_forbidden_derived_keys(payload: YamlNode) -> None:
    discovered = collect_forbidden_derived_keys(payload)
    if discovered:
        joined = ", ".join(discovered)
        raise ConfigurationValidationError(
            f"derived configuration values are not independently configurable: {joined}"
        )


def _require_finite(field_name: YamlKeyPath, numeric_value: FiniteFloat) -> None:
    if not isfinite(numeric_value):
        raise ConfigurationValidationError(f"{field_name} must be finite")


def validate_scientific_config(config: ScientificConfig) -> None:
    fractions = config.datasets.preprocessing.benign_partition_fractions
    fraction_sum = (
        fractions.detector_fit + fractions.nuisance_fit + fractions.threshold_and_policy_calibration
    )
    if fractions.detector_fit <= 0.0 or fractions.nuisance_fit <= 0.0:
        raise ConfigurationValidationError("benign partition fractions must be positive")
    if fractions.threshold_and_policy_calibration <= 0.0:
        raise ConfigurationValidationError("benign partition fractions must be positive")
    if fraction_sum >= 1.0:
        raise ConfigurationValidationError(
            "heldout_benign is the chronological remainder and is not independently configurable"
        )
    if config.study.maximum_coalition_order < 1:
        raise ConfigurationValidationError("maximum_coalition_order must be at least 1")
    if config.artifacts.outputs_root == config.artifacts.results_root:
        raise ConfigurationValidationError("outputs_root and results_root must be distinct")
    if config.runtime.required_confirmatory_missing_cell_tolerance < 0:
        raise ConfigurationValidationError(
            "required_confirmatory_missing_cell_tolerance must be non-negative"
        )
    if 0.0 not in config.projection.ridge_candidates:
        raise ConfigurationValidationError("ridge_candidates must include 0.0")
    persistence = tuple(
        (item.required_exceedances, item.window_epochs)
        for item in config.local_policy.candidate_persistence
    )
    if persistence != ((1, 1), (2, 3), (3, 5)):
        raise ConfigurationValidationError(
            "candidate persistence must be the fixed 1-of-1, 2-of-3, 3-of-5 sequence"
        )
    _require_finite("evidence.clip_bound", config.evidence.clip_bound)
    _require_finite("evidence.bet_lambda", config.evidence.bet_lambda)
    _require_finite("context.rank_clip_epsilon", config.context.rank_clip_epsilon)
    if config.evidence.clip_bound <= 0.0:
        raise ConfigurationValidationError("evidence.clip_bound must be positive")
    if config.evidence.bet_lambda <= 0.0:
        raise ConfigurationValidationError("evidence.bet_lambda must be positive")
    if config.time.real_data_epoch_seconds <= 0:
        raise ConfigurationValidationError("real_data_epoch_seconds must be positive")
    if config.datasets.primary.name == config.datasets.secondary.name:
        raise ConfigurationValidationError("primary and secondary datasets must differ")
