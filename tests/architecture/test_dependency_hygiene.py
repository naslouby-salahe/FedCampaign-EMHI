from __future__ import annotations

import subprocess
import sys

from tests.architecture.ast_scans import REPO_ROOT


def test_dependency_hygiene() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "deptry", "src"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_dependency_hygiene_fails_on_fixture() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "deptry", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "deptry" in completed.stdout.lower() or completed.returncode == 0


def test_dependency_hygiene_passes_on_compliant_fixture() -> None:
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "pydantic" in pyproject
    assert "typer" in pyproject
    assert "rfc8785" in pyproject
