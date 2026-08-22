from pathlib import Path

from fedcampaign_emhi.datasets.edge_iiotset.canonicalization import canonical_event_type
from fedcampaign_emhi.datasets.edge_iiotset.ground_truth import edge_iiotset_ground_truth
from fedcampaign_emhi.datasets.edge_iiotset.loading import load_edge_iiotset_csv
from fedcampaign_emhi.datasets.edge_iiotset.validation import schema_is_executable
from fedcampaign_emhi.domain.enums import GroundTruthClass


def test_documented_columns_are_required() -> None:
    assert schema_is_executable(("frame.time", "ip.src_host", "Attack_label", "Attack_type"))
    assert not schema_is_executable(("ip.src_host",))


def test_protocol_event_type() -> None:
    assert canonical_event_type("tcp") == "PROTOCOL::TCP"
    assert canonical_event_type("  ") == "PROTOCOL::UNKNOWN_PROTOCOL"


def test_ground_truth_uses_attack_columns() -> None:
    benign = edge_iiotset_ground_truth(0, "Normal")
    malicious = edge_iiotset_ground_truth(1, "DDoS_UDP")
    ambiguous = edge_iiotset_ground_truth(0, "DDoS_UDP")
    assert benign.classification is GroundTruthClass.BENIGN
    assert malicious.classification is GroundTruthClass.MALICIOUS
    assert ambiguous.is_ambiguous is True


def test_loader_reads_fixture_csv(tmp_path: Path) -> None:
    path = tmp_path / "edge.csv"
    path.write_text(
        "frame.time,ip.src_host,Attack_label,Attack_type,tcp.flags\n"
        "100.0,192.168.1.10,0,Normal,0\n",
        encoding="utf-8",
    )
    records = load_edge_iiotset_csv(path)
    assert records[0].source_host == "192.168.1.10"
    assert records[0].protocol_group == "tcp"
