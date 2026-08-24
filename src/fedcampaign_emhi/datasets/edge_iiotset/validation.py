import hashlib
from pathlib import Path

from fedcampaign_emhi.datasets.edge_iiotset.canonicalization import (
    record_enters_epoch_event_count,
)
from fedcampaign_emhi.datasets.edge_iiotset.ground_truth import edge_iiotset_ground_truth
from fedcampaign_emhi.datasets.partitions import epoch_index
from fedcampaign_emhi.domain.enums import ClaimState, ExperimentState, GroundTruthClass
from fedcampaign_emhi.domain.types import (
    CanonicalEventToken,
    ClientBenignTally,
    ClientCount,
    ClientEligibilityRecord,
    ClientId,
    ConfigurationDigest,
    EdgeIiotsetBenignEvaluationSeparation,
    EdgeIiotsetFlowRecord,
    EdgeIiotsetGroundTruthDiscrepancy,
    EpochGroundTruthAttachment,
    EpochIndex,
    EpochIndexValue,
    EpochSeconds,
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
DOCUMENTED_IDENTITY_COLUMNS = (
    "frame.time",
    "ip.src_host",
    "ip.dst_host",
)
DOCUMENTED_ATTACK_TYPE_EXPECTATIONS = (
    "Normal",
    "DDoS_UDP",
    "DDoS_ICMP",
    "DDoS_TCP",
    "DDoS_HTTP",
    "SQL_injection",
    "Uploading",
    "Backdoor",
    "Port_Scanning",
    "Vulnerability_scanner",
    "Password",
    "XSS",
    "Ransomware",
    "Fingerprinting",
    "MITM",
)
DOCUMENTED_PROTOCOL_GROUP_PREFIXES = (
    "arp.",
    "http.",
    "tcp.",
    "udp.",
    "icmp.",
    "mqtt.",
    "mbtcp.",
)


def missing_required_columns(
    observed_columns: tuple[CanonicalEventToken, ...],
) -> tuple[CanonicalEventToken, ...]:
    observed = {column.strip() for column in observed_columns}
    return tuple(column for column in REQUIRED_EDGE_IIOTSET_COLUMNS if column not in observed)


def schema_is_executable(observed_columns: tuple[CanonicalEventToken, ...]) -> bool:
    return not missing_required_columns(observed_columns)


def observed_schema_preprocessing_state(
    observed_columns: tuple[CanonicalEventToken, ...],
) -> ExperimentState:
    if schema_is_executable(observed_columns):
        return ExperimentState.READY
    return ExperimentState.INVALID


def adapter_material_code_fingerprint() -> ConfigurationDigest:
    digest = hashlib.sha256()
    directory = Path(__file__).resolve().parent
    for name in ("canonicalization.py", "loading.py", "ground_truth.py", "validation.py"):
        digest.update((directory / name).read_bytes())
    return digest.hexdigest()


def documented_attack_type_is_expected(attack_type: CanonicalEventToken) -> bool:
    return attack_type.strip() in DOCUMENTED_ATTACK_TYPE_EXPECTATIONS


def documented_identity_columns() -> tuple[CanonicalEventToken, ...]:
    return DOCUMENTED_IDENTITY_COLUMNS


def documented_protocol_group_prefixes() -> tuple[CanonicalEventToken, ...]:
    return DOCUMENTED_PROTOCOL_GROUP_PREFIXES


def epoch_of_record(record: EdgeIiotsetFlowRecord, epoch_seconds: EpochSeconds) -> EpochIndex:
    return epoch_index(record.timestamp_seconds, epoch_seconds)


def record_is_benign(record: EdgeIiotsetFlowRecord) -> bool:
    return (
        edge_iiotset_ground_truth(record.binary_label, record.attack_type).classification
        is GroundTruthClass.BENIGN
    )


def record_identity_is_usable(source_host: ClientId) -> bool:
    return bool(source_host.strip())


def attach_epoch_ground_truth(
    record: EdgeIiotsetFlowRecord, epoch_seconds: EpochSeconds
) -> EpochGroundTruthAttachment:
    return EpochGroundTruthAttachment(
        client_id=record.source_host.strip(),
        epoch=epoch_of_record(record, epoch_seconds),
        ground_truth=edge_iiotset_ground_truth(record.binary_label, record.attack_type),
    )


def separate_benign_and_evaluation(
    records: tuple[EdgeIiotsetFlowRecord, ...],
) -> EdgeIiotsetBenignEvaluationSeparation:
    benign_records: list[EdgeIiotsetFlowRecord] = []
    evaluation_records: list[EdgeIiotsetFlowRecord] = []
    discrepancies: list[EdgeIiotsetGroundTruthDiscrepancy] = []
    for record in records:
        ground_truth = edge_iiotset_ground_truth(record.binary_label, record.attack_type)
        if ground_truth.is_ambiguous:
            discrepancies.append(
                EdgeIiotsetGroundTruthDiscrepancy(record=record, ground_truth=ground_truth)
            )
            evaluation_records.append(record)
            continue
        if ground_truth.classification is GroundTruthClass.BENIGN:
            benign_records.append(record)
            continue
        evaluation_records.append(record)
    return EdgeIiotsetBenignEvaluationSeparation(
        benign_records=tuple(benign_records),
        evaluation_records=tuple(evaluation_records),
        discrepancies=tuple(discrepancies),
        experiment_state=ExperimentState.READY,
    )


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
    if len(eligible_ids) < minimum_eligible_client_count:
        return SecondaryClientSelection(
            selected_client_ids=(),
            eligible_client_ids=eligible_ids,
            eligibility=tuple(eligibility),
            claim_state=ClaimState.NOT_TESTED,
        )
    if len(eligible_ids) < target_client_count:
        return SecondaryClientSelection(
            selected_client_ids=eligible_ids,
            eligible_client_ids=eligible_ids,
            eligibility=tuple(eligibility),
            claim_state=ClaimState.SUPPORTED,
        )
    return SecondaryClientSelection(
        selected_client_ids=eligible_ids[:target_client_count],
        eligible_client_ids=eligible_ids,
        eligibility=tuple(eligibility),
        claim_state=ClaimState.SUPPORTED,
    )


def epoch_event_count_records(
    records: tuple[EdgeIiotsetFlowRecord, ...],
) -> tuple[EdgeIiotsetFlowRecord, ...]:
    return tuple(
        record for record in records if record_enters_epoch_event_count(record.protocol_group)
    )
