import pytest

from fedcampaign_emhi.domain.enums import ExperimentName
from fedcampaign_emhi.reporting.tables import (
    TableCatalogEntry,
    TableRow,
    catalog_has_unique_sources_per_table,
    compact_source_is_machine_readable,
    every_table_maps_to_declared_experiment,
    table_names_are_unique,
)


def row(path: str, digest: str) -> TableRow:
    return TableRow(
        table_name="primary strict-ODI results",
        source_artifact_path=path,
        source_artifact_hash=digest,
        column_count=6,
    )


def entry(rows: tuple[TableRow, ...]) -> TableCatalogEntry:
    return TableCatalogEntry(
        table_name="primary strict-ODI results",
        experiment_name=ExperimentName.PRIMARY_STRICT_ODI_EVALUATION,
        row_bindings=rows,
    )


def test_single_sourced_tables_pass() -> None:
    good = entry((row("results/a/cell.json", "a" * 64), row("results/b/cell.json", "b" * 64)))
    assert good.is_single_sourced is True
    assert catalog_has_unique_sources_per_table((good,)) is True


def test_duplicate_source_hashes_fail_single_sourcing() -> None:
    bad = entry((row("results/a/cell.json", "a" * 64), row("results/b/cell.json", "a" * 64)))
    assert bad.is_single_sourced is False
    assert catalog_has_unique_sources_per_table((bad,)) is False


def test_table_names_must_be_unique_across_catalog() -> None:
    first = entry((row("results/a.json", "a" * 64),))
    second = entry((row("results/b.json", "b" * 64),))
    assert table_names_are_unique((first, second)) is False


def test_every_table_maps_to_declared_experiment() -> None:
    valid = entry((row("results/a.json", "a" * 64),))
    assert every_table_maps_to_declared_experiment((valid,)) is True


def test_compact_source_is_machine_readable_json() -> None:
    json_row = row("results/experiments/x/cell.json", "a" * 64)
    log_row = row("results/experiments/x/trace.log", "a" * 64)
    assert compact_source_is_machine_readable(json_row) is True
    assert compact_source_is_machine_readable(log_row) is False


def test_zero_columns_rejected() -> None:
    with pytest.raises(ValueError):
        TableRow(
            table_name="t",
            source_artifact_path="results/x.json",
            source_artifact_hash="a" * 64,
            column_count=0,
        )
