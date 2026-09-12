import json
from pathlib import Path

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import DatasetName, OverwritePolicy, RecordExclusionReason
from fedcampaign_emhi.execution.preprocessing import execute_preprocess


def test_ton_iot_exclusions_are_classified_by_deterministic_reason_code(tmp_path: Path) -> None:
    loaded = load_production_configuration()
    raw = tmp_path / "data/raw/TON-IoT/Processed_datasets/Processed_Network_dataset"
    raw.mkdir(parents=True)
    (raw / "Network_dataset_1.csv").write_text(
        "ts,src_ip,proto,service,label,type\n"
        "1,10.0.0.1,tcp,http,0,normal\n"
        "not-a-time,10.0.0.1,tcp,http,0,normal\n"
        "2,-,tcp,http,0,normal\n"
        "3,10.0.0.1,tcp,http,not-a-label,normal\n"
        "4,10.0.0.1,tcp,http,0,\n"
    )
    execute_preprocess(
        loaded, tmp_path, DatasetName.TON_IOT_NETWORK, OverwritePolicy.REUSE_COMPATIBLE
    )

    prepared_path = tmp_path / "outputs" / "preprocessing" / "prepared" / "TON_IoT_Network.json"
    payload = json.loads(prepared_path.read_text(encoding="utf-8"))

    assert payload["excluded_record_count"] == 4
    reasons = {
        entry["reason"]: entry["record_count"] for entry in payload["excluded_record_reason_counts"]
    }
    assert reasons[RecordExclusionReason.UNPARSEABLE_TIMESTAMP.value] == 1
    assert reasons[RecordExclusionReason.UNUSABLE_HOST_IDENTITY.value] == 1
    assert reasons[RecordExclusionReason.STRUCTURALLY_INVALID_EVENT.value] == 1
    assert reasons[RecordExclusionReason.MISSING_FIELD_VALUE.value] == 1
