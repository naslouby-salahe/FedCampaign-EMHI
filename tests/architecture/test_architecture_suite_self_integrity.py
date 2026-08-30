from __future__ import annotations

import ast
from pathlib import Path

SELF_FILE = "test_architecture_suite_self_integrity.py"
FORBIDDEN_EXCEPTION_IDENTIFIERS = frozenset(
    {
        "ALLOWLIST",
        "DEFAULT_ALLOWED",
        "DICT_BOUNDARY_ALLOWED_FILES",
        "FUNCTION_ALLOWLIST",
        "OBJECT_BOUNDARY_ALLOWED_FILES",
        "PACKAGE_PRIMITIVE_ALLOWLIST",
    }
)
NEGATIVE_TOKENS = frozenset({"fail", "reject", "detect", "forbidden", "violation"})
POSITIVE_TOKENS = frozenset({"pass", "accept", "clean", "compliant", "valid"})


def _test_names(tree: ast.Module) -> set[str]:
    return {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and node.name.startswith("test_")
    }


def _detector_names(tree: ast.Module) -> set[str]:
    return {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and not node.name.startswith("test_")
        and any(token in node.name for token in ("scan", "violation", "finding", "boundary"))
    }


def _contains_token(names: set[str], tokens: frozenset[str]) -> bool:
    return any(token in name for name in names for token in tokens)


def _suite_violations(repository_root: Path) -> list[str]:
    architecture_root = repository_root / "tests" / "architecture"
    violations: list[str] = []
    for source_file in sorted(architecture_root.glob("test_*.py")):
        if source_file.name == SELF_FILE:
            continue
        relative = source_file.relative_to(repository_root).as_posix()
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        forbidden = sorted(FORBIDDEN_EXCEPTION_IDENTIFIERS & names)
        violations.extend(f"{relative}: forbidden broad exception {name}" for name in forbidden)
        detectors = _detector_names(tree)
        tests = _test_names(tree)
        if detectors and not _contains_token(tests, NEGATIVE_TOKENS):
            violations.append(f"{relative}: detector has no adversarial canary")
        if detectors and not _contains_token(tests, POSITIVE_TOKENS):
            violations.append(f"{relative}: detector has no valid canary")
    return violations


def test_architecture_suite_is_fail_closed_and_self_testing(repo_root: Path) -> None:
    violations = _suite_violations(repo_root)
    assert not violations, "architecture suite self-integrity violations:\n" + "\n".join(violations)


def test_self_integrity_rejects_broad_exceptions_and_missing_canaries(tmp_path: Path) -> None:
    architecture_root = tmp_path / "tests" / "architecture"
    architecture_root.mkdir(parents=True)
    source = architecture_root / "test_bad_rule.py"
    source.write_text(
        "ALLOWLIST = frozenset()\n"
        "def boundary_violations() -> list[str]:\n"
        "    return []\n"
        "def test_rule_accepts_valid_case() -> None:\n"
        "    assert True\n",
        encoding="utf-8",
    )
    assert _suite_violations(tmp_path)


def test_self_integrity_accepts_exact_exemptions_with_both_canaries(tmp_path: Path) -> None:
    architecture_root = tmp_path / "tests" / "architecture"
    architecture_root.mkdir(parents=True)
    source = architecture_root / "test_good_rule.py"
    source.write_text(
        "EXACT_EXEMPTIONS = frozenset()\n"
        "def boundary_violations() -> list[str]:\n"
        "    return []\n"
        "def test_rule_rejects_forbidden_case() -> None:\n"
        "    assert True\n"
        "def test_rule_accepts_valid_case() -> None:\n"
        "    assert True\n",
        encoding="utf-8",
    )
    assert _suite_violations(tmp_path) == []
