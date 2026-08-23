from __future__ import annotations

import ast
from pathlib import Path

from tests.architecture.ast_scans import (
    REPO_ROOT,
    SRC_ROOT,
    module_ast,
    parametrize_source_files,
)

ALLOWED_FLOATS = {0.0, 0.5, 1.0, 2.0, 8.0}
CONFIG_OWNERS = frozenset({"config/schema.py", "config/loading.py", "config/validation.py"})
FORMULA_OWNERS = frozenset(
    {
        "config/loading.py",
        "emhi/basis.py",
        "emhi/evidence.py",
        "emhi/projection.py",
        "models/autoencoder.py",
        "evaluation/smoke_gate.py",
    }
)


def _scan_literals(path: Path) -> list[tuple[int, str]]:
    tree = module_ast(path)
    findings: list[tuple[int, str]] = []
    rel = path.relative_to(SRC_ROOT).as_posix()
    if rel in CONFIG_OWNERS:
        return findings
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant):
            continue
        if isinstance(node.value, float) and node.value not in ALLOWED_FLOATS:
            if abs(node.value) in {0.125}:
                continue
            if rel in FORMULA_OWNERS:
                continue
            findings.append((node.lineno, f"float {node.value!r}"))
        if isinstance(node.value, int) and node.value in {66, 59, 1024, 8000, 10000, 4100, 3000}:
            findings.append((node.lineno, f"int {node.value}"))
    return findings


@parametrize_source_files
def test_no_hardcoded_values(path: Path) -> None:
    findings = _scan_literals(path)
    assert not findings, f"{path}: {findings}"


def test_production_values_live_in_yaml() -> None:
    yaml_text = (REPO_ROOT / "configs" / "fedcampaign-emhi.yaml").read_text(encoding="utf-8")
    assert "maximum_coalition_order: 3" in yaml_text
    assert "real_data_epoch_seconds: 60" in yaml_text
    assert "target_pfa: 0.05" in yaml_text


def test_cli_has_no_scientific_overrides() -> None:
    findings: list[str] = []
    for path in (SRC_ROOT / "cli").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in (
            "--seed",
            "--method",
            "--coalition-order",
            "--basis",
            "--threshold",
            "--pfa",
            "--run-id",
        ):
            if token in text:
                findings.append(f"{path.name}:{token}")
    assert findings == []


def test_no_hardcoded_values_fails_on_fixture() -> None:
    tree = ast.parse("threshold = 0.05\nseed = 4100\n")
    findings: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and node.value in {0.05, 4100}:
            findings.append(str(node.value))
    assert findings == ["0.05", "4100"]


def test_no_hardcoded_values_passes_on_compliant_fixture() -> None:
    tree = ast.parse("neutral = 1.0\n")
    findings: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            if node.value not in ALLOWED_FLOATS:
                findings.append(str(node.value))
    assert findings == []
