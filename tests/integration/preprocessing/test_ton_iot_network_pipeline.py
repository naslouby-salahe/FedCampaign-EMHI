import inspect
from pathlib import Path

from fedcampaign_emhi.datasets.inventory import (
    adapter_producer_commit,
    build_ton_iot_network_release_identity,
    inventory_raw_directory,
)
from fedcampaign_emhi.datasets.ton_iot_network.loading import load_ton_iot_network_csv
from fedcampaign_emhi.datasets.ton_iot_network.validation import (
    attach_epoch_ground_truth,
    observed_schema_preprocessing_state,
    select_primary_clients,
    separate_benign_and_evaluation,
)
from fedcampaign_emhi.domain.enums import ExperimentState, GroundTruthClass, SupportState


def test_adapter_pipeline_inventories_selects_and_separates(tmp_path: Path) -> None:
    raw = tmp_path / "ton_iot_network"
    raw.mkdir()
    csv_path = raw / "Network_dataset_1.csv"
    csv_path.write_text(
        "ts,src_ip,src_port,dst_ip,proto,service,label,type,dns_query\n"
        "10,10.0.0.1,80,10.0.0.9,tcp,http,0,normal,example\n"
        "70,10.0.0.1,80,10.0.0.9,tcp,http,0,normal,example\n"
        "10,10.0.0.2,80,10.0.0.9,tcp,-,0,normal,-\n"
        "70,10.0.0.2,80,10.0.0.9,udp,dns,0,normal,example\n"
        "130,10.0.0.2,80,10.0.0.9,tcp,http,1,ddos,example\n"
        "11,10.0.0.3,80,10.0.0.9,tcp,http,0,ddos,example\n",
        encoding="utf-8",
    )
    files = inventory_raw_directory(raw, tmp_path)
    identity = build_ton_iot_network_release_identity(
        files,
        files[0].sha256,
        adapter_producer_commit(Path(__file__).resolve().parents[3]),
    )
    records = load_ton_iot_network_csv(csv_path)
    assert identity.dataset_version_label == "Network flow variant"
    assert identity.files[0].relative_path.endswith("Network_dataset_1.csv")
    assert observed_schema_preprocessing_state(
        tuple(csv_path.read_text().splitlines()[0].split(","))
    ) is (ExperimentState.READY)
    separation = separate_benign_and_evaluation(records)
    assert len(separation.benign_records) == 4
    assert len(separation.discrepancies) == 1
    assert separation.discrepancies[0].ground_truth.classification is GroundTruthClass.AMBIGUOUS
    selected = select_primary_clients(records, 60, 2, 2, 2)
    assert selected.support_state is SupportState.SUPPORTED
    assert selected.selected_client_ids == ("10.0.0.1", "10.0.0.2")
    undersized = select_primary_clients(records, 60, 2, 2, 5)
    assert undersized.support_state is SupportState.NOT_TESTED
    assert undersized.selected_client_ids == ()
    attachment = attach_epoch_ground_truth(records[4], 60)
    assert attachment.epoch.index == 2
    assert attachment.ground_truth.classification is GroundTruthClass.MALICIOUS
    assert tuple(inspect.signature(select_primary_clients).parameters) == (
        "records",
        "epoch_seconds",
        "minimum_benign_event_records",
        "minimum_nonempty_benign_epochs",
        "target_client_count",
    )
