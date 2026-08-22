from pathlib import Path

from fedcampaign_emhi.artifacts.storage import file_sha256
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.datasets.edge_iiotset.validation import (
    REQUIRED_EDGE_IIOTSET_COLUMNS,
)
from fedcampaign_emhi.datasets.edge_iiotset.validation import (
    adapter_material_code_fingerprint as edge_iiotset_adapter_material_code_fingerprint,
)
from fedcampaign_emhi.datasets.ton_iot_network.validation import (
    REQUIRED_TON_IOT_NETWORK_COLUMNS,
    adapter_material_code_fingerprint,
)
from fedcampaign_emhi.domain.enums import DatasetName
from fedcampaign_emhi.domain.types import (
    CanonicalEventToken,
    EdgeIiotsetReleaseIdentity,
    FileInventoryEntry,
    Sha256Hex,
    TonIotNetworkReleaseIdentity,
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


def map_documented_columns(
    documented: tuple[CanonicalEventToken, ...], observed: tuple[CanonicalEventToken, ...]
) -> tuple[tuple[CanonicalEventToken, CanonicalEventToken], ...]:
    observed_set = {column.strip() for column in observed}
    mapped: list[tuple[CanonicalEventToken, CanonicalEventToken]] = []
    for column in documented:
        if column not in observed_set:
            raise ValueError(f"documented semantic field {column} is missing from observed schema")
        mapped.append((column, column))
    return tuple(mapped)


def ton_iot_network_field_mapping(
    observed: tuple[CanonicalEventToken, ...],
) -> tuple[tuple[CanonicalEventToken, CanonicalEventToken], ...]:
    return map_documented_columns(REQUIRED_TON_IOT_NETWORK_COLUMNS, observed)


def edge_iiotset_field_mapping(
    observed: tuple[CanonicalEventToken, ...],
) -> tuple[tuple[CanonicalEventToken, CanonicalEventToken], ...]:
    return map_documented_columns(REQUIRED_EDGE_IIOTSET_COLUMNS, observed)


def adapter_producer_commit(repository: Path) -> CanonicalEventToken:
    head = repository / ".git" / "HEAD"
    if not head.is_file():
        raise ValueError("adapter producer commit is unavailable")
    text = head.read_text(encoding="utf-8").strip()
    if text.startswith("ref:"):
        reference = repository / ".git" / text.split(" ", 1)[1].strip()
        if not reference.is_file():
            raise ValueError("adapter producer commit reference is unavailable")
        return reference.read_text(encoding="utf-8").strip()
    return text


def build_ton_iot_network_release_identity(
    files: tuple[FileInventoryEntry, ...],
    ground_truth_source_sha256: Sha256Hex | None,
    adapter_producer_commit_hash: CanonicalEventToken,
) -> TonIotNetworkReleaseIdentity:
    return TonIotNetworkReleaseIdentity(
        release_persistent_identifier="IEEE DataPort / UNSW Research TON_IoT Datasets",
        dataset_version_label="Network flow variant",
        files=files,
        ground_truth_source_sha256=ground_truth_source_sha256,
        adapter_material_code_fingerprint=adapter_material_code_fingerprint(),
        adapter_producer_commit=adapter_producer_commit_hash,
        published_external_checksum_cross_checks=(),
    )


def build_edge_iiotset_release_identity(
    files: tuple[FileInventoryEntry, ...],
    ground_truth_source_sha256: Sha256Hex | None,
    adapter_producer_commit_hash: CanonicalEventToken,
) -> EdgeIiotsetReleaseIdentity:
    return EdgeIiotsetReleaseIdentity(
        release_persistent_identifier="10.21227/mbc1-1h68",
        dataset_version_label=DatasetName.EDGE_IIOTSET.value,
        files=files,
        ground_truth_source_sha256=ground_truth_source_sha256,
        adapter_material_code_fingerprint=edge_iiotset_adapter_material_code_fingerprint(),
        adapter_producer_commit=adapter_producer_commit_hash,
        published_external_checksum_cross_checks=(),
    )


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
