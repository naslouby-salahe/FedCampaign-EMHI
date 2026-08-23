from dataclasses import dataclass

from fedcampaign_emhi.domain.enums import ExperimentName
from fedcampaign_emhi.domain.types import (
    ComponentName,
    ModuleContract,
    RecordCount,
    RelativePath,
    Sha256Hex,
)


def tables_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.reporting.tables",
        ownership="compact manuscript-facing tables without recomputing scientific metrics or statistics",
    )


@dataclass(frozen=True)
class TableRow:
    table_name: ComponentName
    source_artifact_path: RelativePath
    source_artifact_hash: Sha256Hex
    column_count: RecordCount

    def __post_init__(self) -> None:
        if self.column_count <= 0:
            raise ValueError("a table row binding requires at least one column")


@dataclass(frozen=True)
class TableCatalogEntry:
    table_name: ComponentName
    experiment_name: ExperimentName
    row_bindings: tuple[TableRow, ...]

    @property
    def is_single_sourced(self) -> bool:
        hashes = [row.source_artifact_hash for row in self.row_bindings]
        return len(set(hashes)) == len(hashes)


def catalog_has_unique_sources_per_table(catalog: tuple[TableCatalogEntry, ...]) -> bool:
    return all(entry.is_single_sourced for entry in catalog)


def table_names_are_unique(catalog: tuple[TableCatalogEntry, ...]) -> bool:
    names = [entry.table_name for entry in catalog]
    return len(set(names)) == len(names)


def every_table_maps_to_declared_experiment(catalog: tuple[TableCatalogEntry, ...]) -> bool:
    return all(entry.experiment_name in list(ExperimentName) for entry in catalog)


def compact_source_is_machine_readable(binding: TableRow) -> bool:
    return binding.source_artifact_path.endswith(".json")
