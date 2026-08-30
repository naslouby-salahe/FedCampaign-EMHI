from __future__ import annotations

import ast
from pathlib import Path

import pytest
from tests.architecture.ast_scans import SRC_ROOT, module_ast, source_files


def _public_annotation_violations(module_name: str, tree: ast.Module) -> list[str]:
    violations: list[str] = []
    candidates: list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            candidates.append((module_name, node))
        elif isinstance(node, ast.ClassDef):
            candidates.extend(
                (f"{module_name}.{node.name}", method)
                for method in node.body
                if isinstance(method, ast.FunctionDef | ast.AsyncFunctionDef)
            )
    for owner, function in candidates:
        if function.name.startswith("_"):
            continue
        positional = [*function.args.posonlyargs, *function.args.args]
        if positional and positional[0].arg in {"self", "cls"}:
            positional = positional[1:]
        arguments = [*positional, *function.args.kwonlyargs]
        if function.args.vararg is not None:
            arguments.append(function.args.vararg)
        if function.args.kwarg is not None:
            arguments.append(function.args.kwarg)
        symbol = f"{owner}.{function.name}"
        for argument in arguments:
            if argument.annotation is None:
                violations.append(f"{symbol}:{argument.lineno}: unannotated {argument.arg}")
        if function.returns is None:
            violations.append(f"{symbol}:{function.lineno}: missing return annotation")
    return violations


def _file_violations(path: Path) -> list[str]:
    module = path.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
    return _public_annotation_violations(module, module_ast(path))


def test_every_public_callable_boundary_is_fully_annotated() -> None:
    violations = [violation for path in source_files() for violation in _file_violations(path)]
    assert violations == []


@pytest.mark.parametrize(
    "snippet",
    [
        "def expose(value) -> None:\n    return None\n",
        "def expose(value: int):\n    return value\n",
        "class Port:\n    def load(self, value) -> None:\n        return None\n",
        "def expose(*values, **options) -> None:\n    return None\n",
    ],
)
def test_public_annotation_rule_rejects_missing_annotations(snippet: str) -> None:
    assert _public_annotation_violations("example", ast.parse(snippet))


def test_public_annotation_rule_accepts_complete_annotations() -> None:
    tree = ast.parse(
        "class Port:\n"
        "    def load(self, value: int) -> int:\n"
        "        return value\n"
        "\n"
        "def expose(value: str, /, *, enabled: bool) -> str:\n"
        "    return value\n"
    )
    assert _public_annotation_violations("example", tree) == []
