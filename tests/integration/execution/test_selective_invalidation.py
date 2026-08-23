from pathlib import Path

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import (
    DatasetName,
    DownstreamArtifactKind,
    OverwritePolicy,
    PreprocessingLayer,
)
from fedcampaign_emhi.execution.preprocess import (
    execute_preprocess,
    nearest_reconstruction_layer,
    preprocess_must_not_regenerate,
    requested_datasets,
)


def test_requested_datasets_cover_all_or_one() -> None:
    assert requested_datasets(None) == (
        DatasetName.TON_IOT_NETWORK,
        DatasetName.EDGE_IIOTSET,
    )
    assert requested_datasets(DatasetName.EDGE_IIOTSET) == (DatasetName.EDGE_IIOTSET,)


def test_nearest_reconstruction_starts_at_first_invalid_layer() -> None:
    assert nearest_reconstruction_layer(
        (True, True, False, True, True), OverwritePolicy.REUSE_COMPATIBLE
    ) is (PreprocessingLayer.SPLITS)
    assert (
        nearest_reconstruction_layer(
            (True, True, True, True, True), OverwritePolicy.REUSE_COMPATIBLE
        )
        is None
    )
    assert nearest_reconstruction_layer(
        (True, True, True, True, True), OverwritePolicy.OVERWRITE
    ) is (PreprocessingLayer.INVENTORY)


def test_reuse_overwrite_and_identity_change(tmp_path: Path) -> None:
    loaded = load_production_configuration()
    raw = tmp_path / "data" / "raw" / "ton_iot_network"
    raw.mkdir(parents=True)
    (raw / "Network_dataset_1.csv").write_text(
        "ts,src_ip,proto,service,label,type\n1,10.0.0.1,tcp,http,0,normal\n"
    )
    first = execute_preprocess(
        loaded, tmp_path, DatasetName.TON_IOT_NETWORK, OverwritePolicy.REUSE_COMPATIBLE
    )
    assert first.requested_datasets == (DatasetName.TON_IOT_NETWORK,)
    assert all(decision.reconstructed for decision in first.decisions)
    assert all(not decision.invalidated_descendant_ids for decision in first.decisions)
    second = execute_preprocess(
        loaded, tmp_path, DatasetName.TON_IOT_NETWORK, OverwritePolicy.REUSE_COMPATIBLE
    )
    assert all(decision.reused for decision in second.decisions)
    assert second.reconstruct_from == ((DatasetName.TON_IOT_NETWORK, None),)
    registry = (
        tmp_path
        / "outputs"
        / "preprocessing"
        / "TON_IoT_Network"
        / f"{PreprocessingLayer.CAMPAIGN_REGISTRY.value}.json"
    )
    registry.unlink()
    third = execute_preprocess(
        loaded, tmp_path, DatasetName.TON_IOT_NETWORK, OverwritePolicy.REUSE_COMPATIBLE
    )
    assert third.reconstruct_from == (
        (DatasetName.TON_IOT_NETWORK, PreprocessingLayer.CAMPAIGN_REGISTRY),
    )
    reused_layers = tuple(decision.layer for decision in third.decisions if decision.reused)
    rebuilt_layers = tuple(decision.layer for decision in third.decisions if decision.reconstructed)
    assert PreprocessingLayer.INVENTORY in reused_layers
    assert PreprocessingLayer.CAMPAIGN_REGISTRY in rebuilt_layers
    overwrite = execute_preprocess(
        loaded, tmp_path, DatasetName.TON_IOT_NETWORK, OverwritePolicy.OVERWRITE
    )
    assert all(decision.reconstructed for decision in overwrite.decisions)
    assert all(not decision.invalidated_descendant_ids for decision in overwrite.decisions)
    (raw / "Network_dataset_1.csv").write_text(
        "ts,src_ip,proto,service,label,type\n2,10.0.0.2,tcp,http,0,normal\n"
    )
    changed = execute_preprocess(
        loaded, tmp_path, DatasetName.TON_IOT_NETWORK, OverwritePolicy.REUSE_COMPATIBLE
    )
    invalidated = tuple(
        artifact_id
        for decision in changed.decisions
        for artifact_id in decision.invalidated_descendant_ids
    )
    assert invalidated
    assert any("detector" in artifact_id for artifact_id in invalidated)
    forbidden = preprocess_must_not_regenerate()
    assert DownstreamArtifactKind.DETECTOR_MODELS in forbidden
    assert DownstreamArtifactKind.REPORTS in forbidden
