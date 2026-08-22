from __future__ import annotations

from tests.architecture.ast_scans import SRC_ROOT, source_files

FORBIDDEN_TERMS = (
    "utils",
    "helpers",
    "manager",
    "processor",
    "wrapper",
    "shim",
    "compat",
    "legacy",
    "v2",
    "final2",
    "ton_iot_network_v2",
    "run_id",
    "uuid",
)


def test_canonical_vocabulary() -> None:
    findings: list[str] = []
    for path in source_files():
        rel = path.relative_to(SRC_ROOT).as_posix()
        lowered = path.name.lower()
        for term in FORBIDDEN_TERMS:
            if term in lowered:
                findings.append(f"{rel}:{term}")
        text = path.read_text(encoding="utf-8")
        if (
            "Operating Point Unavailable" in text
            and "Failed" in text
            and "is_implementation_error=True" in text
        ):
            findings.append(f"{rel}:unavailable-converted-to-error")
    assert findings == []


def test_outputs_and_results_remain_distinct() -> None:
    text = (SRC_ROOT / "artifacts" / "paths.py").read_text(encoding="utf-8")
    assert "outputs_root" in text
    assert "results_root" in text


def test_canonical_vocabulary_fails_on_fixture() -> None:
    assert "utils" in "helpers/utils.py"


def test_canonical_vocabulary_passes_on_compliant_fixture() -> None:
    assert "coalitions.py".find("utils") == -1
