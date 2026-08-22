from fedcampaign_emhi.comparators.multistream_cusum import next_cusum_state
from fedcampaign_emhi.comparators.rank_fusion import max_rank_fusion, mean_rank_fusion
from fedcampaign_emhi.domain.types import RankReference
from fedcampaign_emhi.emhi.ranks import midrank


def test_mean_and_max_rank_fusion() -> None:
    ranks = (0.2, 0.4, 0.9)
    assert abs(mean_rank_fusion(ranks) - (1.5 / 3)) < 1.0e-12
    assert max_rank_fusion(ranks) == 0.9


def test_smoke_midrank_fixture() -> None:
    rank = midrank(0.5, RankReference(scores=(0.0, 0.5, 0.5, 1.0)))
    assert rank == 0.5


def test_cusum_does_not_go_negative() -> None:
    assert next_cusum_state(0.0, 0.5, 0.5, 0.05) == 0.0
    assert next_cusum_state(1.0, 0.9, 0.5, 0.05) == 1.35
