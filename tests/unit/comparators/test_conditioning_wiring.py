from pathlib import Path

import pytest

from fedcampaign_emhi.artifacts.records import (
    ClientDetectorScoreStream,
    DetectorScoreArtifactRecord,
    MarginalRankArtifactRecord,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration, ScientificConfig
from fedcampaign_emhi.domain.enums import DatasetName, DetectorFamily, MethodName
from fedcampaign_emhi.domain.types import EpochIndexValue, RankValue
from fedcampaign_emhi.emhi.structure import build_marginal_rank_artifact
from fedcampaign_emhi.experiments.seed_evaluation import (
    comparator_epoch_scores,
    comparator_evidence_scores,
)


def _score_artifact(
    client_count: int, epoch_count: int, seed_offset: int
) -> DetectorScoreArtifactRecord:
    streams: list[ClientDetectorScoreStream] = []
    for client in range(client_count):
        scores = tuple(
            ((epoch * 31 + client * 17 + seed_offset) % 7919) / 7919 for epoch in range(epoch_count)
        )
        streams.append(
            ClientDetectorScoreStream(
                client_id=f"client-{client:03d}",
                detector_family=DetectorFamily.ISOLATION_FOREST,
                detector_seed=1,
                epoch_indexes=tuple(range(epoch_count)),
                scores=scores,
            )
        )
    return DetectorScoreArtifactRecord(
        dataset_name=DatasetName.TON_IOT_NETWORK,
        root_seed=1,
        selected_client_ids=tuple(f"client-{client:03d}" for client in range(client_count)),
        client_streams=tuple(streams),
        dependency_fingerprint="a" * 64,
    )


def _ranks(client_count: int, epoch_count: int) -> MarginalRankArtifactRecord:
    scores = _score_artifact(client_count, epoch_count, 5)
    return build_marginal_rank_artifact(scores, tuple(range(2, 60)), 1.0e-12, "b" * 64)


def test_pair_dependence_conditioned_scoring_executes_and_is_deterministic(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    ranks = _ranks(6, 400)
    nuisance = tuple(range(2, 60))
    first = comparator_epoch_scores(
        production_configuration, tmp_path, ranks, MethodName.CONDITIONAL_PAIR_DEPENDENCE, nuisance
    )
    second = comparator_epoch_scores(
        production_configuration, tmp_path, ranks, MethodName.CONDITIONAL_PAIR_DEPENDENCE, nuisance
    )
    assert first == second
    assert first
    assert all(epoch >= 1 for epoch, _score in first)
    assert all(score > 0.0 for _epoch, score in first)


def test_conditioned_method_on_insufficient_outside_context_yields_no_evidence(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    ranks = _ranks(4, 200)
    scores = comparator_epoch_scores(
        production_configuration,
        tmp_path,
        ranks,
        MethodName.EXCLUSION_MATCHED_CONDITIONAL_HOFD,
        tuple(range(2, 60)),
    )
    assert scores == ()
    assert comparator_evidence_scores(production_configuration, (), tuple(range(2, 60))) == ()


def test_non_conditioned_comparator_still_scores_with_raw_ranks(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    ranks = _ranks(6, 200)
    scores = comparator_epoch_scores(
        production_configuration,
        tmp_path,
        ranks,
        MethodName.RAW_MEAN_RANK_FUSION,
        tuple(range(2, 60)),
    )
    assert scores


def test_conditioned_scoring_cannot_silently_fall_back_to_plain_ranks(
    production_configuration: LoadedScientificConfiguration,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import fedcampaign_emhi.experiments.seed_evaluation as module
    from fedcampaign_emhi.comparators.conditioning import (
        ComparatorConditioningModel,
        ComparatorEpochPanel,
        condition_epoch_ranks,
    )

    ranks = _ranks(6, 200)
    calls = {"count": 0}

    def counting_condition(
        config: ScientificConfig,
        panel: ComparatorEpochPanel,
        epoch: EpochIndexValue,
        model: ComparatorConditioningModel,
    ) -> tuple[RankValue, ...] | None:
        calls["count"] += 1
        return condition_epoch_ranks(config, panel, epoch, model)

    monkeypatch.setattr(module, "condition_epoch_ranks", counting_condition)
    scores = comparator_epoch_scores(
        production_configuration,
        tmp_path,
        ranks,
        MethodName.CONDITIONAL_PAIR_DEPENDENCE,
        tuple(range(2, 60)),
    )
    assert scores
    assert calls["count"] > 0
