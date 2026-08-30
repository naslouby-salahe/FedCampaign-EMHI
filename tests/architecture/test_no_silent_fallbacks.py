from __future__ import annotations

import ast
from pathlib import Path

from tests.architecture.ast_scans import SRC_ROOT, module_ast, parametrize_source_files


def _scan(path: Path) -> list[str]:
    tree = module_ast(path)
    try:
        rel = path.relative_to(SRC_ROOT).as_posix()
    except ValueError:
        rel = path.name
    findings: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                findings.append(f"{rel}:{node.lineno}:bare except")
            elif isinstance(node.type, ast.Tuple) and len(node.type.elts) > 2:
                findings.append(f"{rel}:{node.lineno}:broad except tuple")
        if isinstance(node, ast.Call):
            func = node.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            if name in {"fallback", "silent_default", "coerce_or_default"}:
                findings.append(f"{rel}:{node.lineno}:forbidden fallback helper '{name}'")
        if isinstance(node, ast.IfExp):
            test = node.test
            if isinstance(test, ast.Constant) and test.value is None:
                findings.append(f"{rel}:{node.lineno}:None-coalescing fallback")
    return findings


@parametrize_source_files
def test_no_silent_fallbacks(path: Path) -> None:
    assert _scan(path) == []


def test_no_silent_fallbacks_detects_and_accepts_fixtures(tmp_path: Path) -> None:
    bad = tmp_path / "bad.py"
    bad.write_text(
        "try:\n    value = 1\nexcept:\n    value = 0\n",
        encoding="utf-8",
    )
    assert _scan(bad) != []
    good = tmp_path / "good.py"
    good.write_text(
        "try:\n    value = 1\nexcept ValueError:\n    value = 0\n",
        encoding="utf-8",
    )
    assert _scan(good) == []
