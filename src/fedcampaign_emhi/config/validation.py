from collections.abc import Mapping, Sequence

from fedcampaign_emhi.domain.enums import DerivedConfigurationKey
from fedcampaign_emhi.domain.types import YamlKeyPath, YamlNode

FORBIDDEN_DERIVED_KEYS = frozenset(DerivedConfigurationKey)


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
