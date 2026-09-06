import re
from collections.abc import Iterator, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import polars as pl

from fedcampaign_emhi.datasets.edge_iiotset.canonicalization import dominant_protocol_group_for_row
from fedcampaign_emhi.datasets.edge_iiotset.validation import (
    REQUIRED_EDGE_IIOTSET_COLUMNS,
    record_identity_is_usable,
    schema_is_executable,
)
from fedcampaign_emhi.domain.enums import RecordExclusionReason
from fedcampaign_emhi.domain.types import (
    BinaryClassLabel,
    ClientId,
    EdgeIiotsetFlowRecord,
    ExcludedRecord,
    NormalizedEventToken,
    UnixTimestampSeconds,
)

EDGE_IIOTSET_TIMEZONE = UTC
EDGE_IIOTSET_NAIVE_BASE_MONTH_DAY = (1, 1)


def _parse_row_fields(
    row: Mapping[NormalizedEventToken, NormalizedEventToken | None],
) -> tuple[UnixTimestampSeconds, ClientId, BinaryClassLabel, NormalizedEventToken] | ExcludedRecord:
    source_host = (row.get("ip.src_host") or "").strip()
    if not source_host:
        return ExcludedRecord(reason=RecordExclusionReason.MISSING_FIELD_VALUE)
    if not record_identity_is_usable(source_host):
        return ExcludedRecord(reason=RecordExclusionReason.UNUSABLE_HOST_IDENTITY)
    try:
        timestamp_seconds = parse_frame_time(row.get("frame.time") or "")
    except (TypeError, ValueError):
        return ExcludedRecord(reason=RecordExclusionReason.UNPARSEABLE_TIMESTAMP)
    raw_label = row.get("Attack_label")
    if raw_label is None:
        return ExcludedRecord(reason=RecordExclusionReason.MISSING_FIELD_VALUE)
    try:
        binary_label = int(raw_label)
    except (TypeError, ValueError):
        return ExcludedRecord(reason=RecordExclusionReason.STRUCTURALLY_INVALID_EVENT)
    attack_type = (row.get("Attack_type") or "").strip()
    if not attack_type:
        return ExcludedRecord(reason=RecordExclusionReason.MISSING_FIELD_VALUE)
    return (timestamp_seconds, source_host, binary_label, attack_type)


def iter_edge_iiotset_csv_entries(
    path: Path,
) -> Iterator[EdgeIiotsetFlowRecord | ExcludedRecord]:
    header = pl.read_csv(path, n_rows=0, infer_schema_length=0)
    fieldnames = tuple(header.columns)
    if not schema_is_executable(fieldnames):
        raise ValueError(
            f"{path} is missing required Edge-IIoTset columns {REQUIRED_EDGE_IIOTSET_COLUMNS}"
        )
    schema_overrides = {name: pl.Utf8 for name in fieldnames}
    frame = pl.scan_csv(path, schema_overrides=schema_overrides, low_memory=True).collect()
    for raw_row in frame.iter_rows(named=True):
        row = {name: raw_row.get(name) for name in fieldnames}
        parsed = _parse_row_fields(
            cast(Mapping[NormalizedEventToken, NormalizedEventToken | None], row)
        )
        if isinstance(parsed, ExcludedRecord):
            yield parsed
            continue
        timestamp_seconds, source_host, binary_label, attack_type = parsed
        fields = tuple(
            (name, cast(NormalizedEventToken | None, row.get(name))) for name in fieldnames
        )
        yield (
            EdgeIiotsetFlowRecord(
                timestamp_seconds=timestamp_seconds,
                source_host=source_host,
                protocol_group=dominant_protocol_group_for_row(fields),
                binary_label=binary_label,
                attack_type=attack_type,
            )
        )


def parse_frame_time(raw_timestamp: NormalizedEventToken) -> UnixTimestampSeconds:
    stripped = raw_timestamp.strip()
    try:
        return float(stripped)
    except ValueError:
        match = re.fullmatch(r"(\d{4}) (\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?", stripped)
        if match is not None:
            year, hour, minute, second, fraction = match.groups()
            microseconds = int((fraction or "0")[:6].ljust(6, "0"))
            base_month, base_day = EDGE_IIOTSET_NAIVE_BASE_MONTH_DAY
            return datetime(
                int(year),
                base_month,
                base_day,
                int(hour),
                int(minute),
                int(second),
                microseconds,
                tzinfo=EDGE_IIOTSET_TIMEZONE,
            ).timestamp()
        parsed = datetime.fromisoformat(stripped)
        if parsed.tzinfo is None:
            raise ValueError(
                "naive Edge-IIoTset timestamps are invalid without a dataset timezone rule"
            ) from None
        return parsed.astimezone(UTC).timestamp()
