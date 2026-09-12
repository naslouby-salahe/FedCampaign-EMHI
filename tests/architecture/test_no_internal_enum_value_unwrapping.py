from __future__ import annotations

from pathlib import Path

from tests.architecture.ast_scans import (
    enum_value_unwrapping_violations,
    parametrize_source_files,
)


@parametrize_source_files
def test_no_internal_enum_value_unwrapping(path: Path) -> None:
    assert enum_value_unwrapping_violations(path) == []


def test_enum_value_rule_rejects_computation_positions(tmp_path: Path) -> None:
    fixture = tmp_path / "consumer.py"
    fixture.write_text(
        "def select(method, methods):\n"
        "    if method.value == 'local':\n"
        "        return None\n"
        "    return sorted(methods, key=lambda item: item.value)\n"
        "def widen(method):\n"
        "    return int(method.value)\n"
        "def index(method, table):\n"
        "    return table[method.value]\n",
        encoding="utf-8",
    )
    assert enum_value_unwrapping_violations(fixture) == [
        "consumer.py:2: .value in comparison operand",
        "consumer.py:4: .value in 'key' key",
        "consumer.py:6: .value in int(...) operand",
        "consumer.py:8: .value in subscript index",
    ]


def test_enum_value_rule_accepts_serialization_and_path_rendering(tmp_path: Path) -> None:
    fixture = tmp_path / "renderer.py"
    fixture.write_text(
        "def payload(method, role, root):\n"
        "    return {'method': method.value}, f'{method.value}', [method.value], root / role.value\n",
        encoding="utf-8",
    )
    assert enum_value_unwrapping_violations(fixture) == []


def test_enum_value_rule_rejects_arithmetic_operand(tmp_path: Path) -> None:
    fixture = tmp_path / "consumer.py"
    fixture.write_text(
        "def offset(order, width):\n    return order.value * width\n",
        encoding="utf-8",
    )
    assert enum_value_unwrapping_violations(fixture) == [
        "consumer.py:2: .value in arithmetic operand"
    ]
