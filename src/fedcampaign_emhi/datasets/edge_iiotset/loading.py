import csv
from datetime import UTC, datetime
from pathlib import Path

from fedcampaign_emhi.datasets.edge_iiotset.canonicalization import dominant_protocol_group_for_row
from fedcampaign_emhi.datasets.edge_iiotset.validation import (
    REQUIRED_EDGE_IIOTSET_COLUMNS,
    record_identity_is_usable,
    schema_is_executable,
)
from fedcampaign_emhi.domain.enums import RecordExclusionReason
from fedcampaign_emhi.domain.types import (
    CanonicalEventToken,
    EdgeIiotsetFlowRecord,
    ExcludedRecord,
    UnixTimestampSeconds,
)


def load_edge_iiotset_csv(path: Path) -> tuple[EdgeIiotsetFlowRecord, ...]:
    records, _exclusions = load_edge_iiotset_csv_with_exclusions(path)
    return records


def load_edge_iiotset_csv_with_exclusions(
    path: Path,
) -> tuple[tuple[EdgeIiotsetFlowRecord, ...], tuple[ExcludedRecord, ...]]:
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = tuple(reader.fieldnames or ())
        if not schema_is_executable(fieldnames):
            raise ValueError(
                f"{path} is missing required Edge-IIoTset columns {REQUIRED_EDGE_IIOTSET_COLUMNS}"
            )
        records: list[EdgeIiotsetFlowRecord] = []
        exclusions: list[ExcludedRecord] = []
        for row in reader:
            source_host = (row.get("ip.src_host") or "").strip()
            if not record_identity_is_usable(source_host):
                exclusions.append(
                    ExcludedRecord(reason=RecordExclusionReason.UNUSABLE_HOST_IDENTITY)
                )
                continue
            try:
                timestamp_seconds = _parse_frame_time(row.get("frame.time") or "")
            except (TypeError, ValueError):
                exclusions.append(
                    ExcludedRecord(reason=RecordExclusionReason.UNPARSEABLE_TIMESTAMP)
                )
                continue
            try:
                binary_label = int(row["Attack_label"])
            except (TypeError, ValueError):
                exclusions.append(
                    ExcludedRecord(reason=RecordExclusionReason.STRUCTURALLY_INVALID_EVENT)
                )
                continue
            attack_type = (row.get("Attack_type") or "").strip()
            if not attack_type:
                exclusions.append(
                    ExcludedRecord(reason=RecordExclusionReason.STRUCTURALLY_INVALID_EVENT)
                )
                continue
            fields = tuple((name, row.get(name)) for name in fieldnames)
            records.append(
                EdgeIiotsetFlowRecord(
                    timestamp_seconds=timestamp_seconds,
                    source_host=source_host,
                    protocol_group=dominant_protocol_group_for_row(fields),
                    binary_label=binary_label,
                    attack_type=attack_type,
                )
            )
    return tuple(records), tuple(exclusions)


def _parse_frame_time(raw_timestamp: CanonicalEventToken) -> UnixTimestampSeconds:
    stripped = raw_timestamp.strip()
    try:
        return float(stripped)
    except ValueError:
        parsed = datetime.fromisoformat(stripped)
        if parsed.tzinfo is None:
            raise ValueError(
                "naive Edge-IIoTset timestamps are invalid without a dataset timezone rule"
            ) from None
        return parsed.astimezone(UTC).timestamp()
