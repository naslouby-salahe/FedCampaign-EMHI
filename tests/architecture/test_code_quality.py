from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tests.architecture.ast_scans import REPO_ROOT


def test_code_quality() -> None:
    formatted = subprocess.run(
        [sys.executable, "-m", "ruff", "format", "--check", "src", "tests"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    linted = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "src", "tests"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    scanned = subprocess.run(
        [
            str(Path(sys.executable).parent / "semgrep"),
            "--config",
            ".semgrep/architecture.yml",
            "--error",
            "--quiet",
            "src",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert formatted.returncode == 0, formatted.stdout + formatted.stderr
    assert linted.returncode == 0, linted.stdout + linted.stderr
    assert scanned.returncode == 0, scanned.stdout + scanned.stderr


def test_code_quality_fails_on_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "bad.py"
    fixture.write_text("import os,sys\n\n\n\n\nx=1\n", encoding="utf-8")
    linted = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(fixture)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert linted.returncode != 0


def test_code_quality_passes_on_compliant_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "good.py"
    fixture.write_text("value = 1\n", encoding="utf-8")
    formatted = subprocess.run(
        [sys.executable, "-m", "ruff", "format", "--check", str(fixture)],
        check=False,
        capture_output=True,
        text=True,
    )
    linted = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(fixture)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert formatted.returncode == 0, formatted.stdout + formatted.stderr
    assert linted.returncode == 0, linted.stdout + linted.stderr
