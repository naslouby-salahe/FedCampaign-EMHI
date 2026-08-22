import hashlib
import unicodedata

from fedcampaign_emhi.domain.types import (
    CanonicalEventToken,
    HashBucketCount,
    SignedInt,
)

UNKNOWN_PROTOCOL_TOKEN = "UNKNOWN_PROTO"
UNKNOWN_SERVICE_TOKEN = "UNKNOWN_SERVICE"


def canonicalize_token(
    raw_token: CanonicalEventToken | None, missing_token: CanonicalEventToken
) -> CanonicalEventToken:
    if raw_token is None:
        return missing_token
    stripped = raw_token.strip()
    if not stripped:
        return missing_token
    return unicodedata.normalize("NFKC", stripped.upper())


def canonical_event_type(
    protocol_token: CanonicalEventToken | None, service_token: CanonicalEventToken | None
) -> CanonicalEventToken:
    protocol = canonicalize_token(protocol_token, UNKNOWN_PROTOCOL_TOKEN)
    service = canonicalize_token(service_token, UNKNOWN_SERVICE_TOKEN)
    return f"{protocol}::{service}"


def event_type_hash_bucket(
    event_type: CanonicalEventToken, bucket_count: HashBucketCount
) -> SignedInt:
    if bucket_count <= 0:
        raise ValueError("bucket_count must be positive")
    digest = hashlib.sha256(event_type.encode("utf-8")).digest()
    identity = int.from_bytes(digest[:8], "big")
    return identity % bucket_count
