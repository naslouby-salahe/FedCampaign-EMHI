import pytest

from fedcampaign_emhi.detection.scoring import (
    oriented_score_stream,
    rank_stream,
    score_stream_isolation_check,
)


def test_score_stream_isolation_requires_one_score_per_epoch() -> None:
    score_stream_isolation_check(3, 3)
    with pytest.raises(ValueError):
        score_stream_isolation_check(2, 3)


def test_rank_stream_uses_benign_reference_and_clips() -> None:
    ranks = rank_stream((0.0, 0.5, 1.0), (0.0, 1.0), 0.1)
    assert ranks == pytest.approx((1 / 3, 0.5, 2 / 3))


def test_score_stream_rejects_empty_input() -> None:
    with pytest.raises(ValueError):
        oriented_score_stream(())
