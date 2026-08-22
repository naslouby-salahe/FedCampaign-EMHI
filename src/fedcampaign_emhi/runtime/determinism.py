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


def canonical_utf8_bytes(payload: YamlNode) -> CanonicalUtf8Bytes:
    return rfc8785.dumps(payload)


def canonical_digest(payload: YamlNode) -> ConfigurationDigest:
    return hashlib.sha256(canonical_utf8_bytes(payload)).hexdigest()


def seed_derivation_payload(identity: SeedDerivationIdentity) -> YamlNode:
    coordinates = {
        coordinate.name: coordinate.scalar for coordinate in identity.condition_coordinates
    }
    dataset_name = None if identity.dataset is None else identity.dataset.value
    return {
        "base_seed": identity.base_seed,
        "component_name": identity.component_name,
        "dataset": dataset_name,
        "client_ids": list(sorted(identity.client_ids)),
        "coalition_ids": list(sorted(identity.coalition_ids)),
        "condition_coordinates": coordinates,
    }


def derive_component_seed(identity: SeedDerivationIdentity) -> SeedValue:
    digest = hashlib.sha256(canonical_utf8_bytes(seed_derivation_payload(identity))).digest()
    return int.from_bytes(digest[:8], "big")


def thirty_two_bit_seed(seed: SeedValue) -> ThirtyTwoBitSeed:
    return seed % THIRTY_TWO_BIT_MODULUS
