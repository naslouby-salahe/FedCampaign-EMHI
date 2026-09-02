from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.types import RankReference
from fedcampaign_emhi.emhi.contexts import histogram_bin_index
from fedcampaign_emhi.emhi.projection import blocked_fold_bounds
from fedcampaign_emhi.emhi.structure import clip_rank, midrank


def test_blocked_folds_are_contiguous() -> None:
    bounds = blocked_fold_bounds(11, 5)
    assert bounds == ((0, 3), (3, 5), (5, 7), (7, 9), (9, 11))


def test_smoke_rank_clip_and_histogram_bins() -> None:
    loaded = load_production_configuration()
    epsilon = loaded.values.context.rank_clip_epsilon
    bins = loaded.values.context.outside_histogram_bin_count
    assert clip_rank(0.0, epsilon) == epsilon
    assert clip_rank(1.0, epsilon) == 1.0 - epsilon
    assert midrank(0.5, RankReference(scores=(0.0, 0.5, 0.5, 1.0))) == 0.5
    ranks = (0.01, 0.13, 0.99)
    indices = tuple(histogram_bin_index(rank, bins) for rank in ranks)
    assert indices == (0, 1, 7)
