from pathlib import Path

from fedcampaign_emhi.artifacts.records import StatisticalRecord
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import ExecutionRole
from fedcampaign_emhi.experiments.campaigns import (
    SelfExplanationObservation,
    materialize_self_explanation_statistics,
)
from fedcampaign_emhi.experiments.synthetic import SelfExplanationSeedMetrics


def test_self_explanation_statistics_are_materialized_from_confirmatory_outputs(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    observations: list[SelfExplanationObservation] = []
    for seed in production_configuration.values.randomness.synthetic_confirmatory_roots:
        diagnostic_path = tmp_path / "diagnostics" / f"seed-{seed}.json"
        diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
        diagnostic_path.write_text('{"diagnostic":"verified"}', encoding="utf-8")
        observations.append(
            SelfExplanationObservation(
                execution_role=ExecutionRole.CONFIRMATORY,
                seed=seed,
                metric=SelfExplanationSeedMetrics(
                    primary_exact_nuisance_derivative=0.0,
                    primary_attenuation_contrast=0.25,
                ),
                diagnostic_path=diagnostic_path,
            )
        )

    path = materialize_self_explanation_statistics(
        production_configuration,
        tmp_path,
        tuple(observations),
    )

    assert path is not None
    record = StatisticalRecord.model_validate_json(path.read_bytes())
    assert record.independent_unit_count == len(observations)
    assert record.estimate == 0.25
    assert record.raw_p_value is not None
    assert record.confidence_lower == 0.25
    assert record.confidence_upper == 0.25
    assert len(record.source_result_ids) == len(observations)


def test_self_explanation_statistics_reject_incomplete_confirmatory_evidence(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    path = materialize_self_explanation_statistics(production_configuration, tmp_path, ())

    assert path is None
