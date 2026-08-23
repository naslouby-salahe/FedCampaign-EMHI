from pathlib import Path

import pytest
from typer.testing import CliRunner

from fedcampaign_emhi.config.loading import load_production_configuration, repository_root
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return repository_root()


@pytest.fixture(scope="session")
def production_configuration() -> LoadedScientificConfiguration:
    return load_production_configuration()


@pytest.fixture(scope="session")
def cli_runner() -> CliRunner:
    return CliRunner()
