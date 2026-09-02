import csv
from pathlib import Path

from fedcampaign_emhi.datasets.ton_iot_network.validation import (
    REQUIRED_TON_IOT_NETWORK_COLUMNS,
    schema_is_executable,
)


def validate_ton_iot_network_csv_schema(path: Path) -> None:
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = tuple(reader.fieldnames or ())
    if not schema_is_executable(fieldnames):
        raise ValueError(
            f"{path} is missing required TON_IoT Network columns {REQUIRED_TON_IOT_NETWORK_COLUMNS}"
        )
