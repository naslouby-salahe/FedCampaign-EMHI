import hashlib

import rfc8785

from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.types import CanonicalUtf8Bytes, ConfigurationDigest


def canonical_utf8_bytes(payload: YamlNode) -> CanonicalUtf8Bytes:
    return rfc8785.dumps(payload)


def canonical_digest(payload: YamlNode) -> ConfigurationDigest:
    return hashlib.sha256(canonical_utf8_bytes(payload)).hexdigest()
