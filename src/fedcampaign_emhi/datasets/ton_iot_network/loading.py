import csv
from pathlib import Path

from fedcampaign_emhi.datasets.ton_iot_network.canonicalization import (
    UNKNOWN_PROTOCOL_TOKEN,
    UNKNOWN_SERVICE_TOKEN,
    canonicalize_token,
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
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = tuple(reader.fieldnames or ())
        if not schema_is_executable(fieldnames):
            raise ValueError(
                f"{path} is missing required TON_IoT Network columns {REQUIRED_TON_IOT_NETWORK_COLUMNS}"
            )
        records: list[TonIotNetworkFlowRecord] = []
        exclusions: list[ExcludedRecord] = []
        for row in reader:
            source_ip = (row.get("src_ip") or "").strip()
            if not record_identity_is_usable(source_ip):
                exclusions.append(
                    ExcludedRecord(reason=RecordExclusionReason.UNUSABLE_HOST_IDENTITY)
                )
                continue
            try:
                timestamp_seconds = float(row["ts"])
            except (TypeError, ValueError):
                exclusions.append(
                    ExcludedRecord(reason=RecordExclusionReason.UNPARSEABLE_TIMESTAMP)
                )
                continue
            try:
                binary_label = int(row["label"])
            except (TypeError, ValueError):
                exclusions.append(
                    ExcludedRecord(reason=RecordExclusionReason.STRUCTURALLY_INVALID_EVENT)
                )
                continue
            attack_type = (row.get("type") or "").strip()
            if not attack_type:
                exclusions.append(
                    ExcludedRecord(reason=RecordExclusionReason.STRUCTURALLY_INVALID_EVENT)
                )
                continue
            records.append(
                TonIotNetworkFlowRecord(
                    timestamp_seconds=timestamp_seconds,
                    source_ip=source_ip,
                    protocol_token=canonicalize_token(row.get("proto"), UNKNOWN_PROTOCOL_TOKEN),
                    service_token=canonicalize_token(row.get("service"), UNKNOWN_SERVICE_TOKEN),
                    binary_label=binary_label,
                    attack_type=attack_type,
                )
            )
    return tuple(records), tuple(exclusions)
