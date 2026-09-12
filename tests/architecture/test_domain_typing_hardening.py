from __future__ import annotations

import ast
from pathlib import Path

import pytest
from tests.architecture.ast_scans import (
    SRC_ROOT,
    annotation_primitives,
    domain_bound_names,
    production_python_files_via_walk,
    redundant_conversion_violations_for_fields,
    redundant_domain_conversion_violations,
    scalar_domain_field_primitives,
    source_files,
)


def test_every_production_source_file_is_scanned() -> None:
    discovered = source_files()
    assert discovered, "source discovery returned no production files"
    assert set(discovered) == set(production_python_files_via_walk())
    assert len(discovered) == len(production_python_files_via_walk())


@pytest.mark.parametrize("path", source_files(), ids=lambda p: p.relative_to(SRC_ROOT).as_posix())
def test_no_redundant_domain_conversion(path: Path) -> None:
    assert redundant_domain_conversion_violations(path) == []


def test_no_redundant_domain_conversion_fails_on_fixture(tmp_path: Path) -> None:
    path = tmp_path / "consumer.py"
    path.write_text(
        "from fedcampaign_emhi.domain.types import ClientCount, ThresholdValue\n"
        "def run(client_count: ClientCount, threshold: ThresholdValue) -> None:\n"
        "    print(int(client_count), float(threshold))\n",
        encoding="utf-8",
    )
    violations = redundant_domain_conversion_violations(path)
    assert violations == [
        "consumer.py:3: float(threshold)",
        "consumer.py:3: int(client_count)",
    ]


def test_no_redundant_domain_conversion_allows_boundary_conversion(
    tmp_path: Path,
) -> None:
    path = tmp_path / "consumer.py"
    path.write_text(
        "import duckdb\n"
        "from fedcampaign_emhi.domain.types import RecordCount\n"
        "def count(connection: duckdb.DuckDBPyConnection, statement: str) -> RecordCount:\n"
        "    row = connection.execute(statement).fetchone()\n"
        "    return int(row[0])\n",
        encoding="utf-8",
    )
    assert redundant_domain_conversion_violations(path) == []


def test_cast_churn_rule_rejects_narrowing_domain_value(tmp_path: Path) -> None:
    tree = ast.parse(
        "from typing import cast\n"
        "from fedcampaign_emhi.domain.types import ClientCount\n"
        "def count(value: ClientCount) -> int:\n"
        "    return cast(int, value)\n"
    )
    bound = domain_bound_names(tree)
    assert "value" in bound
    cast_call = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "cast"
    )
    cast_arg = cast_call.args[1]
    assert isinstance(cast_arg, ast.Name)
    assert cast_arg.id in bound
    assert annotation_primitives(cast_call.args[0]) == ["int"]


def test_boundary_yaml_node_alias_is_allowed(tmp_path: Path) -> None:
    tree = ast.parse(
        "type YamlNode = str | int | float | Sequence[YamlNode] | Mapping[str, YamlNode] | None\n"
    )
    alias = tree.body[0]
    assert isinstance(alias, ast.TypeAlias)
    assert annotation_primitives(alias.value) == []


def test_no_redundant_domain_conversion_rejects_unwrapped_model_field() -> None:
    tree = ast.parse(
        "def order(items):\n    return tuple(int(summary.seed) for summary in items)\n"
    )
    violations = redundant_conversion_violations_for_fields(
        tree, "consumer.py", {"seed": frozenset({"int"})}
    )
    assert violations == ["consumer.py:2: int(summary.seed)"]


def test_no_redundant_domain_conversion_accepts_foreign_model_field() -> None:
    tree = ast.parse(
        "def order(items):\n"
        "    return tuple(float(summary.paired_difference) for summary in items)\n"
    )
    violations = redundant_conversion_violations_for_fields(
        tree, "consumer.py", {"seed": frozenset({"int"})}
    )
    assert violations == []


def test_ambiguous_domain_field_names_are_excluded_from_the_field_map() -> None:
    field_primitives = scalar_domain_field_primitives()
    assert field_primitives.get("seed") == frozenset({"int"})
    assert "native_target_order" not in field_primitives
