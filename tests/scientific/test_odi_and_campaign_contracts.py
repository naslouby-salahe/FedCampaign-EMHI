from fedcampaign_emhi.evaluation.metrics import strict_odi_outcome


def test_same_epoch_is_not_odi() -> None:
    assert strict_odi_outcome(5, (5, 8)).indicator == 0
