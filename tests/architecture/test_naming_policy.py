from __future__ import annotations

import ast
import re
from pathlib import Path

from tests.architecture.ast_scans import SRC_ROOT, iter_functions, parametrize_source_files

OPAQUE = re.compile(r"^[A-Z]+_?[0-9]+$|^[A-Z][0-9]+$")
NUMERIC_SUFFIX = re.compile(r"^[a-z][a-z0-9]*_[0-9]+$")
VAGUE = frozenset(
    {
        "data",
        "value",
        "item",
        "entry",
        "obj",
        "res",
        "result",
        "tmp",
        "arr",
        "helper",
        "manager",
        "thing",
        "handle",
        "utils",
        "misc",
        "base",
        "common",
        "processor",
    }
)
FORBIDDEN_PREFIXES = ("legacy_", "compat_", "tmp_", "old_")


def _identifier_findings(path: Path) -> list[tuple[str, int, str, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    rel = path.relative_to(SRC_ROOT).as_posix()
    findings: list[tuple[str, int, str, str]] = []

    def record(node: ast.AST, name: str, kind: str) -> None:
        if name.startswith("_"):
            return
        if name in {"self", "cls"}:
            return
        if OPAQUE.match(name) or NUMERIC_SUFFIX.match(name):
            findings.append((rel, getattr(node, "lineno", 0), name, kind))
        if any(name.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
            findings.append((rel, getattr(node, "lineno", 0), name, kind))
        if name in VAGUE:
            findings.append((rel, getattr(node, "lineno", 0), name, kind))

    for node, _owner in iter_functions(tree):
        record(node, node.name, "function")
        for arg in node.args.args + node.args.kwonlyargs:
            record(arg, arg.arg, "parameter")
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            record(node, node.name, "class")
    return findings


@parametrize_source_files
def test_naming_policy(path: Path) -> None:
    findings = _identifier_findings(path)
    assert findings == [], f"naming policy violations: {findings}"


def test_naming_policy_fails_on_fixture() -> None:
    tree = ast.parse("def helper(data, tmp):\n    return data\n")
    names = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    assert names == ["helper"]


def test_naming_policy_passes_on_compliant_fixture() -> None:
    tree = ast.parse("def coalition_count(client_count):\n    return client_count\n")
    names = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    assert names == ["coalition_count"]
