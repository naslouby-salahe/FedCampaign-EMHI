from fedcampaign_emhi.detection.detector_assignment import assign_detector_families
from fedcampaign_emhi.detection.local_policy import persistence_is_triggered
from fedcampaign_emhi.domain.enums import DetectorFamily


def test_assignment_is_lexicographic_and_mod_three() -> None:
    assignments = assign_detector_families(("b", "a", "c"))
    assert [item.client_id for item in assignments] == ["a", "b", "c"]
    assert assignments[0].family is DetectorFamily.ISOLATION_FOREST
    assert assignments[1].family is DetectorFamily.ONE_CLASS_SVM
    assert assignments[2].family is DetectorFamily.AUTOENCODER


def test_persistence_may_trigger_once_m_observations_exist() -> None:
    assert persistence_is_triggered((True,), 1, 1) is True
    assert persistence_is_triggered((True, True), 2, 3) is True
    assert persistence_is_triggered((True,), 2, 3) is False
    assert persistence_is_triggered((False, True, True), 2, 3) is True
