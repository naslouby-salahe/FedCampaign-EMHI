from pathlib import Path
from typing import cast

from fedcampaign_emhi.analysis.summaries import build_seed_summary
from fedcampaign_emhi.artifacts.paths import build_artifact_layout
from fedcampaign_emhi.artifacts.provenance import material_fingerprint
from fedcampaign_emhi.artifacts.storage import write_atomic_json
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import ExecutionRole, ExperimentName, MethodName
from fedcampaign_emhi.domain.types import SeedValue
from fedcampaign_emhi.execution.runner import materialize_seed_statistics


def _write_summary(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    role: ExecutionRole,
    seed: SeedValue,
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
        method_values=(0.5,),
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
