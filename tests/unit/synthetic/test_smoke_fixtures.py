from fedcampaign_emhi.datasets.campaigns import campaign_duration_epochs, merge_malicious_runs
from fedcampaign_emhi.synthetic.common_mode import equally_spaced_loadings


def test_loadings_are_equally_spaced() -> None:
    loadings = equally_spaced_loadings(3, 0.6, 1.0)
    assert loadings[0] == 0.6
    assert loadings[-1] == 1.0
    assert abs(loadings[1] - 0.8) < 1.0e-12


def test_campaign_merge_and_duration() -> None:
    merged = merge_malicious_runs((1, 2, 4, 20), 2)
    assert merged == ((1, 4), (20, 20))
    assert campaign_duration_epochs(1, 4) == 4
