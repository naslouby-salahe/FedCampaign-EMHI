from __future__ import annotations

import ast
from pathlib import Path

import pytest
from tests.architecture.ast_scans import SRC_ROOT, module_ast

SCIENTIFIC_LIBRARY_ROOTS = frozenset(
    {"duckdb", "numpy", "scipy", "sklearn", "pandas", "polars", "torch"}
)


def _violations(path: Path) -> list[str]:
    tree = module_ast(path)
    relative = path.relative_to(SRC_ROOT).as_posix()
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in SCIENTIFIC_LIBRARY_ROOTS:
                    violations.append(f"{relative}:{node.lineno}: scientific import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".", 1)[0] in SCIENTIFIC_LIBRARY_ROOTS:
                violations.append(f"{relative}:{node.lineno}: scientific import {node.module}")
        elif isinstance(node, ast.ClassDef):
            violations.append(f"{relative}:{node.lineno}: CLI class {node.name}")
    return violations


def _snippet_violations(snippet: str) -> list[str]:
    temporary = SRC_ROOT / "cli" / "snippet.py"
    tree = ast.parse(snippet)
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in SCIENTIFIC_LIBRARY_ROOTS:
                    violations.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".", 1)[0] in SCIENTIFIC_LIBRARY_ROOTS:
                violations.append(node.module)
        elif isinstance(node, ast.ClassDef):
            violations.append(node.name)
    return [str(temporary)] if violations else []


def test_cli_commands_only_control_application_execution() -> None:
    command_root = SRC_ROOT / "cli" / "commands"
    violations = [
        violation for path in command_root.rglob("*.py") for violation in _violations(path)
    ]
    assert violations == []


@pytest.mark.parametrize(
    "snippet",
    [
        "import numpy\n",
        "from scipy import stats\n",
        "class ExperimentExecutor:\n    pass\n",
    ],
)
def test_cli_boundary_rejects_scientific_implementation_escape_hatches(snippet: str) -> None:
    assert _snippet_violations(snippet)


@pytest.mark.parametrize(
    "snippet",
    [
        "import typer\ndef command() -> None:\n    typer.echo('ok')\n",
        "from fedcampaign_emhi.execution.runner import execute_experiment\n",
    ],
)
def test_cli_boundary_accepts_control_surface_code(snippet: str) -> None:
    assert _snippet_violations(snippet) == []
