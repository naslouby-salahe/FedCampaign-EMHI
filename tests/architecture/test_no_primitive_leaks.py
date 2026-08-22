from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

import pytest
from tests.architecture.ast_scans import (
    LOCAL_LEAK_CONTAINER_NAMES,
    SRC_ROOT,
    annotation_primitives,
    field_annotations,
    is_dataclass,
    is_pydantic_model,
    iter_functions,
    local_annotations,
    module_ast,
    source_files,
    type_alias_annotations,
)


@dataclass(frozen=True, slots=True)
class AllowlistEntry:
    relative_path: str
    lineno: int
    symbol: str
    primitive: str


ALLOWLIST: frozenset[AllowlistEntry] = frozenset(
    {
        AllowlistEntry(
            "src/fedcampaign_emhi/config/validation.py",
            7,
            "YamlNode",
            "str",
        ),
        AllowlistEntry(
            "src/fedcampaign_emhi/config/validation.py",
            7,
            "YamlNode",
            "int",
        ),
        AllowlistEntry(
            "src/fedcampaign_emhi/config/validation.py",
            7,
            "YamlNode",
            "float",
        ),
        AllowlistEntry(
            "src/fedcampaign_emhi/cli/commands/doctor.py",
            12,
            "doctor_command",
            "str",
        ),
        AllowlistEntry(
            "src/fedcampaign_emhi/cli/commands/preprocess.py",
            9,
            "preprocess_command",
            "str",
        ),
        AllowlistEntry(
            "src/fedcampaign_emhi/cli/commands/preprocess.py",
            34,
            "_parse_dataset_name",
            "str",
        ),
        AllowlistEntry(
            "src/fedcampaign_emhi/cli/commands/status.py",
            10,
            "status_command",
            "str",
        ),
        AllowlistEntry(
            "src/fedcampaign_emhi/cli/commands/run.py",
            9,
            "run_command",
            "str",
        ),
        AllowlistEntry(
            "src/fedcampaign_emhi/cli/commands/report.py",
            12,
            "report_command",
            "str",
        ),
        AllowlistEntry(
            "src/fedcampaign_emhi/cli/main.py",
            21,
            "main",
            "str",
        ),
        AllowlistEntry(
            "src/fedcampaign_emhi/evaluation/smoke_gate.py",
            65,
            "_check",
            "list",
        ),
    }
)


def _record_parameter(
    findings: list[tuple[str, int, str, str, str]],
    rel: str,
    symbol: str,
    arg: ast.arg,
) -> None:
    for primitive in annotation_primitives(arg.annotation):
        findings.append((rel, arg.lineno, symbol, primitive, f"parameter '{arg.arg}'"))


def _scan_file(path: Path) -> list[tuple[str, int, str, str, str]]:
    tree = module_ast(path)
    findings: list[tuple[str, int, str, str, str]] = []
    rel = path.resolve().relative_to(SRC_ROOT.parent.parent).as_posix()
    for node, owner in iter_functions(tree, path):
        symbol = f"{owner}.{node.name}" if owner else node.name
        for arg in node.args.args + node.args.kwonlyargs + node.args.posonlyargs:
            _record_parameter(findings, rel, symbol, arg)
        for vararg in (node.args.vararg, node.args.kwarg):
            if vararg is not None:
                _record_parameter(findings, rel, symbol, vararg)
        if node.returns is not None:
            for primitive in annotation_primitives(node.returns):
                findings.append((rel, node.lineno, symbol, primitive, "return type"))
        for local_name, annotation, lineno in local_annotations(node):
            for primitive in annotation_primitives(
                annotation, leak_containers=LOCAL_LEAK_CONTAINER_NAMES
            ):
                findings.append((rel, lineno, symbol, primitive, f"local '{local_name}'"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if not (is_dataclass(node) or is_pydantic_model(node)):
            continue
        for field_name, annotation in field_annotations(node):
            for primitive in annotation_primitives(annotation):
                findings.append(
                    (rel, annotation.lineno, node.name, primitive, f"field '{field_name}'")
                )
    for alias_name, annotation, lineno in type_alias_annotations(tree):
        for primitive in annotation_primitives(annotation):
            findings.append((rel, lineno, alias_name, primitive, "type alias"))
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            for primitive in annotation_primitives(node.annotation):
                findings.append((rel, node.lineno, node.target.id, primitive, "module annotation"))
    return findings


def _report(findings: list[tuple[str, int, str, str, str]]) -> str:
    lines = ["primitive leak findings (file:line symbol primitive context):"]
    for rel, lineno, symbol, primitive, context in sorted(findings):
        lines.append(f"  {rel}:{lineno} {symbol} {primitive} ({context})")
    return "\n".join(lines)


@pytest.mark.parametrize("path", source_files(), ids=lambda p: p.relative_to(SRC_ROOT).as_posix())
def test_no_primitive_leaks(path: Path) -> None:
    findings = _scan_file(path)
    allowed = {
        (entry.relative_path, entry.lineno, entry.symbol, entry.primitive) for entry in ALLOWLIST
    }
    unjustified: list[tuple[str, int, str, str, str]] = []
    for finding in findings:
        rel, lineno, symbol, primitive, _context = finding
        if rel == "src/fedcampaign_emhi/config/validation.py":
            continue
        if rel.startswith("src/fedcampaign_emhi/cli/") and primitive == "str":
            continue
        if (rel, lineno, symbol, primitive) in allowed:
            continue
        unjustified.append(finding)
    assert not unjustified, _report(unjustified)


def test_no_primitive_leaks_fails_on_fixture() -> None:
    tree = ast.parse(
        "\n".join(
            (
                "from dataclasses import dataclass",
                "from typing import Any",
                "",
                "@dataclass",
                "class Hidden:",
                "    name: str",
                "    payload: dict[str, int]",
                "    extra: Any",
                "",
                "def work(count: int) -> list[str]:",
                "    return []",
            )
        )
    )
    findings: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for _field_name, annotation in field_annotations(node):
                findings.extend(annotation_primitives(annotation))
        if isinstance(node, ast.FunctionDef):
            for arg in node.args.args:
                findings.extend(annotation_primitives(arg.annotation))
            findings.extend(annotation_primitives(node.returns))
    assert "str" in findings
    assert "dict" in findings
    assert "int" in findings
    assert "Any" in findings
    assert "list" in findings


def test_no_primitive_leaks_passes_on_compliant_fixture() -> None:
    tree = ast.parse(
        "\n".join(
            (
                "from fedcampaign_emhi.domain.types import ClientCount",
                "",
                "def coalition_size(client_count: ClientCount) -> ClientCount:",
                "    return client_count",
            )
        )
    )
    findings: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for arg in node.args.args:
                findings.extend(annotation_primitives(arg.annotation))
            findings.extend(annotation_primitives(node.returns))
    assert findings == []
