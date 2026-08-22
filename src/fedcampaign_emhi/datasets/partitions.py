from math import floor

from fedcampaign_emhi.domain.types import EpochIndex, EpochSeconds, UnixTimestampSeconds


def epoch_index(
    unix_timestamp_seconds: UnixTimestampSeconds, epoch_seconds: EpochSeconds
) -> EpochIndex:
    if epoch_seconds <= 0:
        raise ValueError("epoch_seconds must be positive")
    index = floor(unix_timestamp_seconds / epoch_seconds)
    return EpochIndex(
        unix_timestamp_seconds=unix_timestamp_seconds,
        epoch_seconds=epoch_seconds,
        index=index,
    )
