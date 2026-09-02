from pathlib import Path

from fedcampaign_emhi.artifacts.records import StatisticalRecord
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import ExecutionRole
from fedcampaign_emhi.experiments.campaigns import (
    PureOrderObservation,
    materialize_pure_order_statistics,
)
from fedcampaign_emhi.experiments.synthetic import PureOrderSeedMetrics


def test_pure_order_statistics_are_materialized_from_confirmatory_outputs(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    observations: list[PureOrderObservation] = []
    for seed in production_configuration.values.randomness.synthetic_confirmatory_roots:
        diagnostic_path = tmp_path / "diagnostics" / f"seed-{seed}.json"
        diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
        diagnostic_path.write_text('{"diagnostic":"verified"}', encoding="utf-8")
        observations.append(
            PureOrderObservation(
                execution_role=ExecutionRole.CONFIRMATORY,
                seed=seed,
                metric=PureOrderSeedMetrics(
                    maximum_proper_subset_standardized_drift=0.0,
                    target_order_standardized_drift=0.75,
                ),
                diagnostic_path=diagnostic_path,
            )
        )

    path = materialize_pure_order_statistics(
        production_configuration,
        tmp_path,
        tuple(observations),
    )

    assert path is not None
    record = StatisticalRecord.model_validate_json(path.read_bytes())
    assert record.independent_unit_count == len(observations)
    assert record.estimate == 0.75
    assert record.raw_p_value is not None
    assert record.confidence_lower == 0.75
    assert record.confidence_upper == 0.75
    assert len(record.source_result_ids) == len(observations)


def test_pure_order_statistics_reject_incomplete_confirmatory_evidence(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    path = materialize_pure_order_statistics(production_configuration, tmp_path, ())

    assert path is None
