from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.execution.runner import confirmatory_completeness_within_tolerance


def test_no_missing_seeds_is_within_tolerance(
    production_configuration: LoadedScientificConfiguration,
) -> None:
    expected = production_configuration.values.randomness.synthetic_confirmatory_roots
    assert confirmatory_completeness_within_tolerance(production_configuration, expected, expected)


def test_missing_count_at_configured_tolerance_is_accepted(
    production_configuration: LoadedScientificConfiguration,
) -> None:
    tolerance = production_configuration.values.runtime.required_confirmatory_missing_cell_tolerance
    loaded = production_configuration.model_copy(
        update={
            "values": production_configuration.values.model_copy(
                update={
                    "runtime": production_configuration.values.runtime.model_copy(
                        update={"required_confirmatory_missing_cell_tolerance": tolerance + 1}
                    )
                }
            )
        }
    )
    expected = loaded.values.randomness.synthetic_confirmatory_roots
    observed = expected[1:]
    assert confirmatory_completeness_within_tolerance(loaded, expected, observed)


def test_missing_count_above_tolerance_is_rejected(
    production_configuration: LoadedScientificConfiguration,
) -> None:
    expected = production_configuration.values.randomness.synthetic_confirmatory_roots
    observed = expected[1:]
    assert not confirmatory_completeness_within_tolerance(
        production_configuration, expected, observed
    )


def test_unexpected_seed_is_rejected_even_within_tolerance(
    production_configuration: LoadedScientificConfiguration,
) -> None:
    tolerance = production_configuration.values.runtime.required_confirmatory_missing_cell_tolerance
    loaded = production_configuration.model_copy(
        update={
            "values": production_configuration.values.model_copy(
                update={
                    "runtime": production_configuration.values.runtime.model_copy(
                        update={"required_confirmatory_missing_cell_tolerance": tolerance + 10}
                    )
                }
            )
        }
    )
    expected = loaded.values.randomness.synthetic_confirmatory_roots
    observed = (*expected, 999999999)
    assert not confirmatory_completeness_within_tolerance(loaded, expected, observed)
