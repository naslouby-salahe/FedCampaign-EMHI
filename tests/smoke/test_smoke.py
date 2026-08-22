from fedcampaign_emhi.config.loading import load_smoke_configuration
from fedcampaign_emhi.evaluation.metrics import smoke_module_fixtures


def test_smoke_fixtures() -> None:
    loaded = load_smoke_configuration()
    fixtures = smoke_module_fixtures(loaded)
    assert fixtures.blocked_fold_sizes == (3, 2, 2, 2, 2)
    assert fixtures.strict_odi_indicator == 1
