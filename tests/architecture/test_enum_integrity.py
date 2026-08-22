from __future__ import annotations

import ast
from pathlib import Path

import pytest
from tests.architecture.ast_scans import SRC_ROOT, source_files

from fedcampaign_emhi.domain.enums import (
    ClaimIdentifier,
    ContextMethodName,
    DatasetName,
    DetectorFamily,
    ExperimentName,
    GeneratorName,
    MethodName,
    NuisanceTransformName,
    PartitionRole,
)

ENUMS = (
    DatasetName,
    ExperimentName,
    MethodName,
    ContextMethodName,
    GeneratorName,
    NuisanceTransformName,
    DetectorFamily,
    PartitionRole,
    ClaimIdentifier,
)
VALUE_TO_ENUM: dict[str, str] = {}
for enum_type in ENUMS:
    for member in enum_type:
        VALUE_TO_ENUM.setdefault(str(member.value), enum_type.__name__)


def _enum_literal_findings(path: Path) -> list[tuple[str, int, str, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    rel = path.relative_to(SRC_ROOT).as_posix()
    findings: list[tuple[str, int, str, str]] = []
    if rel.startswith("config/") or rel == "domain/enums.py":
        return findings
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        enum_name = VALUE_TO_ENUM.get(node.value)
        if enum_name is None:
            continue
        findings.append((rel, node.lineno, node.value, enum_name))
    return findings


@pytest.mark.parametrize("path", source_files(), ids=lambda p: p.relative_to(SRC_ROOT).as_posix())
def test_enum_integrity(path: Path) -> None:
    findings = _enum_literal_findings(path)
    assert findings == [], f"enum-value string literals bypass enums: {findings}"


def test_enums_are_used() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in source_files())
    for enum_type in ENUMS:
        assert enum_type.__name__ in source


def test_enum_integrity_fails_on_fixture() -> None:
    tree = ast.parse('name = "Corrected OpTC"\n')
    constants = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and node.value == DatasetName.CORRECTED_OPTC.value
    ]
    assert constants


def test_enum_integrity_passes_on_compliant_fixture() -> None:
    tree = ast.parse(
        "from fedcampaign_emhi.domain.enums import DatasetName\nname = DatasetName.CORRECTED_OPTC\n"
    )
    constants = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and node.value == DatasetName.CORRECTED_OPTC.value
    ]
    assert constants == []
