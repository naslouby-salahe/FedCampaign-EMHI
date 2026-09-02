import inspect
from pathlib import Path

from fedcampaign_emhi.datasets.edge_iiotset.canonicalization import normalize_event_type
from fedcampaign_emhi.datasets.edge_iiotset.loading import iter_edge_iiotset_csv_entries
from fedcampaign_emhi.datasets.edge_iiotset.validation import select_secondary_clients
from fedcampaign_emhi.domain.enums import SupportState
from fedcampaign_emhi.domain.types import ExcludedRecord


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
    records = tuple(
        entry
        for entry in iter_edge_iiotset_csv_entries(csv_path)
        if not isinstance(entry, ExcludedRecord)
    )
    assert normalize_event_type(records[0].protocol_group) == "PROTOCOL::TCP"
    selected = select_secondary_clients(records, 60, 2, 2, 12, 2)
    assert selected.support_state is SupportState.SUPPORTED
    assert selected.selected_client_ids == ("192.168.1.10", "192.168.1.11")
    untested = select_secondary_clients(records, 60, 2, 2, 12, 6)
    assert untested.support_state is SupportState.NOT_TESTED
    assert "primary" not in inspect.signature(select_secondary_clients).parameters
