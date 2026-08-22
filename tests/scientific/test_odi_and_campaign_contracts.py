from fedcampaign_emhi.datasets.campaigns import first_activity_is_distributed
from fedcampaign_emhi.evaluation.metrics import strict_odi_outcome


def test_same_epoch_is_not_odi() -> None:
    assert strict_odi_outcome(5, (5, 8)).indicator == 0


def test_earlier_global_stop_is_odi() -> None:
    assert strict_odi_outcome(4, (5, 8)).indicator == 1


def test_missing_global_stop_is_not_odi() -> None:
    assert strict_odi_outcome(None, (5, 8)).indicator == 0


def test_distributed_first_activity_window() -> None:
    assert first_activity_is_distributed((10, 15, 12), 10) is True
    assert first_activity_is_distributed((10, 30), 10) is False
