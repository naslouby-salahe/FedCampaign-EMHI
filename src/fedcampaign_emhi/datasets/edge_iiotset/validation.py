import hashlib
from pathlib import Path

from fedcampaign_emhi.datasets.edge_iiotset.ground_truth import edge_iiotset_ground_truth
from fedcampaign_emhi.datasets.eligibility import build_eligibility_records
from fedcampaign_emhi.datasets.partitions import epoch_index
from fedcampaign_emhi.domain.enums import GroundTruthClass, SupportState
from fedcampaign_emhi.domain.types import (
    Boolean,
    ClientBenignTally,
    ClientCount,
    ClientId,
    ConfigurationDigest,
    EdgeIiotsetFlowRecord,
    EpochIndexValue,
    EpochSeconds,
    NormalizedEventToken,
    PositiveEpochCount,
    RecordCount,
    SecondaryClientSelection,
)

REQUIRED_EDGE_IIOTSET_COLUMNS = (
    "frame.time",
    "ip.src_host",
    "Attack_label",
    "Attack_type",
)


def missing_required_columns(
    observed_columns: tuple[NormalizedEventToken, ...],
) -> tuple[NormalizedEventToken, ...]:
    observed = {column.strip() for column in observed_columns}
    return tuple(column for column in REQUIRED_EDGE_IIOTSET_COLUMNS if column not in observed)


def schema_is_executable(observed_columns: tuple[NormalizedEventToken, ...]) -> Boolean:
    return not missing_required_columns(observed_columns)


def adapter_material_code_fingerprint() -> ConfigurationDigest:
    digest = hashlib.sha256()
    directory = Path(__file__).resolve().parent
    for name in ("canonicalization.py", "loading.py", "ground_truth.py", "validation.py"):
        digest.update((directory / name).read_bytes())
    return digest.hexdigest()


def record_is_benign(record: EdgeIiotsetFlowRecord) -> Boolean:
    return (
        edge_iiotset_ground_truth(record.binary_label, record.attack_type).classification
        is GroundTruthClass.BENIGN
    )


def record_identity_is_usable(source_host: ClientId) -> Boolean:
    return bool(source_host.strip())


def _add_benign_event(
    tallies: tuple[ClientBenignTally, ...],
    client_id: ClientId,
    epoch: EpochIndexValue,
) -> tuple[ClientBenignTally, ...]:
    replaced: list[ClientBenignTally] = []
    matched = False
    for tally in tallies:
        if tally.client_id != client_id:
            replaced.append(tally)
            continue
        matched = True
        epochs = tally.observed_epoch_indexes
        if epoch not in epochs:
            epochs = (*epochs, epoch)
        replaced.append(
            ClientBenignTally(
                client_id=client_id,
                benign_event_count=tally.benign_event_count + 1,
                observed_epoch_indexes=epochs,
            )
        )
    if not matched:
        replaced.append(
            ClientBenignTally(
                client_id=client_id,
                benign_event_count=1,
                observed_epoch_indexes=(epoch,),
            )
        )
    return tuple(replaced)


def select_secondary_clients(
    records: tuple[EdgeIiotsetFlowRecord, ...],
    epoch_seconds: EpochSeconds,
    minimum_benign_event_records: RecordCount,
    minimum_nonempty_benign_epochs: PositiveEpochCount,
    target_client_count: ClientCount,
    minimum_eligible_client_count: ClientCount,
) -> SecondaryClientSelection:
    tallies: tuple[ClientBenignTally, ...] = ()
    for record in records:
        if not record_identity_is_usable(record.source_host):
            continue
        if not record_is_benign(record):
            continue
        client_id = record.source_host.strip()
        epoch = epoch_index(record.timestamp_seconds, epoch_seconds).index
        tallies = _add_benign_event(tallies, client_id, epoch)
    return select_secondary_clients_from_tallies(
        tallies,
        minimum_benign_event_records,
        minimum_nonempty_benign_epochs,
        target_client_count,
        minimum_eligible_client_count,
    )


def select_secondary_clients_from_tallies(
    tallies: tuple[ClientBenignTally, ...],
    minimum_benign_event_records: RecordCount,
    minimum_nonempty_benign_epochs: PositiveEpochCount,
    target_client_count: ClientCount,
    minimum_eligible_client_count: ClientCount,
) -> SecondaryClientSelection:
    eligibility = build_eligibility_records(
        tallies, minimum_benign_event_records, minimum_nonempty_benign_epochs
    )
    ranked = sorted(
        (candidate for candidate in eligibility if candidate.is_eligible),
        key=lambda candidate: (-candidate.benign_event_count, candidate.client_id),
    )
    eligible_ids = tuple(candidate.client_id for candidate in ranked)
    if len(eligible_ids) < minimum_eligible_client_count:
        return SecondaryClientSelection(
            selected_client_ids=(),
            eligible_client_ids=eligible_ids,
            eligibility=eligibility,
            support_state=SupportState.NOT_TESTED,
        )
    if len(eligible_ids) < target_client_count:
        return SecondaryClientSelection(
            selected_client_ids=eligible_ids,
            eligible_client_ids=eligible_ids,
            eligibility=eligibility,
            support_state=SupportState.SUPPORTED,
        )
    return SecondaryClientSelection(
        selected_client_ids=eligible_ids[:target_client_count],
        eligible_client_ids=eligible_ids,
        eligibility=eligibility,
        support_state=SupportState.SUPPORTED,
    )
