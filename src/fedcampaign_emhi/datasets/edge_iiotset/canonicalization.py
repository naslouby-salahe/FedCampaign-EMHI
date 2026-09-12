import unicodedata

from fedcampaign_emhi.domain.types import Boolean, NormalizedEventToken

UNKNOWN_PROTOCOL_GROUP = "UNKNOWN_PROTOCOL"
PROTOCOL_GROUP_PREFIXES = ("arp.", "http.", "tcp.", "udp.", "icmp.", "mqtt.", "mbtcp.")
UNRESOLVED_PROTOCOL_PAYLOADS = ("", "-", "0", "0.0", "0.0.0.0")
UNKNOWN_NORMALIZED_EVENT_TYPE = f"PROTOCOL::{UNKNOWN_PROTOCOL_GROUP}"


def protocol_payload_is_resolvable(payload: NormalizedEventToken | None) -> Boolean:
    if payload is None:
        return False
    return payload.strip() not in UNRESOLVED_PROTOCOL_PAYLOADS


def dominant_protocol_group_for_row(
    fields: tuple[tuple[NormalizedEventToken, NormalizedEventToken | None], ...],
) -> NormalizedEventToken:
    for prefix in PROTOCOL_GROUP_PREFIXES:
        for column, payload in fields:
            if column.startswith(prefix) and protocol_payload_is_resolvable(payload):
                return prefix[:-1]
    return UNKNOWN_PROTOCOL_GROUP


def normalize_event_type(protocol_group: NormalizedEventToken) -> NormalizedEventToken:
    stripped = protocol_group.strip()
    if not stripped or stripped == UNKNOWN_PROTOCOL_GROUP:
        return UNKNOWN_NORMALIZED_EVENT_TYPE
    normalized = unicodedata.normalize("NFKC", stripped.upper())
    if not normalized:
        return UNKNOWN_NORMALIZED_EVENT_TYPE
    return f"PROTOCOL::{normalized}"


def record_enters_epoch_event_count(protocol_group: NormalizedEventToken) -> Boolean:
    return protocol_group.strip() != UNKNOWN_PROTOCOL_GROUP and bool(protocol_group.strip())
