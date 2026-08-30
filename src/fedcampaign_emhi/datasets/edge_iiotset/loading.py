import csv
import re
from collections.abc import Iterator, Mapping
from datetime import UTC, datetime
from pathlib import Path

from fedcampaign_emhi.datasets.edge_iiotset.normalization import dominant_protocol_group_for_row
from fedcampaign_emhi.datasets.edge_iiotset.validation import (
    REQUIRED_EDGE_IIOTSET_COLUMNS,
    record_identity_is_usable,
    schema_is_executable,
)
from fedcampaign_emhi.domain.enums import RecordExclusionReason
from fedcampaign_emhi.domain.types import (
    ClientId,
    EdgeIiotsetFlowRecord,
    ExcludedRecord,
    FiniteFloat,
    NormalizedEventToken,
    UnixTimestampSeconds,
)


def load_edge_iiotset_csv(path: Path) -> tuple[EdgeIiotsetFlowRecord, ...]:
    records, _exclusions = load_edge_iiotset_csv_with_exclusions(path)
    return records


def _parse_row_fields(
    row: Mapping[NormalizedEventToken, NormalizedEventToken | None],
) -> tuple[FiniteFloat, ClientId, FiniteFloat, NormalizedEventToken] | ExcludedRecord:
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
    return (timestamp_seconds, source_host, float(binary_label), attack_type)


def load_edge_iiotset_csv_with_exclusions(
    path: Path,
) -> tuple[tuple[EdgeIiotsetFlowRecord, ...], tuple[ExcludedRecord, ...]]:
    records: list[EdgeIiotsetFlowRecord] = []
    exclusions: list[ExcludedRecord] = []
    for entry in iter_edge_iiotset_csv_entries(path):
        if isinstance(entry, ExcludedRecord):
            exclusions.append(entry)
        else:
            records.append(entry)
    return tuple(records), tuple(exclusions)


def iter_edge_iiotset_csv_entries(
    path: Path,
) -> Iterator[EdgeIiotsetFlowRecord | ExcludedRecord]:
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = tuple(reader.fieldnames or ())
        if not schema_is_executable(fieldnames):
            raise ValueError(
                f"{path} is missing required Edge-IIoTset columns {REQUIRED_EDGE_IIOTSET_COLUMNS}"
            )
        for row in reader:
            parsed = _parse_row_fields(row)
            if isinstance(parsed, ExcludedRecord):
                yield parsed
                continue
            timestamp_seconds, source_host, binary_label, attack_type = parsed
            fields = tuple((name, row.get(name)) for name in fieldnames)
            yield (
                EdgeIiotsetFlowRecord(
                    timestamp_seconds=timestamp_seconds,
                    source_host=source_host,
                    protocol_group=dominant_protocol_group_for_row(fields),
                    binary_label=int(binary_label),
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
            return datetime(
                int(year),
                1,
                1,
                int(hour),
                int(minute),
                int(second),
                microseconds,
                tzinfo=UTC,
            ).timestamp()
        parsed = datetime.fromisoformat(stripped)
        if parsed.tzinfo is None:
            raise ValueError(
                "naive Edge-IIoTset timestamps are invalid without a dataset timezone rule"
            ) from None
        return parsed.astimezone(UTC).timestamp()
