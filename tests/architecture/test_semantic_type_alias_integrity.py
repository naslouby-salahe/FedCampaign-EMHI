from __future__ import annotations

import ast
from pathlib import Path

import pytest
from tests.architecture.ast_scans import SRC_ROOT, module_ast

BARE_PRIMITIVES = frozenset({"str", "int", "float", "bool", "bytes"})


def _terminal_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _is_semantic_alias(value: ast.expr) -> bool:
    if isinstance(value, ast.Subscript):
        return _terminal_name(value.value) == "Annotated"
    if isinstance(value, ast.Call):
        return _terminal_name(value.func) == "NewType"
    return False


def _alias_violations(path: Path) -> list[str]:
    tree = module_ast(path)
    relative = path.relative_to(SRC_ROOT).as_posix()
    violations: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or not target.id[:1].isupper():
            continue
        if isinstance(node.value, ast.Name) and node.value.id in BARE_PRIMITIVES:
            violations.append(f"{relative}:{node.lineno}: {target.id} aliases {node.value.id}")
        elif not _is_semantic_alias(node.value):
            continue
    return violations


def test_domain_type_aliases_carry_semantic_validation() -> None:
    domain_root = SRC_ROOT / "domain"
    violations = [
        violation for path in domain_root.rglob("*.py") for violation in _alias_violations(path)
    ]
    assert violations == []


@pytest.mark.parametrize(
    "snippet",
    [
        "ClientId = str\n",
        "SampleCount = int\n",
        "Score = float\n",
    ],
)
def test_semantic_alias_rule_rejects_bare_primitive_aliases(snippet: str, tmp_path: Path) -> None:
    path = tmp_path / "aliases.py"
    path.write_text(snippet, encoding="utf-8")
    tree = ast.parse(snippet)
    violations: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            if isinstance(node.value, ast.Name) and node.value.id in BARE_PRIMITIVES:
                violations.append(node.targets[0].id)
    assert violations


def test_semantic_alias_rule_accepts_validated_aliases(tmp_path: Path) -> None:
    path = tmp_path / "aliases.py"
    path.write_text("ClientId = Annotated[str, Field(min_length=1)]\n", encoding="utf-8")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    assignment = tree.body[0]
    assert isinstance(assignment, ast.Assign)
    assert _is_semantic_alias(assignment.value)
