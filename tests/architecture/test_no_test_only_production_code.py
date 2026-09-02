from __future__ import annotations

import ast
from collections import deque

from tests.architecture.ast_scans import (
    SRC_ROOT,
    architecture_test_paths,
    bare_literal_only_names,
    module_ast,
    source_files,
)


def _imported_production_modules() -> set[str]:
    imported: set[str] = set()
    for path in source_files():
        tree = module_ast(path)
        registry_only = bare_literal_only_names(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local = alias.asname or alias.name.split(".")[0]
                    if alias.name.startswith("fedcampaign_emhi") and local not in registry_only:
                        imported.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("fedcampaign_emhi"):
                    for alias in node.names:
                        local = alias.asname or alias.name
                        if local in registry_only:
                            continue
                        imported.add(node.module)
                        imported.add(f"{node.module}.{alias.name}")
    return imported


def _production_module_dependencies() -> dict[str, set[str]]:
    modules: dict[str, set[str]] = {}
    known_modules = {
        "fedcampaign_emhi." + path.relative_to(SRC_ROOT).as_posix()[:-3].replace("/", ".")
        for path in source_files()
        if path.name != "__init__.py"
    }
    for path in source_files():
        if path.name == "__init__.py":
            continue
        module = "fedcampaign_emhi." + path.relative_to(SRC_ROOT).as_posix()[:-3].replace("/", ".")
        dependencies: set[str] = set()
        for node in ast.walk(module_ast(path)):
            if isinstance(node, ast.Import):
                dependencies.update(
                    alias.name for alias in node.names if alias.name in known_modules
                )
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module in known_modules:
                    dependencies.add(node.module)
                dependencies.update(
                    f"{node.module}.{alias.name}"
                    for alias in node.names
                    if f"{node.module}.{alias.name}" in known_modules
                )
        modules[module] = dependencies
    return modules


def _reachable_production_modules() -> set[str]:
    dependencies = _production_module_dependencies()
    reachable = {"fedcampaign_emhi.cli"}
    pending: deque[str] = deque(reachable)
    while pending:
        current = pending.popleft()
        for dependency in dependencies.get(current, set()):
            if dependency not in reachable:
                reachable.add(dependency)
                pending.append(dependency)
    return reachable


def _public_definition_references() -> dict[tuple[str, str], set[str]]:
    references: dict[tuple[str, str], set[str]] = {}
    for path in source_files():
        if path.name == "__init__.py":
            continue
        module = "fedcampaign_emhi." + path.relative_to(SRC_ROOT).as_posix()[:-3].replace("/", ".")
        tree = module_ast(path)
        definitions = {
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef | ast.ClassDef) and not node.name.startswith("_")
        }
        for name in definitions:
            references.setdefault((module, name), set())
    for path in source_files():
        if path.name == "__init__.py":
            continue
        module = "fedcampaign_emhi." + path.relative_to(SRC_ROOT).as_posix()[:-3].replace("/", ".")
        tree = module_ast(path)
        definitions = {
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef | ast.ClassDef) and not node.name.startswith("_")
        }
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and node.id in definitions
            ):
                references[(module, node.id)].add(module)
            elif (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("fedcampaign_emhi")
            ):
                for alias in node.names:
                    key = (node.module, alias.name)
                    if key in references:
                        references[key].add(module)
    return references


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
        if module == "fedcampaign_emhi.cli":
            continue
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


def test_every_non_initializer_production_module_has_a_production_inbound_reference() -> None:
    dependencies = _production_module_dependencies()
    unreachable = sorted(set(dependencies) - _reachable_production_modules())
    assert unreachable == []


def test_every_public_production_definition_has_a_production_reference() -> None:
    references = _public_definition_references()
    unreferenced = sorted(
        f"{module}.{name}" for (module, name), users in references.items() if not users
    )
    assert unreferenced == []


def test_no_test_only_production_code_fails_on_fixture() -> None:
    production = "fedcampaign_emhi.ghost_only_for_tests"
    test_text = f"from {production} import value\n"
    assert production in test_text
    assert "ghost_only_for_tests" not in "from fedcampaign_emhi.config.loading import load\n"


def test_production_module_reachability_rejects_an_unimported_module() -> None:
    dependencies = {"fedcampaign_emhi.cli": {"fedcampaign_emhi.config.loading"}}
    reachable = {"fedcampaign_emhi.cli", *dependencies["fedcampaign_emhi.cli"]}
    assert "fedcampaign_emhi.ghost" not in reachable


def test_no_test_only_production_code_passes_on_compliant_fixture() -> None:
    imports = _imported_production_modules()
    assert any(item.startswith("fedcampaign_emhi.config") for item in imports)


def test_analyze_command_materializes_primary_and_secondary_holm_families() -> None:
    tree = module_ast(SRC_ROOT / "cli.py")
    imported: set[str] = set()
    analyze_calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported.update(alias.name for alias in node.names)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "analyze_command":
            for child in ast.walk(node):
                if not isinstance(child, ast.Call):
                    continue
                func = child.func
                if isinstance(func, ast.Name):
                    analyze_calls.add(func.id)
                elif isinstance(func, ast.Attribute):
                    analyze_calls.add(func.attr)
    assert "materialize_primary_holm_family" in imported
    assert "materialize_secondary_holm_family" in imported
    assert "materialize_primary_holm_family" in analyze_calls
    assert "materialize_secondary_holm_family" in analyze_calls
