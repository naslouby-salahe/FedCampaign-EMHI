from pathlib import Path

FORBIDDEN_MARKERS = ("TODO", "FIXME", "HACK", "XXX")


def temporary_code_violations(path: Path) -> list[str]:
    violations: list[str] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        for marker in FORBIDDEN_MARKERS:
            if marker in line:
                violations.append(f"{path}:{index}:{marker}")
    return violations


def test_no_todos_or_temporary_code(repo_root: Path) -> None:
    violations: list[str] = []
    for directory in (repo_root / "src",):
        for path in directory.rglob("*.py"):
            violations.extend(temporary_code_violations(path))
    assert violations == []


def test_no_todos_or_temporary_code_fails_on_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "bad.py"
    fixture.write_text("value = 1  # TODO finish\n", encoding="utf-8")
    assert temporary_code_violations(fixture)


def test_no_todos_or_temporary_code_passes_on_compliant_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "good.py"
    fixture.write_text("value = 1\n", encoding="utf-8")
    assert temporary_code_violations(fixture) == []
