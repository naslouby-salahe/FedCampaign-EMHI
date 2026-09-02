import hashlib
import unicodedata

from fedcampaign_emhi.domain.types import (
    ClientId,
    HashBucketCount,
    HashBucketIndex,
    NormalizedEventToken,
)

UNKNOWN_PROTOCOL_TOKEN = "UNKNOWN_PROTO"
UNKNOWN_SERVICE_TOKEN = "UNKNOWN_SERVICE"
ZEEK_MISSING_FIELD_TOKEN = "-"


def normalize_token(
    raw_token: NormalizedEventToken | None, missing_token: NormalizedEventToken
) -> NormalizedEventToken:
    if raw_token is None:
        return missing_token
    stripped = raw_token.strip()
    if not stripped or stripped == ZEEK_MISSING_FIELD_TOKEN:
        return missing_token
    return unicodedata.normalize("NFKC", stripped.upper())


def normalize_client_id(source_ip: ClientId) -> ClientId:
    return unicodedata.normalize("NFKC", source_ip.strip())


def normalize_event_type(
    protocol_token: NormalizedEventToken | None, service_token: NormalizedEventToken | None
) -> NormalizedEventToken:
    protocol = normalize_token(protocol_token, UNKNOWN_PROTOCOL_TOKEN)
    service = normalize_token(service_token, UNKNOWN_SERVICE_TOKEN)
    return f"{protocol}::{service}"


def event_type_hash_bucket(
    event_type: NormalizedEventToken, bucket_count: HashBucketCount
) -> HashBucketIndex:
    if bucket_count <= 0:
        raise ValueError("bucket_count must be positive")
    digest = hashlib.sha256(event_type.encode("utf-8")).digest()
    identity = int.from_bytes(digest[:8], "big")
    return identity % bucket_count
