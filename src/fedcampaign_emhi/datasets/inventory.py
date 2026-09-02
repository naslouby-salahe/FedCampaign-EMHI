from pathlib import Path

from fedcampaign_emhi.artifacts.storage import file_sha256
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import DatasetName
from fedcampaign_emhi.domain.types import (
    FileInventoryEntry,
)


def discover_raw_paths(raw_directory: Path) -> tuple[Path, ...]:
    candidates: tuple[Path, ...]
    if not raw_directory.exists():
        candidates = ()
    elif raw_directory.is_file():
        candidates = (raw_directory,)
    else:
        candidates = tuple(raw_directory.rglob("*"))
    return tuple(sorted(path.resolve() for path in candidates if path.is_file()))


def configured_raw_directory(
    loaded: LoadedScientificConfiguration,
    dataset_name: DatasetName,
    repository: Path,
) -> Path:
    if dataset_name is DatasetName.TON_IOT_NETWORK:
        relative = loaded.values.datasets.primary.raw_directory
    elif dataset_name is DatasetName.EDGE_IIOTSET:
        relative = loaded.values.datasets.secondary.raw_directory
    else:
        raise ValueError(f"unsupported dataset {dataset_name}")
    return (repository / relative).resolve()


def inventory_raw_directory(
    raw_directory: Path, repository: Path
) -> tuple[FileInventoryEntry, ...]:
    entries: list[FileInventoryEntry] = []
    for path in discover_raw_paths(raw_directory):
        relative = path.relative_to(repository) if path.is_relative_to(repository) else path
        entries.append(
            FileInventoryEntry(
                relative_path=relative.as_posix(),
                sha256=file_sha256(path),
                byte_count=path.stat().st_size,
            )
        )
    return tuple(entries)
