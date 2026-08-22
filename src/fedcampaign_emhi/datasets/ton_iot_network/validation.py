from fedcampaign_emhi.domain.types import CanonicalEventToken

REQUIRED_TON_IOT_NETWORK_COLUMNS = (
    "ts",
    "src_ip",
    "proto",
    "service",
    "label",
    "type",
)


def missing_required_columns(
    observed_columns: tuple[CanonicalEventToken, ...],
) -> tuple[CanonicalEventToken, ...]:
    observed = {column.strip() for column in observed_columns}
    return tuple(column for column in REQUIRED_TON_IOT_NETWORK_COLUMNS if column not in observed)


def schema_is_executable(observed_columns: tuple[CanonicalEventToken, ...]) -> bool:
    return not missing_required_columns(observed_columns)
