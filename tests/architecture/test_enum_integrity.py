from __future__ import annotations

import ast
from pathlib import Path

from tests.architecture.ast_scans import SRC_ROOT, parametrize_source_files, source_files

from fedcampaign_emhi.domain.enums import (
    ArtifactLifecycleState,
    ContextMethodName,
    DatasetName,
    DetectorFamily,
    ExperimentName,
    ExperimentState,
    FitStatus,
    GeneratorName,
    GroundTruthClass,
    MethodName,
    NuisanceTransformName,
    OverwritePolicy,
    PartitionRole,
    PrimaryHolmHypothesis,
    RecordExclusionReason,
    SecondaryHolmHypothesis,
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
    ExperimentState,
    FitStatus,
    OverwritePolicy,
    ArtifactLifecycleState,
    PrimaryHolmHypothesis,
    SecondaryHolmHypothesis,
    GroundTruthClass,
    RecordExclusionReason,
)
VALUE_TO_ENUM: dict[str, str] = {}
for enum_type in ENUMS:
    for member in enum_type:
        VALUE_TO_ENUM.setdefault(str(member.value), enum_type.__name__)


def _enum_literal_findings(path: Path) -> list[tuple[str, int, str, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    rel = path.relative_to(SRC_ROOT).as_posix() if path.is_relative_to(SRC_ROOT) else path.name
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


@parametrize_source_files
def test_enum_integrity(path: Path) -> None:
    findings = _enum_literal_findings(path)
    assert findings == [], f"enum-value string literals bypass enums: {findings}"


def test_enums_are_used() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in source_files())
    for enum_type in ENUMS:
        assert enum_type.__name__ in source


def test_enum_integrity_fails_on_fixture() -> None:
    tree = ast.parse('name = "TON_IoT Network"\n')
    constants = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and node.value == DatasetName.TON_IOT_NETWORK.value
    ]
    assert constants


def test_enum_integrity_passes_on_compliant_fixture() -> None:
    tree = ast.parse(
        "from fedcampaign_emhi.domain.enums import DatasetName\nname = DatasetName.TON_IOT_NETWORK\n"
    )
    constants = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and node.value == DatasetName.TON_IOT_NETWORK.value
    ]
    assert constants == []


def test_enum_integrity_rejects_hypothesis_identifier_literal(tmp_path: Path) -> None:
    path = tmp_path / "producer.py"
    path.write_text(
        "def materialize() -> None:\n    identifier = 'Pure-Order Target Drift'\n",
        encoding="utf-8",
    )
    assert _enum_literal_findings(path) == [
        (
            "producer.py",
            2,
            PrimaryHolmHypothesis.PURE_ORDER_TARGET_DRIFT.value,
            "PrimaryHolmHypothesis",
        )
    ]


def test_enum_integrity_rejects_execution_state_literal(tmp_path: Path) -> None:
    path = tmp_path / "producer.py"
    path.write_text(
        "def run() -> None:\n    state = 'Completed'\n",
        encoding="utf-8",
    )
    assert _enum_literal_findings(path) == [
        ("producer.py", 2, ExperimentState.COMPLETED.value, "ExperimentState")
    ]


def test_enum_integrity_accepts_hypothesis_enum_value_reference(tmp_path: Path) -> None:
    path = tmp_path / "producer.py"
    path.write_text(
        "from fedcampaign_emhi.domain.enums import PrimaryHolmHypothesis\n"
        "def materialize() -> None:\n"
        "    identifier = PrimaryHolmHypothesis.PURE_ORDER_TARGET_DRIFT.value\n",
        encoding="utf-8",
    )
    assert _enum_literal_findings(path) == []
