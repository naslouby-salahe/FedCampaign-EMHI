from pathlib import Path
from typing import cast

from fedcampaign_emhi.analysis.results import build_seed_summary
from fedcampaign_emhi.artifacts.records import PrimaryStrictOdiSupportRecord
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
    KnownArtifactOutputFilename,
    MethodName,
)
from fedcampaign_emhi.experiments.seed_statistics import materialize_confirmatory_odi_inferences

_EXPERIMENT = ExperimentName.PRIMARY_STRICT_ODI_EVALUATION


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
    operational_lead_epochs: float | None,
) -> None:
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(_EXPERIMENT)
    stem = method_artifact_stem(method_name)
    campaigns: list[YamlNode] = (
        []
        if operational_lead_epochs is None
        else [{"strict_odi": 1, "operational_lead_epochs": operational_lead_epochs}]
    )
    for seed in loaded.values.randomness.real_confirmatory_roots:
        payload: YamlNode = {
            "calibration": {"global": {"threshold": 5.0, "heldout_upper_pfa": 0.01}},
            "campaigns": campaigns,
        }
        path = (
            root
            / "evaluations"
            / "raw"
            / ExecutionRole.CONFIRMATORY.value
            / stem
            / f"seed-{seed}.json"
        )
        write_atomic_json(path, payload, repository / "outputs" / "cache" / "staging")


def _support_path(loaded: LoadedScientificConfiguration, repository: Path) -> Path:
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(_EXPERIMENT)
    return root / "statistics" / "effects" / KnownArtifactOutputFilename.PRIMARY_STRICT_ODI_SUPPORT


def _prepare(
    loaded: LoadedScientificConfiguration, repository: Path, operational_lead_epochs: float | None
) -> None:
    _write_summaries(loaded, repository, MethodName.FULL_FEDCAMPAIGN_EMHI, 0.9)
    _write_summaries(loaded, repository, MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI, 0.2)
    _write_raw_evaluation(
        loaded, repository, MethodName.FULL_FEDCAMPAIGN_EMHI, operational_lead_epochs
    )
    _write_raw_evaluation(
        loaded, repository, MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI, 5.0
    )
    materialize_confirmatory_odi_inferences(
        loaded, repository, _EXPERIMENT, primary_not_tested=False
    )


def test_primary_strict_odi_support_passes_when_every_criterion_meets_its_threshold(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    materiality = production_configuration.values.materiality.primary_real
    _prepare(
        production_configuration,
        tmp_path,
        operational_lead_epochs=materiality.minimum_median_operational_lead_epochs + 1.0,
    )

    record = PrimaryStrictOdiSupportRecord.model_validate_json(
        _support_path(production_configuration, tmp_path).read_bytes()
    )

    assert record.mean_strict_odi_rate == 0.9
    assert (
        record.odi_rate_advantage >= materiality.minimum_odi_rate_advantage_over_order_at_most_two
    )
    assert (
        record.median_operational_lead_epochs
        == materiality.minimum_median_operational_lead_epochs + 1.0
    )
    assert record.heldout_pfa_meets_target is True
    assert record.both_methods_operating_point_eligible is True
    assert record.meets_threshold is True


def test_primary_strict_odi_support_fails_when_operational_lead_is_below_threshold(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    materiality = production_configuration.values.materiality.primary_real
    _prepare(
        production_configuration,
        tmp_path,
        operational_lead_epochs=materiality.minimum_median_operational_lead_epochs - 1.0,
    )

    record = PrimaryStrictOdiSupportRecord.model_validate_json(
        _support_path(production_configuration, tmp_path).read_bytes()
    )

    assert record.meets_threshold is False


def test_primary_strict_odi_support_fails_with_no_favorable_substitution_when_no_stops_occur(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    _prepare(production_configuration, tmp_path, operational_lead_epochs=None)

    record = PrimaryStrictOdiSupportRecord.model_validate_json(
        _support_path(production_configuration, tmp_path).read_bytes()
    )

    assert record.strict_odi_success_count == 0
    assert record.median_operational_lead_epochs is None
    assert record.meets_threshold is False
