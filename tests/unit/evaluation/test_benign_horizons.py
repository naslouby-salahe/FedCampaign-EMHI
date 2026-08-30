from types import SimpleNamespace
from typing import cast

import pytest

import fedcampaign_emhi.evaluation.benign_horizons as benign_horizons
from fedcampaign_emhi.artifacts.records import (
    BenignHorizonRecord,
    EMHIFitArtifactRecord,
    MarginalRankArtifactRecord,
)
from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.datasets.preprocessing import (
    complete_benign_horizons,
    horizon_eligibility_state,
)
from fedcampaign_emhi.domain.enums import ClaimState
from fedcampaign_emhi.evaluation.benign_horizons import (
    TrajectoryCache,
    horizon_trajectory,
    horizons_are_nonoverlapping,
    sequential_stop_reset_epochs,
)
from fedcampaign_emhi.evaluation.records import SequentialTrajectory


def test_horizons_are_consecutive_nonoverlapping_and_drop_trailing() -> None:
    epochs = tuple(range(10, 20))
    horizons = complete_benign_horizons(epochs, 3)
    assert len(horizons) == 3
    assert horizons[0].epoch_indexes == (10, 11, 12)
    assert horizons[2].epoch_indexes == (16, 17, 18)
    assert 19 not in horizons[2].epoch_indexes
    assert horizons_are_nonoverlapping(horizons)
    assert sequential_stop_reset_epochs(horizons) == (10, 13, 16)
    assert horizon_eligibility_state(len(horizons), 4) is ClaimState.NOT_TESTED


def test_trajectory_cache_is_reused_only_for_identical_evaluation_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[object, ...]] = []
    expected = SequentialTrajectory(epochs=(), support_predicates=())

    def record_call(*args: object) -> SequentialTrajectory:
        calls.append(args)
        return expected

    monkeypatch.setattr(benign_horizons, "sequential_trajectory", record_call)
    horizon = BenignHorizonRecord(start_epoch=7, epoch_indexes=(7, 8))
    ranks = cast(
        MarginalRankArtifactRecord,
        SimpleNamespace(dependency_fingerprint="a" * 64),
    )
    first_fit = cast(
        EMHIFitArtifactRecord,
        SimpleNamespace(dependency_fingerprint="b" * 64),
    )
    second_fit = cast(
        EMHIFitArtifactRecord,
        SimpleNamespace(dependency_fingerprint="c" * 64),
    )
    cache = TrajectoryCache()
    config = cast(ScientificConfig, object())

    assert horizon_trajectory(config, ranks, first_fit, horizon, trajectory_cache=cache) is expected
    assert horizon_trajectory(config, ranks, first_fit, horizon, trajectory_cache=cache) is expected
    assert (
        horizon_trajectory(config, ranks, second_fit, horizon, trajectory_cache=cache) is expected
    )
    assert len(calls) == 2
