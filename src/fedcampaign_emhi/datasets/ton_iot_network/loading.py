import csv
from pathlib import Path

from fedcampaign_emhi.datasets.ton_iot_network.canonicalization import (
    UNKNOWN_PROTOCOL_TOKEN,
    UNKNOWN_SERVICE_TOKEN,
    canonicalize_token,
)
from fedcampaign_emhi.datasets.ton_iot_network.validation import (
    REQUIRED_TON_IOT_NETWORK_COLUMNS,
    schema_is_executable,
)
from fedcampaign_emhi.domain.types import TonIotNetworkFlowRecord


def load_ton_iot_network_csv(path: Path) -> tuple[TonIotNetworkFlowRecord, ...]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = tuple(reader.fieldnames or ())
        if not schema_is_executable(fieldnames):
            raise ValueError(
                f"{path} is missing required TON_IoT Network columns {REQUIRED_TON_IOT_NETWORK_COLUMNS}"
            )
        records: list[TonIotNetworkFlowRecord] = []
        for row in reader:
            records.append(
                TonIotNetworkFlowRecord(
                    timestamp_seconds=float(row["ts"]),
                    source_ip=row["src_ip"].strip(),
                    protocol_token=canonicalize_token(row.get("proto"), UNKNOWN_PROTOCOL_TOKEN),
                    service_token=canonicalize_token(row.get("service"), UNKNOWN_SERVICE_TOKEN),
                    binary_label=int(row["label"]),
                    attack_type=row["type"].strip(),
                )
            )
    return tuple(records)
