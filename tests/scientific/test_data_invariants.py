from fedcampaign_emhi.config.loading import load_production_configuration


def test_heldout_is_remainder_not_a_configured_fraction() -> None:
    loaded = load_production_configuration()
    fractions = loaded.values.datasets.preprocessing.benign_partition_fractions
    assert (
        fractions.detector_fit + fractions.nuisance_fit + fractions.threshold_and_policy_calibration
        < 1.0
    )
    assert loaded.derived.heldout_benign_is_remainder is True
