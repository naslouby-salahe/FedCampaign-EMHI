import hashlib
from pathlib import Path

from fedcampaign_emhi.datasets.partitions import epoch_index
from fedcampaign_emhi.datasets.ton_iot_network.canonicalization import (
    ZEEK_MISSING_FIELD_TOKEN,
    canonical_client_id,
)
from fedcampaign_emhi.datasets.ton_iot_network.ground_truth import ton_iot_network_ground_truth
from fedcampaign_emhi.domain.enums import ClaimState, ExperimentState, GroundTruthClass
from fedcampaign_emhi.domain.types import (
    BenignEvaluationSeparation,
    CanonicalEventToken,
    ClientBenignTally,
    ClientCount,
    ClientEligibilityRecord,
    ClientId,
    ConfigurationDigest,
    EpochGroundTruthAttachment,
    EpochIndex,
    EpochIndexValue,
    EpochSeconds,
    GroundTruthDiscrepancy,
    PositiveEpochCount,
    PrimaryClientSelection,
    RecordCount,
    TonIotNetworkFlowRecord,
)

REQUIRED_TON_IOT_NETWORK_COLUMNS = (
    "ts",
    "src_ip",
    "proto",
    "service",
    "label",
    "type",
)
DOCUMENTED_ATTACK_TYPE_EXPECTATIONS = (
    "normal",
    "backdoor",
    "dos",
    "ddos",
    "injection",
    "mitm",
    "password",
    "ransomware",
    "scanning",
    "xss",
)
DOCUMENTED_ZEEK_CORE_COLUMNS = (
    "ts",
    "src_ip",
    "src_port",
    "dst_ip",
    "dst_port",
    "proto",
    "service",
    "duration",
    "src_bytes",
    "dst_bytes",
    "conn_state",
    "missed_bytes",
    "src_pkts",
    "src_ip_bytes",
    "dst_pkts",
    "dst_ip_bytes",
)
DOCUMENTED_PROTOCOL_EXTENSION_PREFIXES = (
    "dns_",
    "ssl_",
    "http_",
    "weird_",
)


def missing_required_columns(
    observed_columns: tuple[CanonicalEventToken, ...],
) -> tuple[CanonicalEventToken, ...]:
    observed = {column.strip() for column in observed_columns}
    return tuple(column for column in REQUIRED_TON_IOT_NETWORK_COLUMNS if column not in observed)


def schema_is_executable(observed_columns: tuple[CanonicalEventToken, ...]) -> bool:
    return not missing_required_columns(observed_columns)


def adapter_material_code_fingerprint() -> ConfigurationDigest:
    digest = hashlib.sha256()
    directory = Path(__file__).resolve().parent
    for name in ("canonicalization.py", "loading.py", "ground_truth.py", "validation.py"):
        digest.update((directory / name).read_bytes())
    return digest.hexdigest()


def epoch_of_record(record: TonIotNetworkFlowRecord, epoch_seconds: EpochSeconds) -> EpochIndex:
    return epoch_index(record.timestamp_seconds, epoch_seconds)


def documented_attack_type_is_expected(attack_type: CanonicalEventToken) -> bool:
    return attack_type.strip().lower() in DOCUMENTED_ATTACK_TYPE_EXPECTATIONS


def documented_zeek_core_columns() -> tuple[CanonicalEventToken, ...]:
    return DOCUMENTED_ZEEK_CORE_COLUMNS


def observed_column_matches_documented_protocol_extension(
    column: CanonicalEventToken,
) -> bool:
    stripped = column.strip()
    return any(stripped.startswith(prefix) for prefix in DOCUMENTED_PROTOCOL_EXTENSION_PREFIXES)


def record_is_benign(record: TonIotNetworkFlowRecord) -> bool:
    return (
        ton_iot_network_ground_truth(record.binary_label, record.attack_type).classification
        is GroundTruthClass.BENIGN
    )


def record_identity_is_usable(source_ip: ClientId) -> bool:
    return bool(source_ip.strip()) and not client_identity_is_ambiguous(source_ip)


def client_identity_is_ambiguous(source_ip: ClientId) -> bool:
    canonical = canonical_client_id(source_ip)
    return (not canonical) or canonical == ZEEK_MISSING_FIELD_TOKEN


def observed_schema_preprocessing_state(
    observed_columns: tuple[CanonicalEventToken, ...],
) -> ExperimentState:
    if schema_is_executable(observed_columns):
        return ExperimentState.READY
    return ExperimentState.INVALID


def attach_epoch_ground_truth(
    record: TonIotNetworkFlowRecord, epoch_seconds: EpochSeconds
) -> EpochGroundTruthAttachment:
    return EpochGroundTruthAttachment(
        client_id=canonical_client_id(record.source_ip),
        epoch=epoch_of_record(record, epoch_seconds),
        ground_truth=ton_iot_network_ground_truth(record.binary_label, record.attack_type),
    )


def separate_benign_and_evaluation(
    records: tuple[TonIotNetworkFlowRecord, ...],
) -> BenignEvaluationSeparation:
    benign_records: list[TonIotNetworkFlowRecord] = []
    evaluation_records: list[TonIotNetworkFlowRecord] = []
    discrepancies: list[GroundTruthDiscrepancy] = []
    for record in records:
        ground_truth = ton_iot_network_ground_truth(record.binary_label, record.attack_type)
        if ground_truth.is_ambiguous:
            discrepancies.append(GroundTruthDiscrepancy(record=record, ground_truth=ground_truth))
            evaluation_records.append(record)
            continue
        if ground_truth.classification is GroundTruthClass.BENIGN:
            benign_records.append(record)
            continue
        evaluation_records.append(record)
    return BenignEvaluationSeparation(
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


def select_primary_clients(
    records: tuple[TonIotNetworkFlowRecord, ...],
    epoch_seconds: EpochSeconds,
    minimum_benign_event_records: RecordCount,
    minimum_nonempty_benign_epochs: PositiveEpochCount,
    target_client_count: ClientCount,
) -> PrimaryClientSelection:
    tallies: tuple[ClientBenignTally, ...] = ()
    for record in records:
        if not record_identity_is_usable(record.source_ip):
            continue
        if not record_is_benign(record):
            continue
        client_id = canonical_client_id(record.source_ip)
        epoch = epoch_index(record.timestamp_seconds, epoch_seconds).index
        tallies = _add_benign_event(tallies, client_id, epoch)
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
            claim_state=ClaimState.NOT_TESTED,
        )
    return PrimaryClientSelection(
        selected_client_ids=eligible_ids[:target_client_count],
        eligible_client_ids=eligible_ids,
        eligibility=tuple(eligibility),
        claim_state=ClaimState.SUPPORTED,
    )
