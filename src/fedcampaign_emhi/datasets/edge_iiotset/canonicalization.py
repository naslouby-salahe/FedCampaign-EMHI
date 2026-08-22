import unicodedata

from fedcampaign_emhi.domain.types import CanonicalEventToken

UNKNOWN_PROTOCOL_GROUP = "UNKNOWN_PROTOCOL"
PROTOCOL_GROUP_PREFIXES = ("arp.", "http.", "tcp.", "udp.", "icmp.", "mqtt.", "mbtcp.")


def dominant_protocol_group(column_names: tuple[CanonicalEventToken, ...]) -> CanonicalEventToken:
    for prefix in PROTOCOL_GROUP_PREFIXES:
        if any(column.startswith(prefix) for column in column_names):
            return prefix[:-1]
    return UNKNOWN_PROTOCOL_GROUP


def canonical_event_type(protocol_group: CanonicalEventToken) -> CanonicalEventToken:
    normalized = unicodedata.normalize("NFKC", protocol_group.strip().upper())
    if not normalized:
        normalized = UNKNOWN_PROTOCOL_GROUP
    return f"PROTOCOL::{normalized}"
