from collections.abc import Mapping, Sequence

from fedcampaign_emhi.domain.types import Boolean, YamlKeyPath

type YamlNode = str | int | float | Boolean | Sequence[YamlNode] | Mapping[str, YamlNode] | None

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
