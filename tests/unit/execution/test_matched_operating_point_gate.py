from pathlib import Path
from typing import cast

import pytest

from fedcampaign_emhi.analysis.results import build_seed_summary
from fedcampaign_emhi.artifacts.records import StatisticalRecord
from fedcampaign_emhi.artifacts.storage import (
    build_artifact_layout,
    method_artifact_stem,
    write_atomic_json,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import (
    ExecutionRole,
    ExperimentName,
    MethodName,
    PrimaryHolmHypothesis,
)
from fedcampaign_emhi.experiments.seed_statistics import materialize_confirmatory_odi_inferences

_EXPERIMENT = ExperimentName.PRIMARY_STRICT_ODI_EVALUATION
_HYPOTHESIS = PrimaryHolmHypothesis.PRIMARY_ODI_ADVANTAGE_OVER_ORDER_AT_MOST_TWO_EMHI


def _write_summaries(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    method_name: MethodName,
    value: float,
) -> None:
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(_EXPERIMENT)
    stem = method_artifact_stem(method_name)
    for index, seed in enumerate(loaded.values.randomness.real_confirmatory_roots):
        summary = build_seed_summary(
            experiment_name=_EXPERIMENT,
            execution_role=ExecutionRole.CONFIRMATORY,
            method_name=method_name,
            reference_method_name=None,
            metric_name="strict_odi_rate",
            seed=seed,
            method_values=(value,),
            reference_values=None,
            source_evaluation_ids=(f"evaluation-{stem}-{index}",),
            dependency_fingerprint=f"{index:064d}",
        )
        path = (
            root
            / "metrics"
            / "seed-summaries"
            / ExecutionRole.CONFIRMATORY.value
            / stem
            / f"seed-{seed}.json"
        )
        write_atomic_json(
            path,
            cast(YamlNode, summary.model_dump(mode="json")),
            repository / "outputs" / "cache" / "staging",
        )


def _write_raw_evaluation(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    method_name: MethodName,
    threshold_present: bool,
) -> None:
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(_EXPERIMENT)
    stem = method_artifact_stem(method_name)
    for seed in loaded.values.randomness.real_confirmatory_roots:
        payload: YamlNode = {
            "calibration": {
                "global": {
                    "threshold": 5.0 if threshold_present else None,
                    "heldout_upper_pfa": 0.01 if threshold_present else None,
                }
            }
        }
        path = (
            root
            / "evaluations"
            / "raw"
            / ExecutionRole.CONFIRMATORY.value
            / stem
            / f"seed-{seed}.json"
        )
        write_atomic_json(
            path,
            payload,
            repository / "outputs" / "cache" / "staging",
        )


def _hypothesis_path(loaded: LoadedScientificConfiguration, repository: Path) -> Path:
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(_EXPERIMENT)
    identifier = _HYPOTHESIS.value.lower().replace(" ", "-")
    return root / "statistics" / "tests" / f"{identifier}.json"


def _write_complete_evidence(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    full_threshold: bool,
    comparator_threshold: bool,
) -> None:
    _write_summaries(loaded, repository, MethodName.FULL_FEDCAMPAIGN_EMHI, 0.9)
    _write_summaries(loaded, repository, MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI, 0.2)
    _write_raw_evaluation(loaded, repository, MethodName.FULL_FEDCAMPAIGN_EMHI, full_threshold)
    _write_raw_evaluation(
        loaded,
        repository,
        MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI,
        comparator_threshold,
    )


def _materialize(loaded: LoadedScientificConfiguration, repository: Path) -> None:
    materialize_confirmatory_odi_inferences(
        loaded, repository, _EXPERIMENT, primary_not_tested=False
    )


def test_odi_advantage_requires_matched_eligible_operating_points(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    _write_complete_evidence(
        production_configuration, tmp_path, full_threshold=True, comparator_threshold=True
    )

    _materialize(production_configuration, tmp_path)

    record = StatisticalRecord.model_validate_json(
        _hypothesis_path(production_configuration, tmp_path).read_bytes()
    )
    assert record.raw_p_value is not None
    assert record.estimate == pytest.approx(0.7)


def test_odi_advantage_null_when_comparator_operating_point_unavailable(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    _write_complete_evidence(
        production_configuration, tmp_path, full_threshold=True, comparator_threshold=False
    )

    _materialize(production_configuration, tmp_path)

    record = StatisticalRecord.model_validate_json(
        _hypothesis_path(production_configuration, tmp_path).read_bytes()
    )
    assert record.hypothesis_identifier == _HYPOTHESIS.value
    assert record.raw_p_value is None
    assert record.meets_threshold is False
