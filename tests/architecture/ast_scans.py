from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src" / "fedcampaign_emhi"
CANONICAL_TYPES_FILE = SRC_ROOT / "domain" / "types.py"
DOMAIN_TYPES_FILE = CANONICAL_TYPES_FILE
PRIMITIVE_NAMES = frozenset({"str", "int", "float", "bool", "object", "Any", "bytes"})
LEAK_CONTAINER_NAMES = frozenset({"dict", "list", "set", "Dict", "List", "Set"})
LOCAL_LEAK_CONTAINER_NAMES = frozenset({"dict", "Dict"})
BOUNDARY_TYPE_NAMES = frozenset({"YamlNode"})
LAYERS = (
    "cli",
    "reporting",
    "execution",
    "analysis",
    "evaluation",
    "experiments",
    "comparators",
    "synthetic",
    "detection",
    "emhi",
    "datasets",
    "models",
    "artifacts",
    "runtime",
    "config",
    "domain",
)


def annotation_primitives(
    node: ast.expr | None, *, leak_containers: frozenset[str] = LEAK_CONTAINER_NAMES
) -> list[str]:
    if node is None:
        return []
    if references_boundary_type(node):
        return []
    if isinstance(node, ast.Name):
        if node.id in PRIMITIVE_NAMES or node.id in leak_containers:
            return [node.id]
        return []
    if isinstance(node, ast.Attribute):
        attr = node.attr
        if attr in PRIMITIVE_NAMES or attr in leak_containers:
            return [f"typing.{attr}"]
        return []
    if isinstance(node, ast.Subscript):
        if isinstance(node.value, ast.Name) and node.value.id == "Literal":
            return []
        if isinstance(node.value, ast.Name) and node.value.id == "Annotated":
            slice_node = node.slice
            annotated_type = slice_node.elts[0] if isinstance(slice_node, ast.Tuple) else slice_node
            return annotation_primitives(annotated_type, leak_containers=leak_containers)
        container = node.value.id if isinstance(node.value, ast.Name) else None
        found: list[str] = []
        if container in leak_containers or container in PRIMITIVE_NAMES:
            found.append(container)
        slice_node = node.slice
        parts: list[ast.expr] = (
            list(slice_node.elts) if isinstance(slice_node, ast.Tuple) else [slice_node]
        )
        for part in parts:
            found.extend(annotation_primitives(part, leak_containers=leak_containers))
        return found
    if isinstance(node, ast.BinOp):
        return annotation_primitives(node.left, leak_containers=leak_containers) + (
            annotation_primitives(node.right, leak_containers=leak_containers)
        )
    if isinstance(node, ast.Tuple):
        found: list[str] = []
        for elt in node.elts:
            found.extend(annotation_primitives(elt, leak_containers=leak_containers))
        return found
    if isinstance(node, ast.List):
        found: list[str] = []
        for elt in node.elts:
            found.extend(annotation_primitives(elt, leak_containers=leak_containers))
        return found
    return []


def references_boundary_type(node: ast.AST) -> bool:
    return any(
        isinstance(child, ast.Name) and child.id in BOUNDARY_TYPE_NAMES for child in ast.walk(node)
    )


def python_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(root.rglob("*.py")))


def source_files() -> tuple[Path, ...]:
    return python_files(SRC_ROOT)


parametrize_source_files = pytest.mark.parametrize(
    "path", source_files(), ids=lambda p: p.relative_to(SRC_ROOT).as_posix()
)


def architecture_test_paths() -> tuple[Path, ...]:
    return python_files(REPO_ROOT / "tests")


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def module_ast(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def iter_functions(tree: ast.Module) -> list[tuple[ast.FunctionDef, str | None]]:
    functions: list[tuple[ast.FunctionDef, str | None]] = []

    def _collect(nodes: list[ast.stmt], owner: str | None) -> None:
        for node in nodes:
            if isinstance(node, ast.FunctionDef):
                functions.append((node, owner))
                nested_owner = f"{owner}.{node.name}" if owner else node.name
                _collect(node.body, nested_owner)
            elif isinstance(node, ast.ClassDef):
                class_owner = f"{owner}.{node.name}" if owner else node.name
                _collect(node.body, class_owner)

    _collect(tree.body, None)
    return functions


def local_annotations(func: ast.FunctionDef) -> list[tuple[str, ast.expr, int]]:
    found: list[tuple[str, ast.expr, int]] = []

    def _visit(nodes: list[ast.stmt]) -> None:
        for node in nodes:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                continue
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                found.append((node.target.id, node.annotation, node.lineno))
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.stmt) and not isinstance(
                    child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
                ):
                    _visit([child])

    _visit(func.body)
    return found


def is_dataclass(class_node: ast.ClassDef) -> bool:
    for decorator in class_node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
            return True
        if (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Name)
            and decorator.func.id == "dataclass"
        ):
            return True
    return False


def is_pydantic_model(class_node: ast.ClassDef) -> bool:
    for base in class_node.bases:
        if isinstance(base, ast.Name) and base.id in {"BaseModel", "FrozenConfigModel"}:
            return True
        if isinstance(base, ast.Attribute) and base.attr in {"BaseModel", "FrozenConfigModel"}:
            return True
    return False


def field_annotations(class_node: ast.ClassDef) -> list[tuple[str, ast.expr]]:
    fields: list[tuple[str, ast.expr]] = []
    for item in class_node.body:
        if (
            isinstance(item, ast.AnnAssign)
            and isinstance(item.target, ast.Name)
            and not item.target.id.startswith("_")
        ):
            fields.append((item.target.id, item.annotation))
    return fields


def type_alias_annotations(tree: ast.Module) -> list[tuple[str, ast.expr, int]]:
    aliases: list[tuple[str, ast.expr, int]] = []
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Name | ast.Attribute | ast.Subscript | ast.BinOp)
        ):
            aliases.append((node.targets[0].id, node.value, node.lineno))
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and isinstance(node.annotation, ast.Name)
            and node.annotation.id == "TypeAlias"
            and node.value is not None
        ):
            aliases.append((node.target.id, node.value, node.lineno))
        if isinstance(node, ast.TypeAlias):
            aliases.append((node.name.id, node.value, node.lineno))
    return aliases


def class_attribute_annotations(tree: ast.Module) -> list[tuple[str, ast.expr, int]]:
    found: list[tuple[str, ast.expr, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                found.append((node.name, item.annotation, item.lineno))
    return found


def bare_literal_only_names(tree: ast.Module) -> set[str]:
    bare_occurrences: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Tuple | ast.List | ast.Set):
            for elt in node.elts:
                if isinstance(elt, ast.Name):
                    bare_occurrences[elt.id] = bare_occurrences.get(elt.id, 0) + 1
    load_occurrences: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            load_occurrences[node.id] = load_occurrences.get(node.id, 0) + 1
    return {
        name for name, count in bare_occurrences.items() if load_occurrences.get(name, 0) == count
    }


def package_of(rel: str) -> str:
    if "/" not in rel:
        return Path(rel).stem
    return rel.split("/")[0]


def domain_type_names() -> frozenset[str]:
    tree = module_ast(DOMAIN_TYPES_FILE)
    names: set[str] = set()
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            target = node.targets[0]
            if not target.id[:1].isupper():
                continue
            value = node.value
            if isinstance(value, ast.Subscript) and isinstance(value.value, ast.Name):
                if value.value.id == "Annotated":
                    names.add(target.id)
            elif isinstance(value, ast.Name):
                names.add(target.id)
    return frozenset(names)


def _domain_annotation(node: ast.expr | None, domain_names: frozenset[str]) -> bool:
    if node is None:
        return False
    if isinstance(node, ast.Name):
        return node.id in domain_names
    if isinstance(node, ast.Attribute):
        return node.attr in domain_names
    if isinstance(node, ast.Subscript):
        container = node.value.id if isinstance(node.value, ast.Name) else None
        if container in _DOMAIN_CONTAINER_NAMES:
            return False
        if isinstance(node.value, ast.Name) and node.value.id == "Annotated":
            sl = node.slice
            inner = sl.elts[0] if isinstance(sl, ast.Tuple) else sl
            return _domain_annotation(inner, domain_names)
        return _domain_annotation(node.value, domain_names) or any(
            _domain_annotation(p, domain_names)
            for p in ([] if not isinstance(node.slice, ast.Tuple) else list(node.slice.elts))
        )
    if isinstance(node, ast.BinOp):
        return _domain_annotation(node.left, domain_names) or _domain_annotation(
            node.right, domain_names
        )
    if isinstance(node, ast.Tuple):
        return any(_domain_annotation(e, domain_names) for e in node.elts)
    return False


_DOMAIN_CONTAINER_NAMES = frozenset(
    {
        "tuple",
        "list",
        "set",
        "dict",
        "frozenset",
        "Sequence",
        "Mapping",
        "MutableMapping",
        "Iterable",
        "Iterator",
        "UserDict",
        "OrderedDict",
        "NDArray",
        "Deque",
    }
)


def domain_bound_names(tree: ast.Module) -> set[str]:
    domain_names = domain_type_names()
    bound: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            for arg in node.args.args + node.args.kwonlyargs + node.args.posonlyargs:
                if _domain_annotation(arg.annotation, domain_names):
                    bound.add(arg.arg)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if _domain_annotation(node.annotation, domain_names):
                bound.add(node.target.id)
    return bound


def redundant_domain_conversion_violations(path: Path) -> list[str]:
    tree = module_ast(path)
    relative = path.relative_to(SRC_ROOT).as_posix() if path.is_relative_to(SRC_ROOT) else path.name
    bound = domain_bound_names(tree)
    violations: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in {"int", "float", "str", "bool"}
            and len(node.args) == 1
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id in bound
        ):
            violations.append(f"{relative}:{node.lineno}: {node.func.id}({node.args[0].id})")
    return sorted(violations)


def production_python_files_via_walk() -> tuple[Path, ...]:
    found: set[Path] = set()
    for current, dirs, files in os.walk(SRC_ROOT):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in files:
            if name.endswith(".py"):
                found.add(Path(current) / name)
    return tuple(sorted(found))
