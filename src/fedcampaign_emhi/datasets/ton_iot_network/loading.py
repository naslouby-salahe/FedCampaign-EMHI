import csv
from pathlib import Path

from fedcampaign_emhi.config.schema import DatasetsPrimaryConfig
from fedcampaign_emhi.datasets.ton_iot_network.validation import schema_is_executable


def validate_ton_iot_network_csv_schema(path: Path, schema: DatasetsPrimaryConfig) -> None:
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = tuple(reader.fieldnames or ())
    if not schema_is_executable(fieldnames, schema.required_columns):
        raise ValueError(
            f"{path} is missing required TON_IoT Network columns {schema.required_columns}"
        )
