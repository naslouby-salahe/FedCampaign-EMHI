from typer.testing import CliRunner

from fedcampaign_emhi.cli.main import application
from fedcampaign_emhi.domain.enums import DatasetName, DownstreamArtifactKind, PreprocessingLayer
from fedcampaign_emhi.execution.planning import RESUME_SEQUENCE
from fedcampaign_emhi.execution.preprocess import preprocess_must_not_regenerate


def test_resume_sequence_is_fixed() -> None:
    assert RESUME_SEQUENCE[0] == "validate required existing artifacts"
    assert RESUME_SEQUENCE[-1] == "atomically publish completed outputs"


def test_preprocess_cli_selects_dataset_and_states_ownership(cli_runner: CliRunner) -> None:
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
