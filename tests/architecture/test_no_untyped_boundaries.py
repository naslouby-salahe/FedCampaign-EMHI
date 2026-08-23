from __future__ import annotations

import ast
from pathlib import Path

from tests.architecture.ast_scans import SRC_ROOT, module_ast, parametrize_source_files

TYPED_PRIMITIVES_ALLOWED_IN_CLI = {"str", "str | None"}


def _is_untyped_public_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    if node.name.startswith("_"):
        return None
    for arg in [*node.args.args, *node.args.kwonlyargs]:
        if arg.arg in {"self", "cls"}:
            continue
        if arg.annotation is None:
            return f"untyped parameter '{arg.arg}'"
    if node.args.vararg is not None and node.args.vararg.annotation is None:
        return f"untyped vararg '{node.args.vararg.arg}'"
    if node.args.kwarg is not None and node.args.kwarg.annotation is None:
        return f"untyped kwarg '{node.args.kwarg.arg}'"
    if node.returns is None and node.name != "main":
        return "missing return annotation"
    return None


def _scan(path: Path) -> list[str]:
    tree = module_ast(path)
    try:
        rel = path.relative_to(SRC_ROOT).as_posix()
    except ValueError:
        rel = path.name
    findings: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        problem = _is_untyped_public_function(node)
        if problem is None:
            continue
        findings.append(f"{rel}:{node.lineno}:{node.name}: {problem}")
    return findings


@parametrize_source_files
def test_no_untyped_public_boundaries(path: Path) -> None:
    assert _scan(path) == []


def test_untyped_boundary_scan_detects_fixture(tmp_path: Path) -> None:
    bad = tmp_path / "bad.py"
    bad.write_text("def public_api(value):\n    return value\n", encoding="utf-8")
    assert _scan(bad) != []
    good = tmp_path / "good.py"
    good.write_text(
        "def public_api(value: int) -> int:\n    return value\n"
        "\n\ndef _private(value):\n    return value\n",
        encoding="utf-8",
    )
    assert _scan(good) == []
