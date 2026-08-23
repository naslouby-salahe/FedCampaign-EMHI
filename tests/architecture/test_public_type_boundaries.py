from __future__ import annotations

import ast
from pathlib import Path

from tests.architecture.ast_scans import (
    SRC_ROOT,
    annotation_primitives,
    iter_functions,
    module_ast,
    parametrize_source_files,
)

PUBLIC_PACKAGES = frozenset(
    {
        "domain",
        "config",
        "experiments",
        "evaluation",
        "analysis",
        "artifacts",
        "execution",
        "runtime",
        "reporting",
    }
)


def _public_functions(path: Path) -> list[ast.FunctionDef]:
    tree = module_ast(path)
    functions: list[ast.FunctionDef] = []
    for node, owner in iter_functions(tree):
        if node.name.startswith("_"):
            continue
        if owner is not None and owner.split(".")[-1].startswith("_"):
            continue
        functions.append(node)
    return functions


@parametrize_source_files
def test_public_type_boundaries(path: Path) -> None:
    rel = path.relative_to(SRC_ROOT).as_posix()
    package = rel.split("/")[0]
    if package not in PUBLIC_PACKAGES:
        return
    if package == "cli":
        return
    findings: list[str] = []
    for function in _public_functions(path):
        for arg in function.args.args:
            if arg.arg in {"self", "cls"}:
                continue
            primitives = annotation_primitives(arg.annotation)
            if primitives:
                findings.append(f"{rel}:{arg.lineno} {function.name}({arg.arg}) {primitives}")
        if function.returns is not None:
            primitives = annotation_primitives(function.returns)
            if primitives:
                findings.append(f"{rel}:{function.lineno} {function.name} return {primitives}")
    assert findings == []


def test_public_type_boundaries_fails_on_fixture() -> None:
    tree = ast.parse("def load(name: str) -> dict:\n    return {}\n")
    function = tree.body[0]
    assert isinstance(function, ast.FunctionDef)
    assert annotation_primitives(function.args.args[0].annotation)
    assert annotation_primitives(function.returns)


def test_public_type_boundaries_passes_on_compliant_fixture() -> None:
    tree = ast.parse(
        "from fedcampaign_emhi.domain.enums import ExperimentName\n"
        "def resolve(name: ExperimentName) -> ExperimentName:\n    return name\n"
    )
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef))
    assert annotation_primitives(function.args.args[0].annotation) == []
    assert annotation_primitives(function.returns) == []
