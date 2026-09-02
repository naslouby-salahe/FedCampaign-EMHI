from fedcampaign_emhi.config.loading import load_smoke_configuration
from fedcampaign_emhi.evaluation.validation import run_synthetic_module_validation


def test_smoke_validation_passes_all_exact_roadmap_fixtures() -> None:
    criterion = run_synthetic_module_validation(load_smoke_configuration())
    assert criterion.passed, criterion.failures
    assert criterion.failures == ()
