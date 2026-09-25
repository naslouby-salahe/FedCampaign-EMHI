from fedcampaign_emhi.evaluation.metrics import strict_odi_outcome


def test_strict_odi_requires_earlier_global_stop() -> None:
    assert strict_odi_outcome(4, (5, 8)).indicator == 1
    assert strict_odi_outcome(5, (5, 8)).indicator == 0


def test_strict_odi_with_no_local_stop_is_odi_when_global_stops() -> None:
    assert strict_odi_outcome(4, (None, None)).indicator == 1
    assert strict_odi_outcome(None, (None, None)).indicator == 0
