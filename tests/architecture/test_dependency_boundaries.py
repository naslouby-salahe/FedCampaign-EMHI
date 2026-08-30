from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

from tests.architecture.ast_scans import (
    REPO_ROOT,
    SRC_ROOT,
    module_ast,
    parametrize_source_files,
    source_files,
)

PACKAGE_DEPENDENCIES: dict[str, frozenset[str]] = {
    "domain": frozenset(),
    "config": frozenset({"domain"}),
    "runtime": frozenset({"domain", "config"}),
    "artifacts": frozenset({"domain", "config", "runtime"}),
    "datasets": frozenset({"domain", "config", "artifacts", "runtime"}),
    "models": frozenset({"domain", "config", "artifacts", "runtime"}),
    "emhi": frozenset({"domain", "config", "artifacts", "runtime"}),
    "detection": frozenset({"domain", "config", "models", "emhi", "artifacts", "runtime"}),
    "comparators": frozenset({"domain", "config", "emhi", "artifacts", "runtime", "models"}),
    "synthetic": frozenset({"domain", "config", "emhi", "runtime"}),
    "experiments": frozenset({"domain", "config", "emhi", "comparators", "synthetic"}),
    "evaluation": frozenset(
        {"domain", "config", "emhi", "comparators", "artifacts", "datasets", "detection"}
    ),
    "analysis": frozenset({"domain", "config", "evaluation", "artifacts"}),
    "execution": frozenset(
        {
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
        }
    ),
    "reporting": frozenset(
        {
            "domain",
            "config",
            "artifacts",
            "analysis",
            "evaluation",
            "experiments",
            "runtime",
        }
    ),
    "cli": frozenset(
        {
            "domain",
            "config",
            "runtime",
            "artifacts",
            "datasets",
            "models",
            "emhi",
            "detection",
            "comparators",
            "synthetic",
            "experiments",
            "evaluation",
            "analysis",
            "execution",
            "reporting",
        }
    ),
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


@parametrize_source_files
def test_dependency_boundaries(path: Path) -> None:
    rel = path.relative_to(SRC_ROOT).as_posix()
    package = _package_of(rel)
    if package == "__init__":
        return
    assert package in PACKAGE_DEPENDENCIES, f"{rel} has no declared architectural owner"
    allowed = PACKAGE_DEPENDENCIES[package]
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
