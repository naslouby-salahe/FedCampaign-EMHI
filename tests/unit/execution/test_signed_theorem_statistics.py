from pathlib import Path

from fedcampaign_emhi.artifacts.records import (
    FiniteHorizonAggregationRecord,
    StatisticalRecord,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import ExecutionRole, SupportState
from fedcampaign_emhi.experiments.calibration import FiniteHorizonSeedMetrics
from fedcampaign_emhi.experiments.campaigns import (
    FiniteHorizonObservation,
    SignedTheoremObservation,
    materialize_finite_horizon_statistics,
    materialize_signed_theorem_statistics,
)
from fedcampaign_emhi.synthetic.sequential import SignedTheoremSeedMetrics


def test_signed_theorem_statistics_materialize_one_sided_restricted_arl_bound(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    observations: list[SignedTheoremObservation] = []
    for seed in production_configuration.values.randomness.synthetic_confirmatory_roots:
        diagnostic_path = tmp_path / "diagnostics" / f"seed-{seed}.json"
        diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
        diagnostic_path.write_text('{"diagnostic":"verified"}', encoding="utf-8")
        observations.append(
            SignedTheoremObservation(
                execution_role=ExecutionRole.CONFIRMATORY,
                seed=seed,
                metric=SignedTheoremSeedMetrics(
                    restricted_arl=1000.0,
                    stopped_trajectory_count=0,
                    trajectory_count=100,
                    maximum_trajectory_epochs=1000,
                    threshold=1000.0,
                    compensator=0.125,
                ),
                diagnostic_path=diagnostic_path,
            )
        )

    path = materialize_signed_theorem_statistics(
        production_configuration,
        tmp_path,
        tuple(observations),
    )

    assert path is not None
    record = StatisticalRecord.model_validate_json(path.read_bytes())
    assert record.estimate == 1000.0
    assert record.confidence_lower == 1000.0
    assert record.confidence_upper is None
    assert record.decision is SupportState.SUPPORTED


def test_signed_theorem_statistics_reject_incomplete_confirmatory_evidence(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    assert materialize_signed_theorem_statistics(production_configuration, tmp_path, ()) is None


def test_finite_horizon_statistics_fail_closed_when_an_operating_point_is_unavailable(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    observations: list[FiniteHorizonObservation] = []
    for index, seed in enumerate(
        production_configuration.values.randomness.synthetic_confirmatory_roots
    ):
        diagnostic_path = tmp_path / "diagnostics" / f"finite-{seed}.json"
        diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
        diagnostic_path.write_text('{"diagnostic":"verified"}', encoding="utf-8")
        observations.append(
            FiniteHorizonObservation(
                execution_role=ExecutionRole.CONFIRMATORY,
                seed=seed,
                metric=FiniteHorizonSeedMetrics(
                    calibrated_threshold=None if index == 0 else 1000.0,
                    calibration_horizon_count=200,
                    heldout_horizon_count=1000,
                    heldout_false_stop_count=0,
                    heldout_upper_pfa=None if index == 0 else 0.01,
                ),
                diagnostic_path=diagnostic_path,
            )
        )

    path = materialize_finite_horizon_statistics(
        production_configuration, tmp_path, tuple(observations)
    )

    assert path is not None
    record = FiniteHorizonAggregationRecord.model_validate_json(path.read_bytes())
    assert record.operating_point_unavailable_count == 1
    assert record.decision is SupportState.NOT_SUPPORTED
