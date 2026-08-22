import csv
from pathlib import Path

from fedcampaign_emhi.datasets.edge_iiotset.canonicalization import dominant_protocol_group
from fedcampaign_emhi.datasets.edge_iiotset.validation import (
    REQUIRED_EDGE_IIOTSET_COLUMNS,
    schema_is_executable,
)
from fedcampaign_emhi.domain.types import (
    CanonicalEventToken,
    EdgeIiotsetFlowRecord,
    UnixTimestampSeconds,
)


def load_edge_iiotset_csv(path: Path) -> tuple[EdgeIiotsetFlowRecord, ...]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = tuple(reader.fieldnames or ())
        if not schema_is_executable(fieldnames):
            raise ValueError(
                f"{path} is missing required Edge-IIoTset columns {REQUIRED_EDGE_IIOTSET_COLUMNS}"
            )
        protocol_group = dominant_protocol_group(fieldnames)
        records: list[EdgeIiotsetFlowRecord] = []
        for row in reader:
            records.append(
                EdgeIiotsetFlowRecord(
                    timestamp_seconds=_parse_frame_time(row["frame.time"]),
                    source_host=row["ip.src_host"].strip(),
                    protocol_group=protocol_group,
                    binary_label=int(row["Attack_label"]),
                    attack_type=row["Attack_type"].strip(),
                )
            )
    return tuple(records)


def _parse_frame_time(raw_timestamp: CanonicalEventToken) -> UnixTimestampSeconds:
    stripped = raw_timestamp.strip()
    try:
        return float(stripped)
    except ValueError:
        from datetime import UTC, datetime

        parsed = datetime.fromisoformat(stripped)
        if parsed.tzinfo is None:
            raise ValueError(
                "naive Edge-IIoTset timestamps are invalid without a dataset timezone rule"
            ) from None
        return parsed.astimezone(UTC).timestamp()
