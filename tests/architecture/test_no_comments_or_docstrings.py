import ast
from pathlib import Path

from tests.architecture.test_repository_structure import REQUIRED_SOURCE_FILES


def python_files(root: Path) -> list[Path]:
    files = [root / relative for relative in REQUIRED_SOURCE_FILES]
    files.extend(sorted((root / "tests").rglob("*.py")))
    return files


def comment_or_docstring_violations(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            docstring = ast.get_docstring(node, clean=False)
            if docstring:
                violations.append(f"{path}:{getattr(node, 'lineno', 1)}:docstring")
    for index, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            violations.append(f"{path}:{index}:comment")
    return violations


def test_no_comments_or_docstrings(repo_root: Path) -> None:
    violations: list[str] = []
    for path in python_files(repo_root):
        if path.is_file():
            violations.extend(comment_or_docstring_violations(path))
    assert violations == []


def test_no_comments_or_docstrings_fails_on_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "bad.py"
    fixture.write_text('"""module docstring"""\n# comment\nvalue = 1\n', encoding="utf-8")
    assert comment_or_docstring_violations(fixture)


def test_no_comments_or_docstrings_passes_on_compliant_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "good.py"
    fixture.write_text("value = 1\n", encoding="utf-8")
    assert comment_or_docstring_violations(fixture) == []
