from datetime import UTC, datetime

import pytest

from fedcampaign_emhi.datasets.edge_iiotset.loading import parse_frame_time


def test_year_clock_uses_documented_utc_base_rule() -> None:
    parsed = parse_frame_time(" 2021 11:44:10.081753000 ")
    expected = datetime(2021, 1, 1, 11, 44, 10, 81753, tzinfo=UTC).timestamp()
    assert parsed == expected


def test_naive_iso_timestamp_fails_closed() -> None:
    with pytest.raises(ValueError, match="dataset timezone rule"):
        parse_frame_time("2021-01-01T11:44:10")


def test_unparseable_timestamp_raises() -> None:
    with pytest.raises(ValueError):
        parse_frame_time("not-a-timestamp")
