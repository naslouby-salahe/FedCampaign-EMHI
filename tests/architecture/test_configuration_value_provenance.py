from __future__ import annotations

import ast
import re
from collections.abc import Iterator
from typing import cast

import pytest
import yaml
from tests.architecture.ast_scans import REPO_ROOT, SRC_ROOT, module_ast, source_files

CONFIGURATION_AUTHORITY_PATHS = frozenset(
    {
        "config/loading.py",
        "config/schema.py",
        "config/validation.py",
    }
)
SAFE_NUMERIC_LITERALS = frozenset({-1, 0, 1})
TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9]*")
GOVERNED_POLICY_TOKENS = frozenset(
    {
        "alpha",
        "bootstrap",
        "candidate",
        "confidence",
        "minimum",
        "maximum",
        "pfa",
        "replicates",
        "threshold",
        "tolerance",
    }
)


def configuration_value_index(payload: str) -> dict[str, frozenset[str]]:
    loaded = cast(object, yaml.safe_load(payload))
    paths_by_value: dict[str, set[str]] = {}

    def walk(value: object, path: tuple[str, ...]) -> None:
        if isinstance(value, bool):
            return
        if isinstance(value, (int, float)):
            if value not in SAFE_NUMERIC_LITERALS:
                paths_by_value.setdefault(repr(value), set()).add(".".join(path))
            return
        if isinstance(value, dict):
            for key, child in cast(dict[object, object], value).items():
                walk(child, (*path, str(key)))
            return
        if isinstance(value, list):
            for child in cast(list[object], value):
                walk(child, path)

    walk(loaded, ())
    return {value: frozenset(paths) for value, paths in paths_by_value.items()}


def name_tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for raw in TOKEN_PATTERN.findall(text):
        tokens.update(
            token
            for token in re.sub(r"(?<!^)(?=[A-Z])", "_", raw).lower().split("_")
            if len(token) > 2
        )
    return tokens


def _numeric_value(node: ast.AST) -> int | float | None:
    if isinstance(node, ast.Constant) and not isinstance(node.value, bool):
        if isinstance(node.value, (int, float)):
            return node.value
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub)
        and isinstance(node.operand, ast.Constant)
        and isinstance(node.operand.value, int | float)
        and not isinstance(node.operand.value, bool)
    ):
        return -node.operand.value
    return None


def _numeric_nodes(tree: ast.Module) -> Iterator[ast.AST]:
    parents = _parents(tree)
    for node in ast.walk(tree):
        if _numeric_value(node) is None:
            continue
        if isinstance(node, ast.Constant):
            parent = parents.get(node)
            if isinstance(parent, ast.UnaryOp) and isinstance(parent.op, ast.USub):
                continue
        yield node


def _parents(tree: ast.Module) -> dict[ast.AST, ast.AST]:
    return {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}


def _context_tokens(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> set[str]:
    current = node
    context: ast.AST = node
    while current in parents:
        current = parents[current]
        context = current
        if isinstance(current, (ast.Assign, ast.AnnAssign, ast.Call, ast.Compare, ast.FunctionDef)):
            break
    names: list[str] = []
    for child in ast.walk(context):
        if isinstance(child, ast.Name):
            names.append(child.id)
        elif isinstance(child, ast.Attribute):
            names.append(child.attr)
        elif isinstance(child, ast.keyword) and child.arg is not None:
            names.append(child.arg)
    return name_tokens(" ".join(names))


def _is_function_default(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, ast.FunctionDef | ast.AsyncFunctionDef):
            defaults = [*current.args.defaults, *current.args.kw_defaults]
            return any(default is not None and node in ast.walk(default) for default in defaults)
    return False


def _is_policy_bearing_literal(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, ast.keyword):
            return current.arg is not None
        if isinstance(current, ast.AnnAssign | ast.Assign):
            return True
        if isinstance(current, ast.FunctionDef | ast.AsyncFunctionDef):
            return False
    return False


def _violations_for_tree(
    tree: ast.Module, relative_path: str, configured_values: dict[str, frozenset[str]]
) -> list[str]:
    if relative_path in CONFIGURATION_AUTHORITY_PATHS:
        return []
    parents = _parents(tree)
    violations: list[str] = []
    for node in _numeric_nodes(tree):
        value = _numeric_value(node)
        if value is None or value in SAFE_NUMERIC_LITERALS:
            continue
        paths = configured_values.get(repr(value), frozenset())
        if not paths:
            continue
        if _is_function_default(node, parents):
            violations.append(
                f"{relative_path}:{getattr(node, 'lineno', 0)}: configured literal {value!r} "
                "is a function default"
            )
            continue
        if not _is_policy_bearing_literal(node, parents):
            continue
        path_tokens = {token for path in paths for token in name_tokens(path)}
        overlap = _context_tokens(node, parents) & path_tokens
        if overlap & GOVERNED_POLICY_TOKENS:
            violations.append(
                f"{relative_path}:{getattr(node, 'lineno', 0)}: configured literal {value!r} duplicates "
                f"{sorted(paths)} via {sorted(overlap)}"
            )
    return violations


def test_governed_values_are_read_from_typed_configuration() -> None:
    payload = (REPO_ROOT / "configs" / "fedcampaign-emhi.yaml").read_text(encoding="utf-8")
    configured_values = configuration_value_index(payload)
    violations = [
        violation
        for path in source_files()
        for violation in _violations_for_tree(
            module_ast(path), path.relative_to(SRC_ROOT).as_posix(), configured_values
        )
    ]
    assert not violations, "hardcoded configured values:\n" + "\n".join(violations)


@pytest.mark.parametrize(
    "snippet",
    [
        "bootstrap_replicates = 10000\n",
        "def bootstrap(replicates: int = 10000) -> None:\n    pass\n",
        "def run() -> None:\n    target_pfa = 0.05\n",
    ],
)
def test_configuration_provenance_rejects_known_literal_bypasses(snippet: str) -> None:
    payload = (REPO_ROOT / "configs" / "fedcampaign-emhi.yaml").read_text(encoding="utf-8")
    assert _violations_for_tree(
        ast.parse(snippet), "evaluation/example.py", configuration_value_index(payload)
    )


def test_configuration_provenance_accepts_structural_literals() -> None:
    assert (
        _violations_for_tree(
            ast.parse("def index(value: int) -> int:\n    return value + 1\n"),
            "evaluation/example.py",
            configuration_value_index(
                (REPO_ROOT / "configs" / "fedcampaign-emhi.yaml").read_text(encoding="utf-8")
            ),
        )
        == []
    )
