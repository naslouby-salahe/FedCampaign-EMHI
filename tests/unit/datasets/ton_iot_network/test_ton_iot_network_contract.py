import hashlib
import inspect
from pathlib import Path

import pytest

from fedcampaign_emhi.datasets.ton_iot_network.canonicalization import (
    UNKNOWN_PROTOCOL_TOKEN,
    UNKNOWN_SERVICE_TOKEN,
    event_type_hash_bucket,
    normalize_event_type,
)
from fedcampaign_emhi.datasets.ton_iot_network.ground_truth import ton_iot_network_ground_truth
from fedcampaign_emhi.datasets.ton_iot_network.loading import validate_ton_iot_network_csv_schema
from fedcampaign_emhi.datasets.ton_iot_network.validation import (
    schema_is_executable,
)
from fedcampaign_emhi.domain.enums import GroundTruthClass


def test_documented_columns_are_required() -> None:
    observed = ("ts", "src_ip", "proto", "service", "label", "type")
    assert schema_is_executable(observed)
    assert not schema_is_executable(("ts", "src_ip"))


def test_loader_preflight_rejects_an_unexecutable_release(tmp_path: Path) -> None:
    path = tmp_path / "invalid.csv"
    path.write_text("src_ip,label\n10.0.0.1,0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="required TON_IoT Network columns"):
        validate_ton_iot_network_csv_schema(path)


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
