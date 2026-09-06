from pathlib import Path

from fedcampaign_emhi.artifacts.records import StrongComparatorCompositionRecord
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import MethodName
from fedcampaign_emhi.experiments.calibration import (
    CompositionCandidateObservation,
    CompositionCandidateSeedMetrics,
    evaluate_composition_candidate_seed,
)
from fedcampaign_emhi.experiments.synthetic_execution import (
    materialize_strong_comparator_composition_selection,
)


def _small_configuration(loaded: LoadedScientificConfiguration) -> LoadedScientificConfiguration:
    sample_sizes = loaded.values.synthetic.sample_sizes.model_copy(
        update={
            "pure_order_independent_evaluation_samples_per_condition_seed": 5,
            "finite_horizon_calibration_horizons_per_seed": 2,
            "finite_horizon_heldout_null_horizons_per_seed": 2,
        }
    )
    synthetic = loaded.values.synthetic.model_copy(update={"sample_sizes": sample_sizes})
    campaign = loaded.values.campaign.model_copy(update={"evaluation_horizon_epochs": 3})
    pure_order = loaded.values.experiments.pure_order_separation_validation.model_copy(
        update={"primary_client_count": 4}
    )
    experiments = loaded.values.experiments.model_copy(
        update={"pure_order_separation_validation": pure_order}
    )
    config = loaded.values.model_copy(
        update={"synthetic": synthetic, "campaign": campaign, "experiments": experiments}
    )
    return loaded.model_copy(update={"values": config})


def test_composition_candidate_seed_calibrates_on_small_configuration(
    production_configuration: LoadedScientificConfiguration,
) -> None:
    small = _small_configuration(production_configuration)

    metrics = evaluate_composition_candidate_seed(
        small.values, MethodName.CONDITIONAL_PAIR_DEPENDENCE, 11
    )

    assert metrics.calibration_horizon_count == 2
    assert metrics.heldout_horizon_count == 2
    assert metrics.heldout_false_stop_count <= metrics.heldout_horizon_count
    assert metrics.scoring_runtime_seconds >= 0.0
    if metrics.calibrated_threshold is not None:
        assert (
            metrics.calibrated_threshold
            in small.values.evidence.calibrated_finite_horizon.threshold_candidates
        )


def test_composition_candidate_seed_rejects_non_native_order_method(
    production_configuration: LoadedScientificConfiguration,
) -> None:
    small = _small_configuration(production_configuration)
    try:
        evaluate_composition_candidate_seed(small.values, MethodName.RAW_MEAN_RANK_FUSION, 11)
    except ValueError as error:
        assert "native-order" in str(error)
    else:
        raise AssertionError("expected ValueError for a non-native-order candidate")


def test_materialize_strong_comparator_composition_selection_writes_eligible_candidate(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    method_name = MethodName.CONDITIONAL_PAIR_DEPENDENCE
    seeds = production_configuration.values.randomness.synthetic_development_roots
    observations: list[CompositionCandidateObservation] = []
    for index, seed in enumerate(seeds):
        diagnostic_path = tmp_path / "diagnostics" / f"seed-{seed}.json"
        diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
        diagnostic_path.write_text('{"diagnostic":"verified"}', encoding="utf-8")
        observations.append(
            CompositionCandidateObservation(
                method_name=method_name,
                seed=seed,
                standardized_target_order_error=0.01,
                metric=CompositionCandidateSeedMetrics(
                    calibrated_threshold=5.0,
                    calibration_horizon_count=200,
                    heldout_horizon_count=100,
                    heldout_false_stop_count=0,
                    scoring_runtime_seconds=0.001 + index * 1e-6,
                ),
                diagnostic_path=diagnostic_path,
            )
        )

    path = materialize_strong_comparator_composition_selection(
        production_configuration,
        tmp_path,
        tuple(observations),
    )

    assert path is not None
    record = StrongComparatorCompositionRecord.model_validate_json(path.read_bytes())
    assert record.selected_method is method_name
    assert method_name in record.eligible_candidates


def test_materialize_strong_comparator_composition_selection_rejects_incomplete_seeds(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    assert (
        materialize_strong_comparator_composition_selection(production_configuration, tmp_path, ())
        is None
    )
