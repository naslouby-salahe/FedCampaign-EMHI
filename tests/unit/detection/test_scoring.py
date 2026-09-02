import pytest

from fedcampaign_emhi.detection import score_stream_isolation_check


def test_score_stream_isolation_requires_one_score_per_epoch() -> None:
    score_stream_isolation_check(3, 3)
    with pytest.raises(ValueError):
        score_stream_isolation_check(2, 3)
