from fedcampaign_emhi.config.loading import load_smoke_configuration
from fedcampaign_emhi.evaluation.smoke_validation import (
    run_synthetic_module_validation,
    smoke_false_stop_counts,
    smoke_first_activity_epochs,
)


def test_smoke_validation_passes_all_exact_roadmap_fixtures() -> None:
    criterion = run_synthetic_module_validation(load_smoke_configuration())
    assert criterion.passed, criterion.failures
    assert criterion.failures == ()


def test_smoke_fixture_inputs_match_roadmap_table() -> None:
    assert smoke_false_stop_counts() == (20, 15, 5, 0)
    assert smoke_first_activity_epochs() == (300, 302)
