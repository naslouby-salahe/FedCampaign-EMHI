from pathlib import Path
from typing import cast

import pytest

from fedcampaign_emhi.analysis.results import (
    PRIMARY_HOLM_STATISTICS,
    materialize_primary_holm_family,
)
from fedcampaign_emhi.artifacts.provenance import (
    material_fingerprint,
    statistical_analysis_boundary_digest,
)
from fedcampaign_emhi.artifacts.records import PrimaryHolmFamilyRecord, StatisticalRecord
from fedcampaign_emhi.artifacts.storage import (
    build_artifact_layout,
    file_sha256,
    payload_digest,
    write_atomic_json,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import SupportState


def _write_statistical_record(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_directory: Path,
    hypothesis_identifier: str,
    raw_p_value: float,
    file_stem: str,
) -> None:
    source_path = experiment_directory / "diagnostics" / f"{file_stem}-source.json"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text('{"diagnostic":"verified"}', encoding="utf-8")
    source_id = source_path.relative_to(repository).as_posix()
    source_digest = file_sha256(source_path)
    payload: YamlNode = {
        "hypothesis_identifier": hypothesis_identifier,
        "metric_name": "test_metric",
        "method_name": "test_method",
        "independent_unit_count": 1,
        "estimate": 0.0,
        "raw_p_value": raw_p_value,
        "adjusted_p_value": None,
        "confidence_level": None,
        "confidence_lower": None,
        "confidence_upper": None,
        "decision": SupportState.SUPPORTED.value,
        "source_result_ids": [source_id],
    }
    record = StatisticalRecord(
        hypothesis_identifier=hypothesis_identifier,
        metric_name="test_metric",
        method_name="test_method",
        independent_unit_count=1,
        estimate=0.0,
        raw_p_value=raw_p_value,
        adjusted_p_value=None,
        confidence_level=None,
        confidence_lower=None,
        confidence_upper=None,
        decision=SupportState.SUPPORTED,
        source_result_ids=(source_id,),
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values), (source_digest,)
        ),
        content_digest=payload_digest(payload),
    )
    path = experiment_directory / "statistics" / f"{file_stem}.json"
    write_atomic_json(
        path,
        cast(YamlNode, record.model_dump(mode="json")),
        repository / "outputs" / "cache" / "staging",
    )


def _write_full_family(
    loaded: LoadedScientificConfiguration, repository: Path, raw_p_values: tuple[float, ...]
) -> None:
    layout = build_artifact_layout(loaded, repository)
    for index, (experiment_name, hypothesis) in enumerate(PRIMARY_HOLM_STATISTICS):
        _write_statistical_record(
            loaded,
            repository,
            layout.experiment_outputs_root(experiment_name),
            hypothesis.value,
            raw_p_values[index],
            f"hypothesis-{index}",
        )


def test_materialize_primary_holm_family_adjusts_across_all_five_hypotheses(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    _write_full_family(production_configuration, tmp_path, (0.001, 0.5, 0.5, 0.5, 0.5))

    path = materialize_primary_holm_family(production_configuration, tmp_path)

    record = PrimaryHolmFamilyRecord.model_validate_json(path.read_bytes())
    assert len(record.results) == len(PRIMARY_HOLM_STATISTICS)
    smallest = next(
        result
        for result in record.results
        if result.hypothesis_identifier == PRIMARY_HOLM_STATISTICS[0][1].value
    )
    assert smallest.raw_p_value == 0.001
    assert smallest.adjusted_p_value == pytest.approx(0.005)
    assert smallest.decision is SupportState.SUPPORTED
    assert record.source_statistical_paths
    assert len(record.source_artifact_hashes) == len(PRIMARY_HOLM_STATISTICS)


def test_materialize_primary_holm_family_requires_every_hypothesis(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    layout = build_artifact_layout(production_configuration, tmp_path)
    experiment_name, hypothesis = PRIMARY_HOLM_STATISTICS[0]
    _write_statistical_record(
        production_configuration,
        tmp_path,
        layout.experiment_outputs_root(experiment_name),
        hypothesis.value,
        0.01,
        "only-hypothesis",
    )

    with pytest.raises(FileNotFoundError):
        materialize_primary_holm_family(production_configuration, tmp_path)


def test_materialize_primary_holm_family_rejects_stale_source_lineage(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    _write_full_family(production_configuration, tmp_path, (0.01, 0.5, 0.5, 0.5, 0.5))
    layout = build_artifact_layout(production_configuration, tmp_path)
    experiment_name = PRIMARY_HOLM_STATISTICS[0][0]
    source_path = (
        layout.experiment_outputs_root(experiment_name) / "diagnostics" / "hypothesis-0-source.json"
    )
    source_path.write_text('{"diagnostic":"tampered"}', encoding="utf-8")

    with pytest.raises(ValueError, match="stale source lineage"):
        materialize_primary_holm_family(production_configuration, tmp_path)
