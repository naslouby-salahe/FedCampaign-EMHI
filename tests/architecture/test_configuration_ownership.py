from __future__ import annotations

import ast

from tests.architecture.ast_scans import REPO_ROOT, SRC_ROOT, module_ast, source_files


def test_configuration_ownership() -> None:
    production = REPO_ROOT / "configs" / "fedcampaign-emhi.yaml"
    tests = REPO_ROOT / "configs" / "tests.yml"
    smoke = REPO_ROOT / "configs" / "smoke.yml"
    assert production.is_file()
    assert tests.is_file()
    assert smoke.is_file()
    loaders = (SRC_ROOT / "config" / "loading.py").read_text(encoding="utf-8")
    assert "configs/fedcampaign-emhi.yaml" in loaders
    assert "configs/tests.yml" in loaders
    assert "configs/smoke.yml" in loaders


def test_no_parallel_scientific_config_models() -> None:
    findings: list[str] = []
    for path in source_files():
        rel = path.relative_to(SRC_ROOT).as_posix()
        if rel.startswith("config/"):
            continue
        tree = module_ast(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.endswith("Config"):
                findings.append(f"{rel}:{node.lineno}:{node.name}")
    assert findings == []


def test_cli_does_not_default_scientific_values() -> None:
    findings: list[str] = []
    for path in (SRC_ROOT / "cli").rglob("*.py"):
        tree = module_ast(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            for default in node.args.defaults + [item for item in node.args.kw_defaults if item]:
                if isinstance(default, ast.Constant) and isinstance(default.value, int | float):
                    if default.value not in {False, True}:
                        findings.append(f"{path.name}:{node.name}:{default.value!r}")
    assert findings == []


def test_configuration_ownership_fails_on_fixture() -> None:
    tree = ast.parse("class ShadowConfig:\n    seed = 4100\n")
    names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    assert "ShadowConfig" in names


def test_configuration_ownership_passes_on_compliant_fixture() -> None:
    tree = ast.parse("from fedcampaign_emhi.config.loading import load_production_configuration\n")
    names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    assert names == []
