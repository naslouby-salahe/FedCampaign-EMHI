from fedcampaign_emhi.runtime.monitoring import assess_implementation_readiness


def test_readiness_probe() -> None:
    readiness = assess_implementation_readiness()
    assert readiness.production_configuration_valid is True
    assert readiness.unspecified_scientific_choice_count == 0
