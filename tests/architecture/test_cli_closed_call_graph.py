from __future__ import annotations

import ast
from collections import defaultdict, deque
from pathlib import Path

from tests.architecture.ast_scans import SRC_ROOT, source_files

CLI_MODULE = "fedcampaign_emhi.cli"
RUNTIME_CALLBACK_CLASS_NAMES = frozenset({"FedAvgServerStrategy"})


def _module_name(path: Path) -> str:
    rel = path.relative_to(SRC_ROOT)
    if rel.name == "__init__.py":
        parent = rel.parent.as_posix()
        return (
            "fedcampaign_emhi" if parent == "." else "fedcampaign_emhi." + parent.replace("/", ".")
        )
    return "fedcampaign_emhi." + rel.as_posix()[:-3].replace("/", ".")


def _collect_functions() -> dict[str, tuple[str, int]]:
    functions: dict[str, tuple[str, int]] = {}
    for path in source_files():
        module = _module_name(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                functions[f"{module}.{node.name}"] = (module, node.lineno)
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                        functions[f"{module}.{node.name}.{item.name}"] = (module, item.lineno)
    return functions


def _cli_commands(functions: dict[str, tuple[str, int]]) -> set[str]:
    return {
        name
        for name in functions
        if name.startswith(f"{CLI_MODULE}.")
        and (name.endswith("_command") or name.rsplit(".", 1)[-1] == "main")
    }


def _resolve_name(
    name: str,
    current_module: str,
    current_class: str | None,
    imported_names: dict[str, str],
    functions: dict[str, tuple[str, int]],
) -> set[str]:
    found: set[str] = set()
    local = f"{current_module}.{name}"
    if local in functions:
        found.add(local)
    if current_class is not None:
        method = f"{current_module}.{current_class}.{name}"
        if method in functions:
            found.add(method)
    imported_target = imported_names.get(name)
    if imported_target in functions:
        found.add(imported_target)
    if imported_target is not None:
        nested = f"{imported_target}.{name}"
        if nested in functions:
            found.add(nested)
    return found


def _add_attr(
    owner: ast.AST,
    attr: str,
    caller: str,
    current_module: str,
    current_class: str | None,
    imported_names: dict[str, str],
    functions: dict[str, tuple[str, int]],
    classes: dict[str, str],
    simple: dict[str, set[str]],
    calls: dict[str, set[str]],
) -> None:
    candidates: set[str] = set()
    if isinstance(owner, ast.Name):
        if owner.id in {"self", "cls"} and current_class is not None:
            method = f"{current_module}.{current_class}.{attr}"
            if method in functions:
                candidates.add(method)
        imported_target = imported_names.get(owner.id)
        if imported_target is not None:
            direct = f"{imported_target}.{attr}"
            if direct in functions:
                candidates.add(direct)
        if owner.id in classes:
            method = f"{classes[owner.id]}.{attr}"
            if method in functions:
                candidates.add(method)
    if not candidates and len(simple[attr]) == 1:
        candidates.update(simple[attr])
    calls[caller].update(candidates)


def _external_import_names() -> dict[str, tuple[str, str]]:
    external: dict[str, tuple[str, str]] = {}
    for path in source_files():
        module = _module_name(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("fedcampaign_emhi"):
                    continue
                for alias in node.names:
                    external[alias.asname or alias.name] = (module, "imported")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("fedcampaign_emhi"):
                        continue
                    external[alias.asname or alias.name.split(".")[-1]] = (module, "imported")
    return external


def _base_root_identifier(base: ast.expr) -> str | None:
    if isinstance(base, ast.Name):
        return base.id
    if isinstance(base, ast.Attribute):
        value = base.value
        while isinstance(value, ast.Attribute):
            value = value.value
        if isinstance(value, ast.Name):
            return value.id
    return None


def _external_base_framework_methods(functions: dict[str, tuple[str, int]]) -> set[str]:
    external = _external_import_names()
    framework_methods: set[str] = set()
    for path in source_files():
        module = _module_name(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            has_external_base = any(
                (identifier := _base_root_identifier(base)) is not None and identifier in external
                for base in node.bases
            )
            is_runtime_callback = node.name in RUNTIME_CALLBACK_CLASS_NAMES
            if not (has_external_base or is_runtime_callback):
                continue
            for item in node.body:
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                    qname = f"{module}.{node.name}.{item.name}"
                    if qname in functions:
                        framework_methods.add(qname)
    return framework_methods


def _build_call_graph(functions: dict[str, tuple[str, int]]) -> dict[str, set[str]]:
    calls: dict[str, set[str]] = defaultdict(set)
    simple: dict[str, set[str]] = defaultdict(set)
    for qname in functions:
        simple[qname.rsplit(".", 1)[-1]].add(qname)
    classes: dict[str, str] = {}
    for qname in functions:
        parent = qname.rsplit(".", 1)[0]
        class_simple = parent.rsplit(".", 1)[-1]
        if f"{parent}.{qname.rsplit('.', 1)[-1]}" == qname and parent in {
            q.rsplit(".", 1)[0] for q in functions if q.rsplit(".", 1)[0].endswith(class_simple)
        }:
            classes[class_simple] = parent
    for qname in functions:
        parent = qname.rsplit(".", 1)[0]
        if any(other.startswith(parent + ".") and other != qname for other in functions):
            classes[parent.rsplit(".", 1)[-1]] = parent

    validator_methods: set[str] = set()
    for path in source_files():
        module = _module_name(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported: dict[str, str] = {}
        for node in tree.body:
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("fedcampaign_emhi")
            ):
                for alias in node.names:
                    imported[alias.asname or alias.name] = f"{node.module}.{alias.name}"
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("fedcampaign_emhi"):
                        imported[alias.asname or alias.name.split(".")[-1]] = alias.name

        bodies: list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, str, str | None]] = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                bodies.append((node, f"{module}.{node.name}", None))
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                        bodies.append((item, f"{module}.{node.name}.{item.name}", node.name))

        for fn, caller, current_class in bodies:
            for decorator in fn.decorator_list:
                func = decorator.func if isinstance(decorator, ast.Call) else decorator
                if isinstance(func, ast.Name) and func.id in {
                    "model_validator",
                    "field_validator",
                }:
                    validator_methods.add(caller)
                if isinstance(func, ast.Attribute) and func.attr in {
                    "model_validator",
                    "field_validator",
                }:
                    validator_methods.add(caller)
            for node in ast.walk(fn):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name):
                        calls[caller].update(
                            _resolve_name(func.id, module, current_class, imported, functions)
                        )
                        if func.id in classes:
                            init = f"{classes[func.id]}.__init__"
                            if init in functions:
                                calls[caller].add(init)
                        imported_target = imported.get(func.id)
                        if imported_target is not None:
                            init = f"{imported_target}.__init__"
                            if init in functions:
                                calls[caller].add(init)
                    elif isinstance(func, ast.Attribute):
                        _add_attr(
                            func.value,
                            func.attr,
                            caller,
                            module,
                            current_class,
                            imported,
                            functions,
                            classes,
                            simple,
                            calls,
                        )
                        if (
                            func.attr in {"getsource", "map"}
                            and node.args
                            and isinstance(node.args[0], ast.Name)
                        ):
                            calls[caller].update(
                                _resolve_name(
                                    node.args[0].id, module, current_class, imported, functions
                                )
                            )
                        if func.attr == "submit":
                            for keyword in node.keywords:
                                if keyword.arg == "fn" and isinstance(keyword.value, ast.Name):
                                    calls[caller].update(
                                        _resolve_name(
                                            keyword.value.id,
                                            module,
                                            current_class,
                                            imported,
                                            functions,
                                        )
                                    )
                        if func.attr == "Thread":
                            for keyword in node.keywords:
                                if keyword.arg == "target" and isinstance(keyword.value, ast.Name):
                                    calls[caller].update(
                                        _resolve_name(
                                            keyword.value.id,
                                            module,
                                            current_class,
                                            imported,
                                            functions,
                                        )
                                    )
                    elif isinstance(func, ast.Name) and func.id == "Thread":
                        for keyword in node.keywords:
                            if keyword.arg == "target" and isinstance(keyword.value, ast.Name):
                                calls[caller].update(
                                    _resolve_name(
                                        keyword.value.id,
                                        module,
                                        current_class,
                                        imported,
                                        functions,
                                    )
                                )
                elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                    _add_attr(
                        node.value,
                        node.attr,
                        caller,
                        module,
                        current_class,
                        imported,
                        functions,
                        classes,
                        simple,
                        calls,
                    )

    for loader in (name for name in functions if name.endswith("load_scientific_configuration")):
        calls[loader].update(validator_methods)
    return calls


def _reachable(roots: set[str], calls: dict[str, set[str]]) -> set[str]:
    seen: set[str] = set()
    pending: deque[str] = deque(roots)
    while pending:
        current = pending.popleft()
        if current in seen:
            continue
        seen.add(current)
        for callee in calls.get(current, ()):
            if callee not in seen:
                pending.append(callee)
    return seen


def test_cli_commands_reach_every_non_cli_production_method() -> None:
    functions = _collect_functions()
    cli_entries = _cli_commands(functions)
    calls = _build_call_graph(functions)
    framework_roots = _external_base_framework_methods(functions)
    reachable = _reachable(cli_entries | framework_roots, calls)
    non_cli = set(functions) - cli_entries
    unreachable = sorted(non_cli - reachable)
    assert cli_entries, "CLI command entry points must exist"
    assert len(reachable - cli_entries) == len(non_cli), (
        "CLI-reachable methods must equal all production methods other than CLI commands; "
        f"reachable={len(reachable - cli_entries)} global_non_cli={len(non_cli)} "
        f"unreachable={unreachable}"
    )
    assert unreachable == []
