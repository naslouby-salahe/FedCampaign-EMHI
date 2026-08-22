from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import GeneratorName


def test_pure_order_primary_condition_is_locked() -> None:
    loaded = load_production_configuration()
    primary = loaded.values.experiments.pure_order_separation_validation.primary_condition
    assert primary.generator is GeneratorName.PURE_CONTINUOUS_TRIPLE
    assert primary.coalition_order == 3
