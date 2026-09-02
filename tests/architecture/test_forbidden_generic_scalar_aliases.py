from __future__ import annotations

import ast
from pathlib import Path

import pytest
from tests.architecture.ast_scans import SRC_ROOT, module_ast, source_files

FORBIDDEN_GENERIC_SCALAR_ALIASES = frozenset(
    {
        "NonNegativeInt",
        "PositiveInt",
        "NonNegativeFloat",
        "PositiveFloat",
        "UnitInterval",
        "OpenUnitInterval",
        "FiniteFloat",
        "SignedInt",
    }
)
CANONICAL_TYPES_FILE = SRC_ROOT / "domain" / "types.py"


def generic_scalar_alias_violations(path: Path) -> list[str]:
    if path == CANONICAL_TYPES_FILE:
        return []
    relative = path.relative_to(SRC_ROOT).as_posix() if path.is_relative_to(SRC_ROOT) else path.name
    violations: list[str] = []
    for node in ast.walk(module_ast(path)):
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_GENERIC_SCALAR_ALIASES:
            violations.append(f"{relative}:{node.lineno}:{node.id}")
        elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_GENERIC_SCALAR_ALIASES:
            violations.append(f"{relative}:{node.lineno}:{node.attr}")
        elif isinstance(node, ast.ImportFrom):
            for imported in node.names:
                if imported.name in FORBIDDEN_GENERIC_SCALAR_ALIASES:
                    violations.append(f"{relative}:{node.lineno}:{imported.name}")
    return sorted(violations)


@pytest.mark.parametrize("path", source_files(), ids=lambda path: path.relative_to(SRC_ROOT))
def test_forbidden_generic_scalar_aliases_are_confined_to_types(path: Path) -> None:
    assert generic_scalar_alias_violations(path) == []


def test_generic_alias_rule_rejects_imports_and_nested_annotations(tmp_path: Path) -> None:
    path = tmp_path / "consumer.py"
    path.write_text(
        "from fedcampaign_emhi.domain.types import FiniteFloat\n"
        "def score(values: tuple[FiniteFloat, ...]) -> FiniteFloat: ...\n",
        encoding="utf-8",
    )
    assert generic_scalar_alias_violations(path) == [
        "consumer.py:1:FiniteFloat",
        "consumer.py:2:FiniteFloat",
        "consumer.py:2:FiniteFloat",
    ]


def test_generic_alias_rule_rejects_qualified_reference(tmp_path: Path) -> None:
    path = tmp_path / "consumer.py"
    path.write_text(
        "import fedcampaign_emhi.domain.types as types\ndef score() -> types.FiniteFloat: ...\n",
        encoding="utf-8",
    )
    assert generic_scalar_alias_violations(path) == ["consumer.py:2:FiniteFloat"]


def test_generic_alias_rule_accepts_canonical_domain_types(tmp_path: Path) -> None:
    path = tmp_path / "consumer.py"
    path.write_text(
        "from fedcampaign_emhi.domain.types import ClientCount\n"
        "def count(value: ClientCount) -> ClientCount: ...\n",
        encoding="utf-8",
    )
    tree = module_ast(path)
    assert not [
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_GENERIC_SCALAR_ALIASES
    ]


def test_generic_alias_scanner_covers_every_production_python_file() -> None:
    assert source_files() == tuple(sorted(SRC_ROOT.rglob("*.py")))
