from pathlib import Path

import pytest
from typer.testing import CliRunner

from fedcampaign_emhi.cli.main import application
from fedcampaign_emhi.cli.commands import preprocess as preprocess_module
from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import DatasetName, DownstreamArtifactKind, PreprocessingLayer
from fedcampaign_emhi.execution.planning import RESUME_SEQUENCE
from fedcampaign_emhi.execution.preprocess import preprocess_must_not_regenerate


def test_resume_sequence_is_fixed() -> None:
    assert RESUME_SEQUENCE[0] == "validate required existing artifacts"
    assert RESUME_SEQUENCE[-1] == "atomically publish completed outputs"


def test_preprocess_cli_selects_dataset_and_states_ownership(
    cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    primary = tmp_path / "data/raw/TON-IoT/Processed_datasets/Processed_Network_dataset"
    primary.mkdir(parents=True)
    (primary / "Network_dataset_1.csv").write_text(
        "ts,src_ip,proto,service,label,type\n1,10.0.0.1,tcp,http,0,normal\n",
        encoding="utf-8",
    )
    secondary = (
        tmp_path / "data/raw/Edge-IIoTset/Edge-IIoTset dataset/Selected dataset for ML and DL"
    )
    secondary.mkdir(parents=True)
    (secondary / "DNN-EdgeIIoT-dataset.csv").write_text(
        "frame.time,ip.src_host,Attack_label,Attack_type,tcp.flags\n1,192.168.0.1,0,Normal,2\n",
        encoding="utf-8",
    )
    loaded = load_production_configuration()
    monkeypatch.setattr(
        preprocess_module,
        "production_configuration_context",
        lambda: (tmp_path, loaded),
    )
    selected = cli_runner.invoke(application, ["preprocess", "edge-iiotset"])
    assert selected.exit_code == 0
    assert DatasetName.EDGE_IIOTSET.value in selected.stdout
    assert (
        DatasetName.TON_IOT_NETWORK.value
        not in selected.stdout.split("datasets=")[1].splitlines()[0]
    )
    both = cli_runner.invoke(application, ["preprocess"])
    assert both.exit_code == 0
    assert DatasetName.TON_IOT_NETWORK.value in both.stdout
    assert DatasetName.EDGE_IIOTSET.value in both.stdout
    overwritten = cli_runner.invoke(application, ["preprocess", "edge-iiotset", "--overwrite"])
    assert overwritten.exit_code == 0
    assert "overwrite=True" in overwritten.stdout
    assert PreprocessingLayer.INVENTORY.value in overwritten.stdout
    forbidden = ",".join(kind.value for kind in preprocess_must_not_regenerate())
    assert forbidden in overwritten.stdout
    assert DownstreamArtifactKind.DETECTOR_MODELS.value in overwritten.stdout
    assert "must_not_regenerate=" in overwritten.stdout
