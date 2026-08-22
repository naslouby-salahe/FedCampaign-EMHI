from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest
from tests.architecture.ast_scans import REPO_ROOT, SRC_ROOT, module_ast, source_files

ALLOWED_DEPENDENCIES: dict[str, set[str]] = {
    "domain": set(),
    "config": {"domain"},
    "runtime": {"domain", "config"},
    "artifacts": {"domain", "config", "runtime"},
    "datasets": {"domain", "config", "artifacts", "runtime"},
    "models": {"domain", "config", "artifacts", "runtime"},
    "emhi": {"domain", "config", "artifacts", "runtime"},
    "detection": {"domain", "config", "models", "artifacts", "runtime"},
    "comparators": {"domain", "config", "emhi", "artifacts", "runtime", "models"},
    "synthetic": {"domain", "config", "emhi", "runtime"},
    "experiments": {"domain", "config"},
    "evaluation": {"domain", "config", "emhi", "comparators", "artifacts"},
    "analysis": {"domain", "config", "evaluation", "artifacts"},
    "execution": {
        "domain",
        "config",
        "experiments",
        "artifacts",
        "runtime",
        "evaluation",
        "analysis",
        "datasets",
        "emhi",
        "detection",
        "synthetic",
        "comparators",
        "models",
    },
    "reporting": {
        "domain",
        "config",
        "artifacts",
        "analysis",
        "evaluation",
        "experiments",
        "runtime",
    },
    "cli": set(),
}


def _imported_packages(tree: ast.Module) -> set[str]:
    packages: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "fedcampaign_emhi" or alias.name.startswith("fedcampaign_emhi."):
                    parts = alias.name.split(".")
                    if len(parts) >= 2:
                        packages.add(parts[1])
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "fedcampaign_emhi" or node.module.startswith("fedcampaign_emhi."):
                parts = node.module.split(".")
                if len(parts) >= 2:
                    packages.add(parts[1])
    return packages


def _package_of(rel: str) -> str:
    if "/" not in rel:
        return Path(rel).stem
    return rel.split("/")[0]


@pytest.mark.parametrize("path", source_files(), ids=lambda p: p.relative_to(SRC_ROOT).as_posix())
def test_dependency_boundaries(path: Path) -> None:
    rel = path.relative_to(SRC_ROOT).as_posix()
    package = _package_of(rel)
    if package in {"cli", "__init__"}:
        return
    allowed = ALLOWED_DEPENDENCIES[package]
    imported = _imported_packages(module_ast(path))
    violations = sorted(imported - allowed - {package})
    assert not violations, f"{rel} imports outside its layer set: {violations}"


def test_import_linter_contract() -> None:
    completed = subprocess.run(
        [str(Path(sys.executable).parent / "lint-imports")],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_cli_is_not_imported_by_lower_layers() -> None:
    findings: list[str] = []
    for path in source_files():
        rel = path.relative_to(SRC_ROOT).as_posix()
        if rel.startswith("cli/"):
            continue
        imported = _imported_packages(module_ast(path))
        if "cli" in imported:
            findings.append(rel)
    assert findings == []


def test_dependency_boundaries_fails_on_fixture() -> None:
    tree = ast.parse("from fedcampaign_emhi.cli.main import application\n")
    assert "cli" in _imported_packages(tree)


def test_dependency_boundaries_passes_on_compliant_fixture() -> None:
    tree = ast.parse("from fedcampaign_emhi.domain.enums import ExperimentName\n")
    assert _imported_packages(tree) == {"domain"}
