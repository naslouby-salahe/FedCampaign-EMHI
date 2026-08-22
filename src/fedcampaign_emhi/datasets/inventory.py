from pathlib import Path

from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import DatasetName


def discover_raw_paths(raw_directory: Path) -> tuple[Path, ...]:
    if not raw_directory.exists():
        return ()
    if raw_directory.is_file():
        return (raw_directory.resolve(),)
    return tuple(sorted(path.resolve() for path in raw_directory.rglob("*") if path.is_file()))


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
