from __future__ import annotations

import ast
from pathlib import Path

import pytest
from tests.architecture.ast_scans import (
    CANONICAL_TYPES_FILE,
    LOCAL_LEAK_CONTAINER_NAMES,
    SRC_ROOT,
    annotation_primitives,
    class_attribute_annotations,
    domain_bound_names,
    field_annotations,
    is_dataclass,
    is_pydantic_model,
    iter_functions,
    local_annotations,
    module_ast,
    parametrize_source_files,
    type_alias_annotations,
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
    for node, owner in iter_functions(tree):
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
    bound_domain_names = domain_bound_names(tree)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "cast"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Name)
            and node.args[1].id in bound_domain_names
        ):
            for primitive in annotation_primitives(node.args[0]):
                findings.append((rel, node.lineno, "cast", primitive, f"cast '{node.args[1].id}'"))
    for owner, annotation, lineno in class_attribute_annotations(tree):
        for primitive in annotation_primitives(annotation):
            findings.append((rel, lineno, owner, primitive, "class attribute"))
    return findings


def _report(findings: list[tuple[str, int, str, str, str]]) -> str:
    lines = ["primitive leak findings (file:line symbol primitive context):"]
    for rel, lineno, symbol, primitive, context in sorted(findings):
        lines.append(f"  {rel}:{lineno} {symbol} {primitive} ({context})")
    return "\n".join(lines)


@parametrize_source_files
def test_no_primitive_leaks(path: Path) -> None:
    if path == CANONICAL_TYPES_FILE:
        pytest.skip("canonical types module is exempt from the primitive-leak policy")
    findings = _scan_file(path)
    assert not findings, _report(findings)


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


def test_no_primitive_leaks_rejects_annotated_bypass() -> None:
    tree = ast.parse(
        "from typing import Annotated\n"
        "def work(count: Annotated[int, 'positive']) -> Annotated[float, 'rate']: ...\n"
    )
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef))
    assert annotation_primitives(function.args.args[0].annotation) == ["int"]
    assert annotation_primitives(function.returns) == ["float"]


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
