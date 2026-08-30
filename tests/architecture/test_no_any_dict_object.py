from __future__ import annotations

import ast
from pathlib import Path

import pytest
from tests.architecture.ast_scans import SRC_ROOT, annotation_primitives, source_files


def _file_violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []
    rel = path.relative_to(SRC_ROOT).as_posix()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in {"Any", "object"}:
            violations.append(f"{rel}:{node.lineno}:{node.id}")
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            if node.value.id in {"dict", "Dict"}:
                violations.append(f"{rel}:{node.lineno}:{node.value.id}")
    return violations


@pytest.mark.parametrize("path", source_files(), ids=lambda p: p.relative_to(SRC_ROOT).as_posix())
def test_no_any_dict_object(path: Path) -> None:
    assert _file_violations(path) == []


def test_no_any_dict_object_fails_on_fixture() -> None:
    tree = ast.parse("from typing import Any\nvalue: Any = 1\npayload: dict[str, int] = {}\n")
    findings: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in {"Any", "object"}:
            findings.append(node.id)
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            if node.value.id == "dict":
                findings.append("dict")
    assert "Any" in findings
    assert "dict" in findings


def test_no_any_dict_object_passes_on_compliant_fixture() -> None:
    tree = ast.parse(
        "from fedcampaign_emhi.domain.types import ClientCount\ncount: ClientCount = 12\n"
    )
    findings = (
        annotation_primitives(tree.body[-1].annotation)
        if isinstance(tree.body[-1], ast.AnnAssign)
        else ["missing"]
    )
    assert findings == []
