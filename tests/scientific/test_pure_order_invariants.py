from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import GeneratorName
from fedcampaign_emhi.synthetic.pure_order import pure_order_one_response, xor_parity_response


def test_pure_order_primary_condition_is_locked() -> None:
    loaded = load_production_configuration()
    primary = loaded.values.experiments.pure_order_separation_validation.primary_condition
    assert primary.generator is GeneratorName.PURE_CONTINUOUS_TRIPLE
    assert primary.coalition_order == 3


def test_order_one_effect_is_linear_in_theta() -> None:
    ranks = (0.75, 0.25)
    assert (
        abs(pure_order_one_response(ranks, 0.2) - (2.0 * pure_order_one_response(ranks, 0.1)))
        < 1.0e-12
    )


def test_xor_parity_flips_with_one_bit() -> None:
    assert xor_parity_response((1, 1, 0), 1.0) == -1.0
    assert xor_parity_response((1, 1, 1), 1.0) == 1.0
