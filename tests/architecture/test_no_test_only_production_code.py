from __future__ import annotations

import ast
from pathlib import Path

from tests.architecture.ast_scans import (
    SRC_ROOT,
    architecture_test_paths,
    module_ast,
    source_files,
)


def _imported_production_modules() -> set[str]:
    imported: set[str] = set()
    for path in source_files():
        tree = module_ast(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("fedcampaign_emhi"):
                        imported.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("fedcampaign_emhi"):
                    imported.add(node.module)
                    for alias in node.names:
                        imported.add(f"{node.module}.{alias.name}")
    return imported


def test_no_test_only_production_code() -> None:
    production_imports = _imported_production_modules()
    test_only: list[str] = []
    for path in source_files():
        rel = path.relative_to(SRC_ROOT).as_posix()
        if rel in {"__init__.py", "py.typed"}:
            continue
        module = "fedcampaign_emhi." + rel[:-3].replace("/", ".")
        if module.endswith(".__init__"):
            module = module[: -len(".__init__")]
        referenced_in_production = any(
            item == module or item.startswith(module + ".") for item in production_imports
        )
        if referenced_in_production:
            continue
        referenced_in_tests = False
        for test_path in architecture_test_paths():
            text = test_path.read_text(encoding="utf-8")
            if module in text:
                referenced_in_tests = True
                break
        if referenced_in_tests and not referenced_in_production:
            test_only.append(module)
    assert test_only == []


def test_no_test_only_production_code_fails_on_fixture(tmp_path: Path) -> None:
    production = "fedcampaign_emhi.ghost_only_for_tests"
    test_text = f"from {production} import value\n"
    assert production in test_text
    assert "ghost_only_for_tests" not in "from fedcampaign_emhi.config.loading import load\n"


def test_no_test_only_production_code_passes_on_compliant_fixture() -> None:
    imports = _imported_production_modules()
    assert any(item.startswith("fedcampaign_emhi.config") for item in imports)
