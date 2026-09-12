from __future__ import annotations

from pathlib import Path

from tests.architecture.ast_scans import (
    cast_annotation_violations,
    parametrize_source_files,
)


@parametrize_source_files
def test_no_primitive_casts(path: Path) -> None:
    assert cast_annotation_violations(path) == []


def test_primitive_cast_rule_rejects_scalar_and_nested_container_targets(tmp_path: Path) -> None:
    fixture = tmp_path / "consumer.py"
    fixture.write_text(
        "from fedcampaign_emhi.config.validation import YamlNode\n"
        "from typing import cast\n"
        "def counts(row: YamlNode) -> YamlNode:\n"
        "    return cast(int, row)\n"
        "def pairs(row: YamlNode) -> YamlNode:\n"
        "    return cast(tuple[int, int], row)\n"
        "def rates(row: YamlNode) -> YamlNode:\n"
        "    return cast(tuple[float, ...], row)\n",
        encoding="utf-8",
    )
    assert cast_annotation_violations(fixture) == [
        "consumer.py:4: cast to primitive 'int'",
        "consumer.py:6: cast to primitive 'tuple[int, int]'",
        "consumer.py:8: cast to primitive 'tuple[float, ...]'",
    ]


def test_primitive_cast_rule_accepts_domain_and_boundary_targets(tmp_path: Path) -> None:
    fixture = tmp_path / "consumer.py"
    fixture.write_text(
        "from collections.abc import Mapping\n"
        "from typing import cast\n"
        "from fedcampaign_emhi.config.validation import YamlNode\n"
        "from fedcampaign_emhi.domain.enums import DatasetName\n"
        "from fedcampaign_emhi.domain.types import RecordCount\n"
        "def count(row: YamlNode) -> RecordCount:\n"
        "    return cast(RecordCount, row)\n"
        "def name(row: YamlNode) -> DatasetName:\n"
        "    return cast(DatasetName, row)\n"
        "def payload(row: YamlNode) -> YamlNode:\n"
        "    return cast(YamlNode, row)\n"
        "def row_mapping(row: YamlNode) -> Mapping[str, YamlNode]:\n"
        "    return cast(Mapping[str, YamlNode], row)\n",
        encoding="utf-8",
    )
    assert cast_annotation_violations(fixture) == []


def test_primitive_cast_rule_rejects_bare_object_and_bytes(tmp_path: Path) -> None:
    fixture = tmp_path / "consumer.py"
    fixture.write_text(
        "from typing import cast\n"
        "def widen(row: object) -> object:\n"
        "    return cast(object, row)\n"
        "def raw(value: bytes) -> bytes:\n"
        "    return cast(bytes, value)\n",
        encoding="utf-8",
    )
    assert cast_annotation_violations(fixture) == [
        "consumer.py:3: cast to primitive 'object'",
        "consumer.py:5: cast to primitive 'bytes'",
    ]
