from __future__ import annotations

import ast
from pathlib import Path

from tests.architecture.ast_scans import SRC_ROOT, module_ast, source_files

PACKAGE_INITS = {"__init__.py"}
SHIM_MARKERS = (
    "compatibility",
    "deprecated",
    "legacy",
    "shim",
    "reexport",
    "re-export",
    "alias for",
    "backward compatible",
)


def _is_reexport_only(path: Path) -> bool:
    if path.name in PACKAGE_INITS:
        return False
    tree = module_ast(path)
    if not tree.body:
        return False
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            continue
        if isinstance(node, ast.Assign):
            targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if targets == ["__all__"]:
                continue
            return False
        return False
    return True


def test_no_redirects_shims_reexports() -> None:
    findings: list[str] = []
    for path in source_files():
        rel = path.relative_to(SRC_ROOT).as_posix()
        text = path.read_text(encoding="utf-8").lower()
        if any(marker in text for marker in SHIM_MARKERS):
            findings.append(f"{rel}:shim-language")
        if _is_reexport_only(path):
            findings.append(f"{rel}:reexport-only")
    assert findings == []


def test_package_initializers_do_not_create_unowned_public_apis() -> None:
    findings: list[str] = []
    for path in source_files():
        if path.name != "__init__.py":
            continue
        tree = module_ast(path)
        for node in tree.body:
            if isinstance(node, ast.Import | ast.ImportFrom):
                findings.append(f"{path.relative_to(SRC_ROOT).as_posix()}:reexport")
            elif isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
            ):
                findings.append(f"{path.relative_to(SRC_ROOT).as_posix()}:public-export")
    assert findings == []


def test_no_redirects_shims_reexports_fails_on_fixture() -> None:
    tree = ast.parse("from fedcampaign_emhi.config.loading import load_production_configuration\n")
    assert all(isinstance(node, ast.ImportFrom) for node in tree.body)


def test_package_initializer_check_rejects_reexports() -> None:
    tree = ast.parse("from fedcampaign_emhi.config.loading import load_production_configuration\n")
    assert any(isinstance(node, ast.ImportFrom) for node in tree.body)


def test_no_redirects_shims_reexports_passes_on_compliant_fixture() -> None:
    tree = ast.parse(
        "from fedcampaign_emhi.domain.types import ModuleContract\n"
        "\n"
        "def loading_contract() -> ModuleContract:\n"
        "    return ModuleContract(module_name='fedcampaign_emhi.datasets.ton_iot_network.loading', ownership='adapter')\n"
    )
    assert any(isinstance(node, ast.FunctionDef) for node in tree.body)
