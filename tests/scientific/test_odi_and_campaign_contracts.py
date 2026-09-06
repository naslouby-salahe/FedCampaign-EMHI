import inspect

from fedcampaign_emhi.analysis.results import PRIMARY_HOLM_STATISTICS, SECONDARY_HOLM_STATISTICS
from fedcampaign_emhi.detection import first_local_stop_epoch
from fedcampaign_emhi.domain.enums import SecondaryHolmHypothesis
from fedcampaign_emhi.emhi.sequential import first_global_stop_epoch, next_global_state
from fedcampaign_emhi.evaluation.metrics import strict_odi_outcome


def test_same_epoch_is_not_odi_but_is_global_detection() -> None:
    outcome = strict_odi_outcome(5, (5, 8))
    assert outcome.indicator == 0
    assert outcome.global_detection_indicator == 1


def test_earlier_global_stop_is_odi() -> None:
    outcome = strict_odi_outcome(4, (5, 8))
    assert outcome.indicator == 1
    assert outcome.global_detection_indicator == 1


def test_missing_global_stop_is_not_odi() -> None:
    outcome = strict_odi_outcome(None, (5, 8))
    assert outcome.indicator == 0
    assert outcome.global_detection_indicator == 0


def test_later_global_stop_is_detection_without_odi() -> None:
    outcome = strict_odi_outcome(7, (5, 8))
    assert outcome.indicator == 0
    assert outcome.global_detection_indicator == 1


def test_local_stop_is_first_persistence_epoch() -> None:
    exceedances = (False, True, True, True)
    assert first_local_stop_epoch(exceedances, 2, 3) == 2


def test_global_stop_ignores_local_policy_inputs() -> None:
    evidence = (1.0, 2.0, 2.0)
    support = (True, True, True)
    stop = first_global_stop_epoch(evidence, support, 4.0)
    state = next_global_state(0.0, 1.0)
    state = next_global_state(state, 2.0)
    assert state == 4.0
    assert stop == 1


def test_global_state_update_has_no_local_policy_argument() -> None:
    names = tuple(inspect.signature(next_global_state).parameters)
    assert names == ("previous_state", "evidence_factor")


def test_secondary_holm_hypothesis_matches_roadmap_identifiers() -> None:
    assert tuple(hypothesis.value for hypothesis in SecondaryHolmHypothesis) == (
        "Full FedCampaign-EMHI vs Inclusive Context",
        "Full FedCampaign-EMHI vs Leave-One-Out Context",
        "Full FedCampaign-EMHI vs Partial Exclusion",
        "Full FedCampaign-EMHI vs No Purification",
        "Full FedCampaign-EMHI vs Order One",
        "Full FedCampaign-EMHI vs Order at Most Two",
    )


def test_holm_statistic_families_have_declared_sizes() -> None:
    assert len(PRIMARY_HOLM_STATISTICS) == 5
    assert len(SECONDARY_HOLM_STATISTICS) == 6
