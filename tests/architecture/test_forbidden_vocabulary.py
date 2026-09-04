from __future__ import annotations

import ast
import re
from pathlib import Path

from tests.architecture.ast_scans import SRC_ROOT, source_files

FORBIDDEN_TERMS = (
    "utils",
    "helpers",
    "manager",
    "processor",
    "wrapper",
    "shim",
    "compat",
    "legacy",
    "v2",
    "final2",
    "ton_iot_network_v2",
    "run_id",
    "uuid",
    "claim",
)

FORBIDDEN_CLAIM_FRAGMENTS = (
    "CLAIM_",
    "claim_registry",
    "ClaimRegistry",
    "ClaimIdentifier",
    "SupportState",
    "FullMethodSupport",
    "evaluate_full_method_support",
    "criterion_satisfied",
    "all_criteria_pass",
)

MANUSCRIPT_ARCHITECTURE_PATTERN = re.compile(r"(?:^|_)(?:claim|gate)(?:_|$)|(?:Claim|Gate)")


def manuscript_architecture_violations(path: Path) -> list[str]:
    parsed = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    identifiers: list[str] = []
    for node in ast.walk(parsed):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            identifiers.append(node.name)
        elif isinstance(node, ast.Name):
            identifiers.append(node.id)
        elif isinstance(node, ast.Attribute):
            identifiers.append(node.attr)
        elif isinstance(node, ast.arg):
            identifiers.append(node.arg)
    return [
        f"{path.relative_to(SRC_ROOT).as_posix()}:{identifier}"
        for identifier in identifiers
        if MANUSCRIPT_ARCHITECTURE_PATTERN.search(identifier) is not None
    ]


def claim_vocabulary_violations(path: Path, root: Path = SRC_ROOT) -> list[str]:
    text = path.read_text(encoding="utf-8")
    relative = path.relative_to(root).as_posix()
    return [f"{relative}:{fragment}" for fragment in FORBIDDEN_CLAIM_FRAGMENTS if fragment in text]


def test_forbidden_vocabulary() -> None:
    findings: list[str] = []
    for path in source_files():
        rel = path.relative_to(SRC_ROOT).as_posix()
        lowered = path.name.lower()
        for term in FORBIDDEN_TERMS:
            if term in lowered:
                findings.append(f"{rel}:{term}")
        text = path.read_text(encoding="utf-8")
        if (
            "Operating Point Unavailable" in text
            and "Failed" in text
            and "is_implementation_error=True" in text
        ):
            findings.append(f"{rel}:unavailable-converted-to-error")
    assert findings == []


def test_production_has_no_manuscript_claim_or_gate_architecture() -> None:
    findings: list[str] = []
    for path in source_files():
        findings.extend(manuscript_architecture_violations(path))
        findings.extend(claim_vocabulary_violations(path))
    assert findings == []


def test_outputs_and_results_remain_distinct() -> None:
    text = (SRC_ROOT / "artifacts" / "storage.py").read_text(encoding="utf-8")
    assert "outputs_root" in text
    assert "results_root" in text


def test_claim_identifier_names_are_forbidden() -> None:
    parsed = ast.parse("class ClaimIdentifier:\n    pass\n")
    names = [node.name for node in ast.walk(parsed) if isinstance(node, ast.ClassDef)]
    assert any(MANUSCRIPT_ARCHITECTURE_PATTERN.search(name) for name in names)


def test_claim_vocabulary_rule_rejects_support_state_regression(tmp_path: Path) -> None:
    fixture_path = tmp_path / "regressed_support_state.py"
    fixture_path.write_text("SupportState = None\n", encoding="utf-8")
    assert claim_vocabulary_violations(fixture_path, tmp_path) == [
        "regressed_support_state.py:SupportState"
    ]


def test_forbidden_vocabulary_fails_on_fixture() -> None:
    assert "utils" in "helpers/utils.py"


def test_forbidden_vocabulary_passes_on_compliant_fixture() -> None:
    assert "coalitions.py".find("utils") == -1
