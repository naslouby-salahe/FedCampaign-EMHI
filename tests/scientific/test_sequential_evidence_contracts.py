from math import exp, isclose

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.emhi.evidence import signed_evidence_factor


def test_signed_evidence_matches_locked_compensator() -> None:
    loaded = load_production_configuration()
    factor = signed_evidence_factor(
        1.0, loaded.values.evidence.clip_bound, loaded.values.evidence.bet_lambda
    )
    assert isclose(factor, exp(0.375))
    assert isclose(loaded.derived.signed_theorem_compensator, 0.125)
