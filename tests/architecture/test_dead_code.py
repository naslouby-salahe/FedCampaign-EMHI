from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tests.architecture.ast_scans import REPO_ROOT, SRC_ROOT


def test_dead_code() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "vulture", "src", "--min-confidence", "80"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_dead_code_fails_on_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "unused.py"
    fixture.write_text("def foo_never_called():\n    return 1\n", encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "-m", "vulture", str(fixture), "--min-confidence", "60"],
        check=False,
        capture_output=True,
        text=True,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode != 0
    assert "foo_never_called" in output


def test_dead_code_passes_on_compliant_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "used.py"
    fixture.write_text(
        "def used_symbol():\n    return 1\n\nprint(used_symbol())\n",
        encoding="utf-8",
    )
    completed = subprocess.run(
        [sys.executable, "-m", "vulture", str(fixture), "--min-confidence", "80"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_required_modules_are_present() -> None:
    assert (SRC_ROOT / "config" / "schema.py").is_file()
    assert (SRC_ROOT / "cli" / "main.py").is_file()
