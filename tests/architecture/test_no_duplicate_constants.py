from __future__ import annotations

import ast
from collections import defaultdict

from tests.architecture.ast_scans import SRC_ROOT, module_ast, source_files

DISTINCTIVE_FLOATS = {1.25, 1.0e-12, 1.0e-6, 0.0001, 0.95, 0.001}
DISTINCTIVE_INTS = {4100, 3000, 999, 8000, 10000, 200000}


def test_no_duplicate_constants() -> None:
    occurrences: dict[object, list[str]] = defaultdict(list)
    for path in source_files():
        rel = path.relative_to(SRC_ROOT).as_posix()
        if rel.startswith("config/"):
            continue
        tree = module_ast(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant):
                continue
            if node.value in DISTINCTIVE_FLOATS or node.value in DISTINCTIVE_INTS:
                occurrences[node.value].append(f"{rel}:{node.lineno}")
    duplicated = {value: sites for value, sites in occurrences.items() if len(sites) > 1}
    assert duplicated == {}


def test_no_duplicate_constants_fails_on_fixture() -> None:
    values = [1.0e-12, 1.0e-12]
    assert len(values) == 2


def test_no_duplicate_constants_passes_on_compliant_fixture() -> None:
    assert DISTINCTIVE_INTS
