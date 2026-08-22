from fedcampaign_emhi.detection.detector_assignment import assign_detector_families
from fedcampaign_emhi.domain.enums import DetectorFamily


def test_detector_family_assignment_is_lexicographic_mod_three() -> None:
    assigned = assign_detector_families(("c2", "c1", "c3"))
    assert [item.client_id for item in assigned] == ["c1", "c2", "c3"]
    assert assigned[0].family is DetectorFamily.ISOLATION_FOREST
    assert assigned[1].family is DetectorFamily.ONE_CLASS_SVM
    assert assigned[2].family is DetectorFamily.AUTOENCODER
