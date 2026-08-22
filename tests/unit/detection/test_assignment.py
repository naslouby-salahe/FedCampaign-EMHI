import inspect

from fedcampaign_emhi.detection.detector_assignment import assign_detector_families
from fedcampaign_emhi.detection.fitting import (
    family_uses_detector_fit_only,
    permitted_fitting_partitions,
    score_isolation_forest,
)
from fedcampaign_emhi.detection.local_policy import (
    candidate_thresholds_from_nuisance_scores,
    heldout_false_stop_count,
    operating_point_state_for_policy,
    persistence_is_triggered,
    select_immutable_local_policy,
)
from fedcampaign_emhi.domain.enums import DetectorFamily, OperatingPointState, PartitionRole
from fedcampaign_emhi.domain.types import LocalPolicyArtifact


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


def test_fitting_uses_detector_fit_only() -> None:
    assert permitted_fitting_partitions() == (PartitionRole.DETECTOR_FIT,)
    assert family_uses_detector_fit_only(DetectorFamily.ISOLATION_FOREST)
    assert "heldout" not in inspect.signature(score_isolation_forest).parameters
    fit_rows = tuple((float(index), 0.0) for index in range(20))
    scores = score_isolation_forest(fit_rows, ((0.0, 0.0), (100.0, 0.0)), 10, 16, 1.0, 1, 7)
    assert scores[1] > scores[0]


def test_local_policy_is_selected_on_calibration_and_immutable() -> None:
    thresholds = candidate_thresholds_from_nuisance_scores((0.1, 0.2, 0.9, 1.0), (0.5,))
    assert len(thresholds) == 1
    loose = LocalPolicyArtifact(threshold=0.1, required_exceedances=1, window_epochs=1)
    strict = LocalPolicyArtifact(threshold=0.9, required_exceedances=1, window_epochs=1)
    selected = select_immutable_local_policy((loose, strict), (8, 0), 20, 0.95, 0.2)
    assert selected == strict
    heldout = heldout_false_stop_count(((True,), (False,)), 1, 1)
    assert heldout == 1
    assert operating_point_state_for_policy(None) is OperatingPointState.UNAVAILABLE
    assert "heldout" not in inspect.signature(select_immutable_local_policy).parameters
