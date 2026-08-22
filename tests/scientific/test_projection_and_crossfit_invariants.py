from fedcampaign_emhi.emhi.projection import blocked_fold_bounds


def test_blocked_folds_are_contiguous() -> None:
    bounds = blocked_fold_bounds(11, 5)
    assert bounds == ((0, 3), (3, 5), (5, 7), (7, 9), (9, 11))
