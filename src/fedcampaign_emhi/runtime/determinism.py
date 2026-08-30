import hashlib

import rfc8785

from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.types import (
    CanonicalUtf8Bytes,
    ConfigurationDigest,
    SeedDerivationIdentity,
    SeedValue,
    ThirtyTwoBitSeed,
)

THIRTY_TWO_BIT_MODULUS = 1 << 32
RFC8785_SAFE_INTEGER_MODULUS = 1 << 53


def deterministic_utf8_bytes(payload: YamlNode) -> CanonicalUtf8Bytes:
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
