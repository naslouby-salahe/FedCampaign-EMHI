import csv
from collections.abc import Iterator
from pathlib import Path

from fedcampaign_emhi.datasets.ton_iot_network.canonicalization import (
    UNKNOWN_PROTOCOL_TOKEN,
    UNKNOWN_SERVICE_TOKEN,
    normalize_token,
)
from fedcampaign_emhi.datasets.ton_iot_network.validation import (
    REQUIRED_TON_IOT_NETWORK_COLUMNS,
    record_identity_is_usable,
    schema_is_executable,
)
from fedcampaign_emhi.domain.enums import RecordExclusionReason
from fedcampaign_emhi.domain.types import ExcludedRecord, TonIotNetworkFlowRecord


def load_ton_iot_network_csv(path: Path) -> tuple[TonIotNetworkFlowRecord, ...]:
    records, _exclusions = load_ton_iot_network_csv_with_exclusions(path)
    return records


def load_ton_iot_network_csv_with_exclusions(
    path: Path,
) -> tuple[tuple[TonIotNetworkFlowRecord, ...], tuple[ExcludedRecord, ...]]:
    records: list[TonIotNetworkFlowRecord] = []
    exclusions: list[ExcludedRecord] = []
    for entry in iter_ton_iot_network_csv_entries(path):
        if isinstance(entry, ExcludedRecord):
            exclusions.append(entry)
        else:
            records.append(entry)
    return tuple(records), tuple(exclusions)


def iter_ton_iot_network_csv_entries(
    path: Path,
) -> Iterator[TonIotNetworkFlowRecord | ExcludedRecord]:
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = tuple(reader.fieldnames or ())
        if not schema_is_executable(fieldnames):
            raise ValueError(
                f"{path} is missing required TON_IoT Network columns {REQUIRED_TON_IOT_NETWORK_COLUMNS}"
            )
        for row in reader:
            source_ip = (row.get("src_ip") or "").strip()
            if not source_ip:
                yield ExcludedRecord(reason=RecordExclusionReason.MISSING_FIELD_VALUE)
                continue
            if not record_identity_is_usable(source_ip):
                yield ExcludedRecord(reason=RecordExclusionReason.UNUSABLE_HOST_IDENTITY)
                continue
            try:
                timestamp_seconds = float(row["ts"])
            except (TypeError, ValueError):
                yield ExcludedRecord(reason=RecordExclusionReason.UNPARSEABLE_TIMESTAMP)
                continue
            try:
                binary_label = int(row["label"])
            except (TypeError, ValueError):
                yield ExcludedRecord(reason=RecordExclusionReason.STRUCTURALLY_INVALID_EVENT)
                continue
            attack_type = (row.get("type") or "").strip()
            if not attack_type:
                yield ExcludedRecord(reason=RecordExclusionReason.MISSING_FIELD_VALUE)
                continue
            yield (
                TonIotNetworkFlowRecord(
                    timestamp_seconds=timestamp_seconds,
                    source_ip=source_ip,
                    protocol_token=normalize_token(row.get("proto"), UNKNOWN_PROTOCOL_TOKEN),
                    service_token=normalize_token(row.get("service"), UNKNOWN_SERVICE_TOKEN),
                    binary_label=binary_label,
                    attack_type=attack_type,
                )
            )
