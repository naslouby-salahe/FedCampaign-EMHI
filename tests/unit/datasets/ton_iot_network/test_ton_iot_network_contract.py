import hashlib
import inspect
from pathlib import Path

import pytest

from fedcampaign_emhi.artifacts.storage import file_sha256
from fedcampaign_emhi.datasets.inventory import (
    adapter_producer_commit,
    build_ton_iot_network_release_identity,
    inventory_raw_directory,
    ton_iot_network_field_mapping,
)
from fedcampaign_emhi.datasets.ton_iot_network.ground_truth import ton_iot_network_ground_truth
from fedcampaign_emhi.datasets.ton_iot_network.loading import (
    load_ton_iot_network_csv,
    load_ton_iot_network_csv_with_exclusions,
)
from fedcampaign_emhi.datasets.ton_iot_network.normalization import (
    UNKNOWN_PROTOCOL_TOKEN,
    UNKNOWN_SERVICE_TOKEN,
    event_type_hash_bucket,
    normalize_client_id,
    normalize_event_type,
)
from fedcampaign_emhi.datasets.ton_iot_network.validation import (
    attach_epoch_ground_truth,
    client_identity_is_ambiguous,
    documented_attack_type_is_expected,
    documented_zeek_core_columns,
    observed_column_matches_documented_protocol_extension,
    observed_schema_preprocessing_state,
    schema_is_executable,
    select_primary_clients,
    separate_benign_and_evaluation,
)
from fedcampaign_emhi.domain.enums import (
    ClaimState,
    ExperimentState,
    GroundTruthClass,
    RecordExclusionReason,
)
from fedcampaign_emhi.domain.types import FileInventoryEntry, TonIotNetworkFlowRecord


def _flow(
    timestamp_seconds: float,
    source_ip: str,
    binary_label: int,
    attack_type: str,
) -> TonIotNetworkFlowRecord:
    return TonIotNetworkFlowRecord(
        timestamp_seconds=timestamp_seconds,
        source_ip=source_ip,
        protocol_token="TCP",
        service_token="HTTP",
        binary_label=binary_label,
        attack_type=attack_type,
    )


def test_documented_columns_are_required() -> None:
    observed = ("ts", "src_ip", "proto", "service", "label", "type")
    assert schema_is_executable(observed)
    assert not schema_is_executable(("ts", "src_ip"))
    mapping = ton_iot_network_field_mapping(observed)
    assert mapping == tuple((column, column) for column in observed)


def test_missing_timestamp_is_blocking() -> None:
    with pytest.raises(ValueError, match="ts"):
        ton_iot_network_field_mapping(("src_ip", "proto", "service", "label", "type"))


def test_documented_zeek_fields_are_expectations_not_execution_constants() -> None:
    extra = (
        "ts",
        "src_ip",
        "proto",
        "service",
        "label",
        "type",
        "dns_query",
        "ssl_version",
        "http_method",
        "weird_name",
    )
    assert schema_is_executable(extra)
    assert observed_column_matches_documented_protocol_extension("dns_query")
    assert "src_port" in documented_zeek_core_columns()
    assert documented_attack_type_is_expected("ddos")
    assert not documented_attack_type_is_expected("undocumented_variant")


def test_normalized_event_type_and_hash_are_deterministic() -> None:
    event_type = normalize_event_type(" tcp ", None)
    assert event_type == "TCP::UNKNOWN_SERVICE"
    assert normalize_event_type(None, None) == f"{UNKNOWN_PROTOCOL_TOKEN}::{UNKNOWN_SERVICE_TOKEN}"
    assert normalize_event_type("-", "-") == f"{UNKNOWN_PROTOCOL_TOKEN}::{UNKNOWN_SERVICE_TOKEN}"
    first = event_type_hash_bucket(event_type, 64)
    second = event_type_hash_bucket(event_type, 64)
    assert first == second
    digest = hashlib.sha256(event_type.encode("utf-8")).digest()
    assert first == int.from_bytes(digest[:8], "big") % 64
    assert 0 <= first < 64


def test_ground_truth_uses_only_label_and_type() -> None:
    signature = inspect.signature(ton_iot_network_ground_truth)
    assert tuple(signature.parameters) == ("binary_label", "attack_type")
    benign = ton_iot_network_ground_truth(0, "normal")
    malicious = ton_iot_network_ground_truth(1, "ddos")
    ambiguous = ton_iot_network_ground_truth(0, "ddos")
    reverse_ambiguous = ton_iot_network_ground_truth(1, "normal")
    extra = ton_iot_network_ground_truth(1, "undocumented_variant")
    assert benign.classification is GroundTruthClass.BENIGN
    assert malicious.classification is GroundTruthClass.MALICIOUS
    assert ambiguous.is_ambiguous is True
    assert ambiguous.classification is GroundTruthClass.AMBIGUOUS
    assert reverse_ambiguous.is_ambiguous is True
    assert extra.classification is GroundTruthClass.MALICIOUS
    assert extra.is_ambiguous is False


def test_loader_reads_fixture_csv(tmp_path: Path) -> None:
    path = tmp_path / "ton.csv"
    path.write_text(
        "ts,src_ip,proto,service,label,type\n100.5,10.0.0.1,tcp,http,0,normal\n",
        encoding="utf-8",
    )
    records = load_ton_iot_network_csv(path)
    assert len(records) == 1
    assert records[0].source_ip == "10.0.0.1"
    assert records[0].binary_label == 0


def test_loader_strips_bom_and_excludes_unusable_rows(tmp_path: Path) -> None:
    path = tmp_path / "ton_bom.csv"
    path.write_bytes(
        b"\xef\xbb\xbfts,src_ip,proto,service,label,type\n"
        b"10.0,10.0.0.1,tcp,http,0,normal\n"
        b"not-a-ts,10.0.0.2,tcp,http,0,normal\n"
        b"11.0,-,tcp,http,0,normal\n"
        b"12.0,,tcp,http,0,normal\n"
        b"13.0,10.0.0.3,tcp,http,bad,normal\n"
    )
    records, exclusions = load_ton_iot_network_csv_with_exclusions(path)
    assert len(records) == 1
    assert records[0].source_ip == "10.0.0.1"
    reasons = tuple(exclusion.reason for exclusion in exclusions)
    assert RecordExclusionReason.UNPARSEABLE_TIMESTAMP in reasons
    assert RecordExclusionReason.UNUSABLE_HOST_IDENTITY in reasons
    assert RecordExclusionReason.STRUCTURALLY_INVALID_EVENT in reasons


def test_missing_ts_column_blocks_loading(tmp_path: Path) -> None:
    path = tmp_path / "train_test_network.csv"
    path.write_text(
        "src_ip,proto,service,label,type\n10.0.0.1,tcp,http,0,normal\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="ts"):
        load_ton_iot_network_csv(path)
    assert observed_schema_preprocessing_state(("src_ip", "proto", "service", "label", "type")) is (
        ExperimentState.INVALID
    )


def test_benign_evaluation_separation_and_discrepancy_manifest() -> None:
    records = (
        _flow(10.0, "10.0.0.1", 0, "normal"),
        _flow(11.0, "10.0.0.1", 1, "ddos"),
        _flow(12.0, "10.0.0.1", 0, "ddos"),
        _flow(13.0, "10.0.0.1", 1, "undocumented_variant"),
    )
    separation = separate_benign_and_evaluation(records)
    assert len(separation.benign_records) == 1
    assert len(separation.evaluation_records) == 3
    assert len(separation.discrepancies) == 1
    assert separation.discrepancies[0].ground_truth.classification is GroundTruthClass.AMBIGUOUS
    assert separation.discrepancies[0].ground_truth.classification is not GroundTruthClass.MALICIOUS
    assert (
        observed_schema_preprocessing_state(("ts", "src_ip", "proto", "service", "label", "type"))
        is ExperimentState.READY
    )


def test_epoch_ground_truth_marks_only_containing_epoch() -> None:
    first = attach_epoch_ground_truth(_flow(59.9, "10.0.0.1", 1, "scanning"), 60)
    second = attach_epoch_ground_truth(_flow(60.0, "10.0.0.1", 0, "normal"), 60)
    assert first.epoch.index == 0
    assert second.epoch.index == 1
    assert first.ground_truth.classification is GroundTruthClass.MALICIOUS
    assert second.ground_truth.classification is GroundTruthClass.BENIGN
    assert first.epoch.index != second.epoch.index


def test_primary_client_selection_ranks_ties_and_rejects_undersized_federation() -> None:
    records = (
        _flow(10.0, "10.0.0.2", 0, "normal"),
        _flow(70.0, "10.0.0.2", 0, "normal"),
        _flow(10.0, "10.0.0.1", 0, "normal"),
        _flow(70.0, "10.0.0.1", 0, "normal"),
        _flow(10.0, "10.0.0.3", 0, "normal"),
        _flow(70.0, "10.0.0.3", 0, "normal"),
        _flow(10.0, "10.0.0.4", 0, "normal"),
        _flow(130.0, "10.0.0.2", 0, "normal"),
        _flow(10.0, "10.0.0.9", 1, "ddos"),
        _flow(70.0, "10.0.0.9", 1, "ddos"),
        _flow(10.0, "-", 0, "normal"),
        _flow(70.0, "-", 0, "normal"),
    )
    selected = select_primary_clients(records, 60, 2, 2, 3)
    assert selected.claim_state is ClaimState.SUPPORTED
    assert selected.selected_client_ids == ("10.0.0.2", "10.0.0.1", "10.0.0.3")
    assert "10.0.0.9" not in selected.eligible_client_ids
    assert "-" not in selected.eligible_client_ids
    undersized = select_primary_clients(records, 60, 2, 2, 8)
    assert undersized.claim_state is ClaimState.NOT_TESTED
    assert undersized.selected_client_ids == ()
    assert len(undersized.eligible_client_ids) == 3
    assert client_identity_is_ambiguous("-")
    assert normalize_client_id(" 10.0.0.1 ") == "10.0.0.1"


def test_release_identity_uses_local_sha256_and_adapter_fingerprint(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    payload = raw / "Network_dataset_1.csv"
    payload.write_text("ts,src_ip,proto,service,label,type\n1,10.0.0.1,tcp,http,0,normal\n")
    files = inventory_raw_directory(raw, tmp_path)
    assert files[0].sha256 == file_sha256(payload)
    assert files[0].byte_count == payload.stat().st_size
    identity = build_ton_iot_network_release_identity(
        files,
        files[0].sha256,
        adapter_producer_commit(Path(__file__).resolve().parents[4]),
    )
    assert identity.release_persistent_identifier.startswith("IEEE DataPort")
    assert identity.dataset_version_label == "Network flow variant"
    assert identity.published_external_checksum_cross_checks == ()
    assert len(identity.adapter_material_code_fingerprint) == 64
    reconstructed = FileInventoryEntry(
        relative_path=files[0].relative_path,
        sha256=files[0].sha256,
        byte_count=files[0].byte_count,
    )
    assert reconstructed.sha256 == identity.files[0].sha256
