import pytest

import fedcampaign_emhi.experiments.synthetic_execution as runner
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import ExecutionRole, ExperimentName, MethodName
from fedcampaign_emhi.domain.types import SeedValue
from fedcampaign_emhi.experiments.synthetic import SyntheticCellOutcome
from fedcampaign_emhi.experiments.synthetic_execution import run_synthetic_cell_with_technical_retry


def _flaky_cell(fail_count: int, result: SyntheticCellOutcome):
    attempts = {"count": 0}

    def cell(
        loaded: LoadedScientificConfiguration,
        experiment_name: ExperimentName,
        seed: SeedValue,
        method_name: MethodName | None,
        execution_role: ExecutionRole,
    ) -> SyntheticCellOutcome:
        attempts["count"] += 1
        if attempts["count"] <= fail_count:
            raise OSError("transient staging failure")
        return result

    return cell, attempts


def _always_fails(
    loaded: LoadedScientificConfiguration,
    experiment_name: ExperimentName,
    seed: SeedValue,
    method_name: MethodName | None,
    execution_role: ExecutionRole,
) -> SyntheticCellOutcome:
    raise OSError("persistent staging failure")


def _always_scientific_error(
    loaded: LoadedScientificConfiguration,
    experiment_name: ExperimentName,
    seed: SeedValue,
    method_name: MethodName | None,
    execution_role: ExecutionRole,
) -> SyntheticCellOutcome:
    raise ValueError("purity violation")


def test_technical_retry_succeeds_after_transient_failures(
    production_configuration: LoadedScientificConfiguration,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    retries = (
        production_configuration.values.runtime.automatic_technical_retries_after_initial_failure
    )
    expected = SyntheticCellOutcome((), 0.0)
    cell, attempts = _flaky_cell(retries, expected)
    monkeypatch.setattr(runner, "run_synthetic_cell", cell)
    outcome = run_synthetic_cell_with_technical_retry(
        production_configuration,
        ExperimentName.SYNTHETIC_MODULE_VALIDATION,
        1,
        None,
        ExecutionRole.DEVELOPMENT,
    )
    assert outcome is expected
    assert attempts["count"] == retries + 1


def test_technical_retry_raises_after_exhausting_configured_count(
    production_configuration: LoadedScientificConfiguration,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    retries = (
        production_configuration.values.runtime.automatic_technical_retries_after_initial_failure
    )
    calls = {"count": 0}

    def counting_always_fails(
        loaded: LoadedScientificConfiguration,
        experiment_name: ExperimentName,
        seed: SeedValue,
        method_name: MethodName | None,
        execution_role: ExecutionRole,
    ) -> SyntheticCellOutcome:
        calls["count"] += 1
        return _always_fails(loaded, experiment_name, seed, method_name, execution_role)

    monkeypatch.setattr(runner, "run_synthetic_cell", counting_always_fails)
    with pytest.raises(OSError, match="persistent staging failure"):
        run_synthetic_cell_with_technical_retry(
            production_configuration,
            ExperimentName.SYNTHETIC_MODULE_VALIDATION,
            1,
            None,
            ExecutionRole.DEVELOPMENT,
        )
    assert calls["count"] == retries + 1


def test_technical_retry_does_not_retry_scientific_errors(
    production_configuration: LoadedScientificConfiguration,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"count": 0}

    def counting_wrapper(
        loaded: LoadedScientificConfiguration,
        experiment_name: ExperimentName,
        seed: SeedValue,
        method_name: MethodName | None,
        execution_role: ExecutionRole,
    ) -> SyntheticCellOutcome:
        calls["count"] += 1
        return _always_scientific_error(loaded, experiment_name, seed, method_name, execution_role)

    monkeypatch.setattr(runner, "run_synthetic_cell", counting_wrapper)
    with pytest.raises(ValueError, match="purity violation"):
        run_synthetic_cell_with_technical_retry(
            production_configuration,
            ExperimentName.SYNTHETIC_MODULE_VALIDATION,
            1,
            None,
            ExecutionRole.DEVELOPMENT,
        )
    assert calls["count"] == 1
