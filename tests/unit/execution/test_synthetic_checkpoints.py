# pyright: reportPrivateUsage=false

from pathlib import Path

from fedcampaign_emhi.artifacts.storage import write_atomic_json
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import ExecutionRole, ExperimentName, ExperimentState
from fedcampaign_emhi.experiments.synthetic import SyntheticCellOutcome
from fedcampaign_emhi.experiments.synthetic_execution import (
    SyntheticCellExecution,
    _checkpoint_path,
    _checkpoint_payload,
    _load_reusable_checkpoint,
)


def test_synthetic_checkpoint_rehydrates_compatible_completed_work(
    production_configuration: LoadedScientificConfiguration,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    experiment_name = ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION
    role = ExecutionRole.DEVELOPMENT
    seed = 1
    execution = SyntheticCellExecution(
        state=ExperimentState.COMPLETED,
        outcome=SyntheticCellOutcome((), 0.0, {"checkpoint": "complete"}),
        finite_horizon_metrics=None,
        composition_metrics=None,
        technical_failure=False,
        runtime_seconds=12.5,
        peak_rss_bytes=1024,
    )
    checkpoint_path = _checkpoint_path(tmp_path, role, seed, None)
    write_atomic_json(
        checkpoint_path,
        _checkpoint_payload(
            production_configuration,
            repo_root,
            experiment_name,
            role,
            seed,
            None,
            execution,
        ),
        tmp_path / "staging",
    )

    rehydrated = _load_reusable_checkpoint(
        production_configuration,
        repo_root,
        experiment_name,
        role,
        seed,
        None,
        tmp_path,
    )

    assert rehydrated == execution


def test_synthetic_checkpoint_is_not_reused_for_a_different_experiment(
    production_configuration: LoadedScientificConfiguration,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    execution = SyntheticCellExecution(
        state=ExperimentState.COMPLETED,
        outcome=SyntheticCellOutcome((), 0.0),
        finite_horizon_metrics=None,
        composition_metrics=None,
        technical_failure=False,
        runtime_seconds=1.0,
        peak_rss_bytes=1,
    )
    write_atomic_json(
        _checkpoint_path(tmp_path, ExecutionRole.DEVELOPMENT, 1, None),
        _checkpoint_payload(
            production_configuration,
            repo_root,
            ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION,
            ExecutionRole.DEVELOPMENT,
            1,
            None,
            execution,
        ),
        tmp_path / "staging",
    )

    assert (
        _load_reusable_checkpoint(
            production_configuration,
            repo_root,
            ExperimentName.PURE_ORDER_SEPARATION_VALIDATION,
            ExecutionRole.DEVELOPMENT,
            1,
            None,
            tmp_path,
        )
        is None
    )


def test_synthetic_checkpoint_retries_a_technical_failure(
    production_configuration: LoadedScientificConfiguration,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    execution = SyntheticCellExecution(
        state=ExperimentState.FAILED,
        outcome=SyntheticCellOutcome(("temporary filesystem failure",), None),
        finite_horizon_metrics=None,
        composition_metrics=None,
        technical_failure=True,
        runtime_seconds=1.0,
        peak_rss_bytes=1,
    )
    write_atomic_json(
        _checkpoint_path(tmp_path, ExecutionRole.DEVELOPMENT, 1, None),
        _checkpoint_payload(
            production_configuration,
            repo_root,
            ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION,
            ExecutionRole.DEVELOPMENT,
            1,
            None,
            execution,
        ),
        tmp_path / "staging",
    )

    assert (
        _load_reusable_checkpoint(
            production_configuration,
            repo_root,
            ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION,
            ExecutionRole.DEVELOPMENT,
            1,
            None,
            tmp_path,
        )
        is None
    )


def test_synthetic_checkpoint_retries_a_scientifically_invalid_result(
    production_configuration: LoadedScientificConfiguration,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    execution = SyntheticCellExecution(
        state=ExperimentState.INVALID,
        outcome=SyntheticCellOutcome(("validation failed",), None),
        finite_horizon_metrics=None,
        composition_metrics=None,
        technical_failure=False,
        runtime_seconds=1.0,
        peak_rss_bytes=1,
    )
    write_atomic_json(
        _checkpoint_path(tmp_path, ExecutionRole.DEVELOPMENT, 1, None),
        _checkpoint_payload(
            production_configuration,
            repo_root,
            ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION,
            ExecutionRole.DEVELOPMENT,
            1,
            None,
            execution,
        ),
        tmp_path / "staging",
    )

    assert (
        _load_reusable_checkpoint(
            production_configuration,
            repo_root,
            ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION,
            ExecutionRole.DEVELOPMENT,
            1,
            None,
            tmp_path,
        )
        is None
    )
