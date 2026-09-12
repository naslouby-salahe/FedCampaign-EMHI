from collections.abc import Mapping, Sequence

from fedcampaign_emhi.domain.types import Boolean, YamlKeyPath

type YamlNode = str | int | float | Boolean | Sequence[YamlNode] | Mapping[str, YamlNode] | None #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this

FORBIDDEN_DERIVED_KEYS = frozenset(
    {
        "heldout_benign", #TODO: should be enums not hardcoded strings
        "model_input_dimension", #TODO: should be enums not hardcoded strings
        "local_horizon_epochs", #TODO: should be enums not hardcoded strings
        "histogram_edges", #TODO: should be enums not hardcoded strings
        "seed_count", #TODO: should be enums not hardcoded strings
        "synthetic_campaign_horizon_epochs", #TODO: should be enums not hardcoded strings
        "synthetic_campaign_warmup_epochs", #TODO: should be enums not hardcoded strings
        "signed_theorem_e_sr_threshold", #TODO: should be enums not hardcoded strings
        "signed_theorem_compensator", #TODO: should be enums not hardcoded strings
        "minimum_nonoverlapping_horizons_for_zero_false_stop", #TODO: should be enums not hardcoded strings
        "exact_real_sign_flip_assignment_count", #TODO: should be enums not hardcoded strings
        "primary_odi_table_method_order", #TODO: should be enums not hardcoded strings
        "derived_feature_dimension", #TODO: should be enums not hardcoded strings
        "equal_order_weights", #TODO: should be enums not hardcoded strings
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
