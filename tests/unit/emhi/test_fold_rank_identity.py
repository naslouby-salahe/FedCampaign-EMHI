from fedcampaign_emhi.artifacts.records import (
    ClientDetectorScoreStream,
    DetectorScoreArtifactRecord,
)
from fedcampaign_emhi.domain.enums import DatasetName, DetectorFamily
from fedcampaign_emhi.emhi.calibration import fold_rank_fingerprint
from fedcampaign_emhi.emhi.structure import build_marginal_rank_artifact, rank_at_epoch


def _score_artifact() -> DetectorScoreArtifactRecord:
    return DetectorScoreArtifactRecord(
        dataset_name=DatasetName.TON_IOT_NETWORK,
        root_seed=1,
        selected_client_ids=("client-a",),
        client_streams=(
            ClientDetectorScoreStream(
                client_id="client-a",
                detector_family=DetectorFamily.ISOLATION_FOREST,
                detector_seed=1,
                epoch_indexes=(0, 1, 2, 3, 4, 5),
                scores=(0.0, 1.0, 2.0, 3.0, 4.0, 5.0),
            ),
        ),
        dependency_fingerprint="f" * 64,
    )


def test_fold_rank_fingerprints_distinguish_training_boundaries() -> None:
    scores = _score_artifact()
    first = fold_rank_fingerprint(scores, 0, 2)
    second = fold_rank_fingerprint(scores, 2, 4)
    assert first != second
    assert fold_rank_fingerprint(scores, 0, 2) == first


def test_distinct_fold_rank_artifacts_do_not_share_reference_ranks() -> None:
    scores = _score_artifact()
    first = build_marginal_rank_artifact(
        scores, (0, 1), 1.0e-12, fold_rank_fingerprint(scores, 0, 2)
    )
    second = build_marginal_rank_artifact(
        scores, (4, 5), 1.0e-12, fold_rank_fingerprint(scores, 2, 4)
    )
    first_rank = rank_at_epoch(first, "client-a", 3)
    second_rank = rank_at_epoch(second, "client-a", 3)
    assert first_rank is not None and second_rank is not None
    assert abs(first_rank - 0.8333333333333333) < 1.0e-9
    assert abs(second_rank - 0.16666666666666666) < 1.0e-9
