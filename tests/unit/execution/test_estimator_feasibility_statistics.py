from pathlib import Path

from fedcampaign_emhi.artifacts.records import EstimatorFeasibilityAggregationRecord
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import ExecutionRole, SupportState
from fedcampaign_emhi.experiments.campaigns import (
    EstimatorFeasibilityObservation,
    materialize_estimator_feasibility_statistics,
)
from fedcampaign_emhi.experiments.synthetic import EstimatorFeasibilitySeedMetrics
from fedcampaign_emhi.synthetic.feasibility import EstimatorFeasibilityMetrics


def test_estimator_feasibility_statistics_aggrecriterion_primary_confirmatory_metrics(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    observations: list[EstimatorFeasibilityObservation] = []
    for seed in production_configuration.values.randomness.synthetic_confirmatory_roots:
        diagnostic_path = tmp_path / "diagnostics" / f"seed-{seed}.json"
        diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
        diagnostic_path.write_text('{"diagnostic":"verified"}', encoding="utf-8")
        observations.append(
            EstimatorFeasibilityObservation(
                execution_role=ExecutionRole.CONFIRMATORY,
                seed=seed,
                metric=EstimatorFeasibilitySeedMetrics(
                    EstimatorFeasibilityMetrics(0.01, 0.01, 0.01, 1.0, 0.0, 1.0, False, 0.0)
                ),
                diagnostic_path=diagnostic_path,
            )
        )

    path = materialize_estimator_feasibility_statistics(
        production_configuration,
        tmp_path,
        tuple(observations),
    )

    assert path is not None
    record = EstimatorFeasibilityAggregationRecord.model_validate_json(path.read_bytes())
    assert record.independent_unit_count == len(observations)
    assert record.mean_context_coverage == 1.0
    assert record.pooled_numerical_failure_rate == 0.0
    assert record.decision is SupportState.SUPPORTED


def test_estimator_feasibility_statistics_reject_incomplete_confirmatory_evidence(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    assert (
        materialize_estimator_feasibility_statistics(production_configuration, tmp_path, ()) is None
    )
