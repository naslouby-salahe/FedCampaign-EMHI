import csv
from io import StringIO
from pathlib import Path

from fedcampaign_emhi.artifacts.records import SeedSummaryRecord
from fedcampaign_emhi.domain.types import DeterministicUtf8Bytes


def load_seed_summaries(paths: tuple[Path, ...]) -> tuple[SeedSummaryRecord, ...]:
    return tuple(SeedSummaryRecord.model_validate_json(path.read_bytes()) for path in paths)


def seed_summary_csv(records: tuple[SeedSummaryRecord, ...]) -> DeterministicUtf8Bytes:
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        (
            "experiment",
            "execution_role",
            "method",
            "reference_method",
            "metric",
            "seed",
            "method_value",
            "reference_value",
            "paired_difference",
            "campaign_count",
        )
    )
    for record in records:
        writer.writerow(
            (
                record.experiment_name.value,
                record.execution_role.value,
                record.method_name.value,
                "" if record.reference_method_name is None else record.reference_method_name.value,
                record.metric_name,
                record.seed,
                record.method_value,
                "" if record.reference_value is None else record.reference_value,
                "" if record.paired_difference is None else record.paired_difference,
                record.campaign_count,
            )
        )
    return output.getvalue().encode("utf-8")


def write_seed_summary_table(destination: Path, records: tuple[SeedSummaryRecord, ...]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_suffix(destination.suffix + ".partial")
    staging.write_bytes(seed_summary_csv(records))
    staging.replace(destination)
