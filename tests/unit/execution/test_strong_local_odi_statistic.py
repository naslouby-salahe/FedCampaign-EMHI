from hashlib import sha256
from pathlib import Path
from typing import cast

import pytest

from fedcampaign_emhi.analysis.results import PRIMARY_HOLM_STATISTICS, build_seed_summary
from fedcampaign_emhi.artifacts.records import StatisticalRecord
from fedcampaign_emhi.artifacts.storage import build_artifact_layout, write_atomic_json
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import (
    ExecutionRole,
    ExperimentName,
    MethodName,
    PrimaryHolmHypothesis,
)
from fedcampaign_emhi.experiments.seed_statistics import materialize_strong_local_odi_statistic


def _write_raw_evaluation(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    seed: int,
    *,
    threshold_present: bool,
) -> None:
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE)
    payload: YamlNode = {
        "calibration": {
            "global": {
                "threshold": 10.0 if threshold_present else None,
                "heldout_upper_pfa": 0.01 if threshold_present else None,
            }
        }
    }
    path = (
        root
        / "evaluations"
        / "raw"
        / ExecutionRole.CONFIRMATORY.value
        / "full-fedcampaign-emhi"
        / f"seed-{seed}.json"
    )
    write_atomic_json(
        path,
        payload,
        repository / "outputs" / "cache" / "staging",
    )


def _write_odi_summary(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    seed: int,
    method_value: float,
    summary_index: int,
) -> Path:
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE)
    summary = build_seed_summary(
        experiment_name=ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE,
        execution_role=ExecutionRole.CONFIRMATORY,
        method_name=MethodName.FULL_FEDCAMPAIGN_EMHI,
        reference_method_name=None,
        metric_name="strict_odi_rate",
        seed=seed,
        method_values=(method_value,),
        reference_values=None,
        source_evaluation_ids=(f"evaluation-{summary_index}",),
        dependency_fingerprint=sha256(f"fingerprint-{summary_index}".encode()).hexdigest(),
    )
    summary_path = (
        root
        / "metrics"
        / "seed-summaries"
        / ExecutionRole.CONFIRMATORY.value
        / "full-fedcampaign-emhi"
        / f"seed-{seed}.json"
    )
    write_atomic_json(
        summary_path,
        cast(YamlNode, summary.model_dump(mode="json")),
        repository / "outputs" / "cache" / "staging",
    )
    return summary_path


def _write_full_confirmatory_set(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    value: float,
    *,
    threshold_present: bool,
) -> None:
    expected = loaded.values.randomness.real_confirmatory_roots
    for index, seed in enumerate(expected):
        _write_raw_evaluation(loaded, repository, seed, threshold_present=threshold_present)
        _write_odi_summary(loaded, repository, seed, value, index)


def test_strong_local_odi_statistic_is_a_primary_holm_hypothesis(
    production_configuration: LoadedScientificConfiguration,
) -> None:
    assert (
        ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE,
        PrimaryHolmHypothesis.STRONG_LOCAL_ODI_ABOVE_MINIMUM,
    ) in PRIMARY_HOLM_STATISTICS


def test_materialize_strong_local_odi_above_minimum_positive_shifts(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    _write_full_confirmatory_set(production_configuration, tmp_path, 0.3, threshold_present=True)

    path = materialize_strong_local_odi_statistic(production_configuration, tmp_path)

    assert path is not None
    record = StatisticalRecord.model_validate_json(path.read_bytes())
    assert record.hypothesis_identifier == PrimaryHolmHypothesis.STRONG_LOCAL_ODI_ABOVE_MINIMUM
    assert record.raw_p_value == pytest.approx(1 / 2**10)
    assert record.meets_threshold is True
    assert record.estimate == pytest.approx(0.1)


def test_materialize_strong_local_odi_negative_shifts_never_significant(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    _write_full_confirmatory_set(production_configuration, tmp_path, 0.15, threshold_present=True)

    path = materialize_strong_local_odi_statistic(production_configuration, tmp_path)

    assert path is not None
    record = StatisticalRecord.model_validate_json(path.read_bytes())
    assert record.raw_p_value == 1.0
    assert record.meets_threshold is False


def test_materialize_strong_local_odi_requires_complete_confirmatory_seeds(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    expected = production_configuration.values.randomness.real_confirmatory_roots
    for index, seed in enumerate(expected[:-1]):
        _write_raw_evaluation(production_configuration, tmp_path, seed, threshold_present=True)
        _write_odi_summary(production_configuration, tmp_path, seed, 0.3, index)

    assert materialize_strong_local_odi_statistic(production_configuration, tmp_path) is None


def test_materialize_strong_local_odi_null_when_operating_point_unavailable(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    _write_full_confirmatory_set(production_configuration, tmp_path, 0.3, threshold_present=False)

    path = materialize_strong_local_odi_statistic(production_configuration, tmp_path)

    assert path is not None
    record = StatisticalRecord.model_validate_json(path.read_bytes())
    assert record.hypothesis_identifier == PrimaryHolmHypothesis.STRONG_LOCAL_ODI_ABOVE_MINIMUM
    assert record.raw_p_value is None
    assert record.meets_threshold is False


def test_materialize_strong_local_odi_skips_when_not_tested_placeholder_exists(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    layout = build_artifact_layout(production_configuration, tmp_path)
    root = layout.experiment_outputs_root(ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE)
    placeholder = root / "statistics" / "tests" / "primary-holm-not-tested.json"
    write_atomic_json(
        placeholder,
        {"hypothesis_identifier": PrimaryHolmHypothesis.STRONG_LOCAL_ODI_ABOVE_MINIMUM.value},
        repository_staging(tmp_path),
    )

    assert materialize_strong_local_odi_statistic(production_configuration, tmp_path) is None


def repository_staging(repository: Path) -> Path:
    return repository / "outputs" / "cache" / "staging"
