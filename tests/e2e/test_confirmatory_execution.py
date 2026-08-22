from fedcampaign_emhi.config.loading import load_production_configuration


def test_confirmatory_seed_namespace_is_independent() -> None:
    loaded = load_production_configuration()
    assert (
        loaded.values.randomness.real_development_roots
        != loaded.values.randomness.real_confirmatory_roots
    )
