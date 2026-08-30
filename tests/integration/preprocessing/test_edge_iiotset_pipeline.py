import inspect
from pathlib import Path

from fedcampaign_emhi.datasets.edge_iiotset.loading import load_edge_iiotset_csv
from fedcampaign_emhi.datasets.edge_iiotset.normalization import normalize_event_type
from fedcampaign_emhi.datasets.edge_iiotset.validation import (
    epoch_event_count_records,
    select_secondary_clients,
    separate_benign_and_evaluation,
)
from fedcampaign_emhi.datasets.inventory import (
    adapter_producer_commit,
    build_edge_iiotset_release_identity,
    inventory_raw_directory,
)
from fedcampaign_emhi.domain.enums import ClaimState, GroundTruthClass


def test_secondary_adapter_pipeline(tmp_path: Path) -> None:
    raw = tmp_path / "edge_iiotset"
    raw.mkdir()
    csv_path = raw / "ML-EdgeIIoT-dataset.csv"
    csv_path.write_text(
        "frame.time,ip.src_host,ip.dst_host,Attack_label,Attack_type,tcp.flags,arp.opcode\n"
        "10,192.168.1.10,192.168.1.1,0,Normal,2,0\n"
        "70,192.168.1.10,192.168.1.1,0,Normal,2,0\n"
        "10,192.168.1.11,192.168.1.1,0,Normal,2,0\n"
        "70,192.168.1.11,192.168.1.1,0,Normal,2,0\n"
        "130,192.168.1.10,192.168.1.1,1,DDoS_UDP,0,0\n"
        "11,192.168.1.12,192.168.1.1,0,MITM,0,0\n",
        encoding="utf-8",
    )
    files = inventory_raw_directory(raw, tmp_path)
    identity = build_edge_iiotset_release_identity(
        files,
        files[0].sha256,
        adapter_producer_commit(Path(__file__).resolve().parents[3]),
    )
    records = load_edge_iiotset_csv(csv_path)
    assert identity.release_persistent_identifier == "10.21227/mbc1-1h68"
    assert normalize_event_type(records[0].protocol_group) == "PROTOCOL::TCP"
    separation = separate_benign_and_evaluation(records)
    assert len(separation.benign_records) == 4
    assert separation.discrepancies[0].ground_truth.classification is GroundTruthClass.AMBIGUOUS
    counted = epoch_event_count_records(records)
    assert all(record.protocol_group != "UNKNOWN_PROTOCOL" for record in counted)
    selected = select_secondary_clients(records, 60, 2, 2, 12, 2)
    assert selected.claim_state is ClaimState.SUPPORTED
    assert selected.selected_client_ids == ("192.168.1.10", "192.168.1.11")
    untested = select_secondary_clients(records, 60, 2, 2, 12, 6)
    assert untested.claim_state is ClaimState.NOT_TESTED
    assert "primary" not in inspect.signature(select_secondary_clients).parameters
