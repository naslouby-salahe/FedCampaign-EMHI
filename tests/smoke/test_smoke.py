from fedcampaign_emhi.config.loading import load_smoke_configuration
from fedcampaign_emhi.evaluation.smoke_gate import (
    run_synthetic_module_validation,
    smoke_false_stop_counts,
    smoke_first_activity_epochs,
)


def test_smoke_gate_passes_all_exact_roadmap_fixtures() -> None:
    gate = run_synthetic_module_validation(load_smoke_configuration())
    assert gate.passed, gate.failures
    assert gate.failures == ()


def test_smoke_fixture_inputs_match_roadmap_table() -> None:
    assert smoke_false_stop_counts() == (20, 15, 5, 0)
    assert smoke_first_activity_epochs() == (300, 302)
