from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tests.architecture.ast_scans import REPO_ROOT


def test_static_typing() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "pyright"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_static_typing_fails_on_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "bad.py"
    fixture.write_text("def typed(flag: int) -> str:\n    return flag\n", encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "-m", "pyright", str(fixture)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0


def test_static_typing_passes_on_compliant_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "good.py"
    fixture.write_text("def typed(flag: int) -> int:\n    return flag\n", encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "-m", "pyright", str(fixture)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
