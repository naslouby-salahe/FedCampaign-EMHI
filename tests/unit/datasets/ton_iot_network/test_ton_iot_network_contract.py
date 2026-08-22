from pathlib import Path

from fedcampaign_emhi.datasets.ton_iot_network.canonicalization import (
    canonical_event_type,
    event_type_hash_bucket,
)
from fedcampaign_emhi.datasets.ton_iot_network.ground_truth import ton_iot_network_ground_truth
from fedcampaign_emhi.datasets.ton_iot_network.loading import load_ton_iot_network_csv
from fedcampaign_emhi.datasets.ton_iot_network.validation import schema_is_executable
from fedcampaign_emhi.domain.enums import GroundTruthClass


def test_documented_columns_are_required() -> None:
    assert schema_is_executable(("ts", "src_ip", "proto", "service", "label", "type"))
    assert not schema_is_executable(("ts", "src_ip"))


def test_canonical_event_type_and_hash_are_deterministic() -> None:
    event_type = canonical_event_type(" tcp ", None)
    assert event_type == "TCP::UNKNOWN_SERVICE"
    first = event_type_hash_bucket(event_type, 64)
    second = event_type_hash_bucket(event_type, 64)
    assert first == second
    assert 0 <= first < 64


def test_ground_truth_uses_label_and_type() -> None:
    benign = ton_iot_network_ground_truth(0, "normal")
    malicious = ton_iot_network_ground_truth(1, "ddos")
    ambiguous = ton_iot_network_ground_truth(0, "ddos")
    assert benign.classification is GroundTruthClass.BENIGN
    assert malicious.classification is GroundTruthClass.MALICIOUS
    assert ambiguous.is_ambiguous is True


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
