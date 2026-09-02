import hashlib
from pathlib import Path

from fedcampaign_emhi.domain.enums import SupportState
from fedcampaign_emhi.domain.types import (
    Boolean,
    ClientBenignTally,
    ClientCount,
    ClientEligibilityRecord,
    ConfigurationDigest,
    NormalizedEventToken,
    PositiveEpochCount,
    PrimaryClientSelection,
    RecordCount,
)

REQUIRED_TON_IOT_NETWORK_COLUMNS = (
    "ts",
    "src_ip",
    "proto",
    "service",
    "label",
    "type",
)


def missing_required_columns(
    observed_columns: tuple[NormalizedEventToken, ...],
) -> tuple[NormalizedEventToken, ...]:
    observed = {column.strip() for column in observed_columns}
    return tuple(column for column in REQUIRED_TON_IOT_NETWORK_COLUMNS if column not in observed)


def schema_is_executable(observed_columns: tuple[NormalizedEventToken, ...]) -> Boolean:
    return not missing_required_columns(observed_columns)


def adapter_material_code_fingerprint() -> ConfigurationDigest:
    digest = hashlib.sha256()
    directory = Path(__file__).resolve().parent
    for name in ("canonicalization.py", "loading.py", "ground_truth.py", "validation.py"):
        digest.update((directory / name).read_bytes())
    return digest.hexdigest()


def select_primary_clients_from_tallies(
    tallies: tuple[ClientBenignTally, ...],
    minimum_benign_event_records: RecordCount,
    minimum_nonempty_benign_epochs: PositiveEpochCount,
    target_client_count: ClientCount,
) -> PrimaryClientSelection:
    eligibility: list[ClientEligibilityRecord] = []
    for tally in sorted(tallies, key=lambda tally: tally.client_id):
        nonempty_epochs = len(tally.observed_epoch_indexes)
        eligible = (
            tally.benign_event_count >= minimum_benign_event_records
            and nonempty_epochs >= minimum_nonempty_benign_epochs
        )
        eligibility.append(
            ClientEligibilityRecord(
                client_id=tally.client_id,
                benign_event_count=tally.benign_event_count,
                benign_nonempty_epoch_count=nonempty_epochs,
                is_eligible=eligible,
            )
        )
    ranked = sorted(
        (candidate for candidate in eligibility if candidate.is_eligible),
        key=lambda candidate: (-candidate.benign_event_count, candidate.client_id),
    )
    eligible_ids = tuple(candidate.client_id for candidate in ranked)
    if len(eligible_ids) < target_client_count:
        return PrimaryClientSelection(
            selected_client_ids=(),
            eligible_client_ids=eligible_ids,
            eligibility=tuple(eligibility),
            support_state=SupportState.NOT_TESTED,
        )
    return PrimaryClientSelection(
        selected_client_ids=eligible_ids[:target_client_count],
        eligible_client_ids=eligible_ids,
        eligibility=tuple(eligibility),
        support_state=SupportState.SUPPORTED,
    )
