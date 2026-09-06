from pathlib import Path
from typing import cast

from fedcampaign_emhi.analysis.results import build_seed_summary
from fedcampaign_emhi.artifacts.provenance import material_fingerprint
from fedcampaign_emhi.artifacts.storage import build_artifact_layout, write_atomic_json
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import ExecutionRole, ExperimentName, MethodName
from fedcampaign_emhi.domain.types import SeedValue
from fedcampaign_emhi.experiments.seed_statistics import materialize_seed_statistics


def _write_summary(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    role: ExecutionRole,
    seed: SeedValue,
    method_value: float = 0.5,
) -> None:
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    summary = build_seed_summary(
        experiment_name=experiment_name,
        execution_role=role,
        method_name=MethodName.FULL_FEDCAMPAIGN_EMHI,
        reference_method_name=None,
        metric_name="strict_odi_rate",
        seed=seed,
        method_values=(method_value,),
        reference_values=None,
        source_evaluation_ids=(),
        dependency_fingerprint=material_fingerprint("test-digest", ()),
    )
    path = (
        root
        / "metrics"
        / "seed-summaries"
        / role.value
        / "full-fedcampaign-emhi"
        / f"seed-{seed}.json"
    )
    write_atomic_json(path, cast(YamlNode, summary.model_dump(mode="json")), repository / "staging")


def test_confirmatory_seeds_within_tolerance_are_synthesized(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    experiment_name = ExperimentName.PRIMARY_STRICT_ODI_EVALUATION
    confirmatory = production_configuration.values.randomness.real_confirmatory_roots
    for seed in confirmatory:
        _write_summary(
            production_configuration, tmp_path, experiment_name, ExecutionRole.CONFIRMATORY, seed
        )
    paths = materialize_seed_statistics(production_configuration, tmp_path, experiment_name)
    assert paths


def test_missing_confirmatory_seeds_above_tolerance_are_excluded(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    experiment_name = ExperimentName.PRIMARY_STRICT_ODI_EVALUATION
    confirmatory = production_configuration.values.randomness.real_confirmatory_roots
    for seed in confirmatory[1:]:
        _write_summary(
            production_configuration, tmp_path, experiment_name, ExecutionRole.CONFIRMATORY, seed
        )
    paths = materialize_seed_statistics(production_configuration, tmp_path, experiment_name)
    assert paths == ()


def test_seed_statistics_use_one_sided_positive_direction_test(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    from fedcampaign_emhi.artifacts.records import StatisticalRecord

    experiment_name = ExperimentName.PRIMARY_STRICT_ODI_EVALUATION
    confirmatory = production_configuration.values.randomness.real_confirmatory_roots
    for seed in confirmatory:
        _write_summary(
            production_configuration,
            tmp_path,
            experiment_name,
            ExecutionRole.CONFIRMATORY,
            seed,
            method_value=-0.9,
        )
    paths = materialize_seed_statistics(production_configuration, tmp_path, experiment_name)
    assert paths
    record = StatisticalRecord.model_validate_json(paths[0].read_bytes())
    assert record.estimate < 0.0
    assert record.raw_p_value == 1.0
