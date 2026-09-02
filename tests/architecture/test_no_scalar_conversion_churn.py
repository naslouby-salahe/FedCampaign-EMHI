from __future__ import annotations

import ast
from pathlib import Path

import pytest
from tests.architecture.ast_scans import SRC_ROOT, module_ast, source_files

SCALAR_CONSTRUCTORS = frozenset({"int", "float", "str", "bool"})


def contains_enum_value(expression: ast.expr) -> bool:
    return any(
        isinstance(node, ast.Attribute) and node.attr == "value" for node in ast.walk(expression)
    )


def scalar_conversion_violations(path: Path, root: Path = SRC_ROOT) -> list[str]:
    relative = path.relative_to(root).as_posix()
    violations: list[str] = []
    for node in ast.walk(module_ast(path)):
        if isinstance(node, ast.Compare) and any(
            contains_enum_value(operand) for operand in (node.left, *node.comparators)
        ):
            violations.append(f"{relative}:{node.lineno}: enum value comparison")
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id not in SCALAR_CONSTRUCTORS or len(node.args) != 1:
            continue
        argument = node.args[0]
        if isinstance(argument, ast.Attribute) and argument.attr == "value":
            violations.append(f"{relative}:{node.lineno}: scalar conversion of enum value")
        if (
            isinstance(argument, ast.Call)
            and isinstance(argument.func, ast.Name)
            and argument.func.id in SCALAR_CONSTRUCTORS
        ):
            violations.append(f"{relative}:{node.lineno}: nested scalar conversion")
    return sorted(violations)


@pytest.mark.parametrize(
    "path", source_files(), ids=lambda path: path.relative_to(SRC_ROOT).as_posix()
)
def test_no_scalar_conversion_churn(path: Path) -> None:
    assert scalar_conversion_violations(path) == []


def test_scalar_conversion_rule_rejects_internal_unwrapping(tmp_path: Path) -> None:
    path = tmp_path / "consumer.py"
    path.write_text(
        "def select(policy):\n"
        "    return str(policy.value) == 'local'\n"
        "def normalize(value):\n"
        "    return float(int(value))\n",
        encoding="utf-8",
    )
    assert scalar_conversion_violations(path, tmp_path) == [
        "consumer.py:2: enum value comparison",
        "consumer.py:2: scalar conversion of enum value",
        "consumer.py:4: nested scalar conversion",
    ]


def test_scalar_conversion_rule_accepts_external_rendering(tmp_path: Path) -> None:
    path = tmp_path / "renderer.py"
    path.write_text(
        "def render(policy):\n    return {'policy': policy.value}\n",
        encoding="utf-8",
    )
    assert scalar_conversion_violations(path, tmp_path) == []
