import inspect
from pathlib import Path

import pytest

from fedcampaign_emhi.artifacts.storage import file_sha256
from fedcampaign_emhi.datasets.edge_iiotset.ground_truth import edge_iiotset_ground_truth
from fedcampaign_emhi.datasets.edge_iiotset.loading import (
    load_edge_iiotset_csv,
    load_edge_iiotset_csv_with_exclusions,
    parse_frame_time,
)
from fedcampaign_emhi.datasets.edge_iiotset.normalization import (
    UNKNOWN_PROTOCOL_GROUP,
    dominant_protocol_group_for_row,
    normalize_event_type,
    record_enters_epoch_event_count,
)
from fedcampaign_emhi.datasets.edge_iiotset.validation import (
    attach_epoch_ground_truth,
    documented_attack_type_is_expected,
    documented_identity_columns,
    documented_protocol_group_prefixes,
    epoch_event_count_records,
    observed_schema_preprocessing_state,
    schema_is_executable,
    select_secondary_clients,
    separate_benign_and_evaluation,
)
from fedcampaign_emhi.datasets.inventory import (
    adapter_producer_commit,
    build_edge_iiotset_release_identity,
    edge_iiotset_field_mapping,
    inventory_raw_directory,
)
from fedcampaign_emhi.domain.enums import ExperimentState, GroundTruthClass, SupportState
from fedcampaign_emhi.domain.types import EdgeIiotsetFlowRecord


def test_release_timestamp_format_is_parsed_deterministically() -> None:
    assert parse_frame_time("2021 11:44:10.081753000") == 1609501450.081753


def _flow(
    timestamp_seconds: float,
    source_host: str,
    binary_label: int,
    attack_type: str,
    protocol_group: str = "tcp",
) -> EdgeIiotsetFlowRecord:
    return EdgeIiotsetFlowRecord(
        timestamp_seconds=timestamp_seconds,
        source_host=source_host,
        protocol_group=protocol_group,
        binary_label=binary_label,
        attack_type=attack_type,
    )


def test_documented_columns_are_required() -> None:
    observed = ("frame.time", "ip.src_host", "Attack_label", "Attack_type")
    assert schema_is_executable(observed)
    assert not schema_is_executable(("ip.src_host",))
    mapping = edge_iiotset_field_mapping(observed)
    assert mapping == tuple((column, column) for column in observed)
    assert "ip.src_host" in documented_identity_columns()
    assert "tcp." in documented_protocol_group_prefixes()


def test_literal_column_names_are_not_normalized_to_zeek() -> None:
    mapping = edge_iiotset_field_mapping(
        ("frame.time", "ip.src_host", "Attack_label", "Attack_type", "tcp.flags")
    )
    mapped_names = tuple(pair[1] for pair in mapping)
    assert "ip.src_host" in mapped_names
    assert "src_ip" not in mapped_names
    assert "ts" not in mapped_names


def test_protocol_event_type() -> None:
    assert normalize_event_type("tcp") == "PROTOCOL::TCP"
    assert normalize_event_type("  ") == "PROTOCOL::UNKNOWN_PROTOCOL"
    assert normalize_event_type(UNKNOWN_PROTOCOL_GROUP) == "PROTOCOL::UNKNOWN_PROTOCOL"
    assert not record_enters_epoch_event_count(UNKNOWN_PROTOCOL_GROUP)
    assert record_enters_epoch_event_count("tcp")


def test_dominant_protocol_group_uses_resolvable_row_payloads() -> None:
    fields = (
        ("arp.opcode", "0"),
        ("tcp.flags", "2"),
        ("udp.port", "0.0"),
    )
    assert dominant_protocol_group_for_row(fields) == "tcp"
    empty = (("arp.opcode", "0"), ("tcp.flags", "0"))
    assert dominant_protocol_group_for_row(empty) == UNKNOWN_PROTOCOL_GROUP


def test_ground_truth_uses_attack_columns() -> None:
    signature = inspect.signature(edge_iiotset_ground_truth)
    assert tuple(signature.parameters) == ("binary_label", "attack_type")
    benign = edge_iiotset_ground_truth(0, "Normal")
    malicious = edge_iiotset_ground_truth(1, "DDoS_UDP")
    ambiguous = edge_iiotset_ground_truth(0, "DDoS_UDP")
    extra = edge_iiotset_ground_truth(1, "undocumented_variant")
    assert benign.classification is GroundTruthClass.BENIGN
    assert malicious.classification is GroundTruthClass.MALICIOUS
    assert ambiguous.is_ambiguous is True
    assert extra.classification is GroundTruthClass.MALICIOUS
    assert documented_attack_type_is_expected("MITM")
    assert not documented_attack_type_is_expected("undocumented_variant")


def test_loader_reads_fixture_csv(tmp_path: Path) -> None:
    path = tmp_path / "edge.csv"
    path.write_text(
        "frame.time,ip.src_host,Attack_label,Attack_type,tcp.flags\n"
        "100.0,192.168.1.10,0,Normal,2\n",
        encoding="utf-8",
    )
    records = load_edge_iiotset_csv(path)
    assert records[0].source_host == "192.168.1.10"
    assert records[0].protocol_group == "tcp"


def test_loader_excludes_unusable_and_unparseable_rows(tmp_path: Path) -> None:
    path = tmp_path / "edge.csv"
    path.write_text(
        "frame.time,ip.src_host,Attack_label,Attack_type,tcp.flags\n"
        "100.0,192.168.1.10,0,Normal,2\n"
        "not-a-time,192.168.1.11,0,Normal,2\n"
        "101.0,,0,Normal,2\n"
        "2020-01-01T00:00:00,192.168.1.12,0,Normal,2\n",
        encoding="utf-8",
    )
    records, exclusions = load_edge_iiotset_csv_with_exclusions(path)
    assert len(records) == 1
    assert len(exclusions) == 3


def test_missing_required_columns_are_invalid_preprocessing(tmp_path: Path) -> None:
    path = tmp_path / "edge.csv"
    path.write_text("ip.src_host,Attack_label,Attack_type\n192.168.1.10,0,Normal\n")
    with pytest.raises(ValueError, match=r"frame\.time"):
        load_edge_iiotset_csv(path)
    assert observed_schema_preprocessing_state(("ip.src_host", "Attack_label", "Attack_type")) is (
        ExperimentState.INVALID
    )


def test_benign_evaluation_separation_and_epoch_attachment() -> None:
    records = (
        _flow(10.0, "192.168.1.10", 0, "Normal"),
        _flow(11.0, "192.168.1.10", 1, "DDoS_UDP"),
        _flow(12.0, "192.168.1.10", 0, "MITM"),
        _flow(13.0, "192.168.1.10", 1, "undocumented_variant", UNKNOWN_PROTOCOL_GROUP),
    )
    separation = separate_benign_and_evaluation(records)
    assert len(separation.benign_records) == 1
    assert len(separation.discrepancies) == 1
    assert separation.discrepancies[0].ground_truth.classification is GroundTruthClass.AMBIGUOUS
    counted = epoch_event_count_records(records)
    assert len(counted) == 3
    first = attach_epoch_ground_truth(records[0], 60)
    second = attach_epoch_ground_truth(_flow(60.0, "192.168.1.10", 1, "XSS"), 60)
    assert first.epoch.index == 0
    assert second.epoch.index == 1


def test_secondary_client_selection_uses_all_eligible_between_minimum_and_target() -> None:
    records = (
        _flow(10.0, "192.168.1.12", 0, "Normal"),
        _flow(70.0, "192.168.1.12", 0, "Normal"),
        _flow(10.0, "192.168.1.10", 0, "Normal"),
        _flow(70.0, "192.168.1.10", 0, "Normal"),
        _flow(130.0, "192.168.1.10", 0, "Normal"),
        _flow(10.0, "192.168.1.11", 0, "Normal"),
        _flow(70.0, "192.168.1.11", 0, "Normal"),
        _flow(10.0, "192.168.1.99", 1, "Backdoor"),
        _flow(70.0, "192.168.1.99", 1, "Backdoor"),
    )
    mid = select_secondary_clients(records, 60, 2, 2, 12, 2)
    assert mid.support_state is SupportState.SUPPORTED
    assert mid.selected_client_ids == ("192.168.1.10", "192.168.1.11", "192.168.1.12")
    targeted = select_secondary_clients(records, 60, 2, 2, 2, 2)
    assert targeted.selected_client_ids == ("192.168.1.10", "192.168.1.11")
    untested = select_secondary_clients(records, 60, 2, 2, 12, 6)
    assert untested.support_state is SupportState.NOT_TESTED
    assert untested.selected_client_ids == ()
    assert tuple(inspect.signature(select_secondary_clients).parameters) == (
        "records",
        "epoch_seconds",
        "minimum_benign_event_records",
        "minimum_nonempty_benign_epochs",
        "target_client_count",
        "minimum_eligible_client_count",
    )


def test_release_identity_records_doi(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    payload = raw / "ML-EdgeIIoT-dataset.csv"
    payload.write_text(
        "frame.time,ip.src_host,Attack_label,Attack_type,tcp.flags\n1,192.168.1.10,0,Normal,2\n"
    )
    files = inventory_raw_directory(raw, tmp_path)
    identity = build_edge_iiotset_release_identity(
        files,
        files[0].sha256,
        adapter_producer_commit(Path(__file__).resolve().parents[4]),
    )
    assert identity.release_persistent_identifier == "10.21227/mbc1-1h68"
    assert identity.dataset_version_label == "Edge-IIoTset"
    assert identity.files[0].sha256 == file_sha256(payload)
    assert identity.published_external_checksum_cross_checks == ()
