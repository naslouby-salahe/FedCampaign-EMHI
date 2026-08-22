from pathlib import Path

from fedcampaign_emhi.comparators.composition import select_strongest_comparator
from fedcampaign_emhi.domain.enums import MethodName
from fedcampaign_emhi.emhi.innovations import center_and_scale_atom, sample_standard_deviation
from fedcampaign_emhi.models.autoencoder import (
    autoencoder_anomaly_scores,
    autoencoder_layer_widths,
    batch_permutation_seed,
)
from fedcampaign_emhi.models.isolation_forest import isolation_forest_anomaly_scores


def test_autoencoder_width_contract() -> None:
    assert autoencoder_layer_widths(66) == (66, 32, 8, 32, 66)


def test_autoencoder_scores_reconstruction_error() -> None:
    fit_rows = tuple((float(index), float(index)) for index in range(16))
    score_rows = ((1.0, 1.0), (80.0, 80.0))
    scores = autoencoder_anomaly_scores(
        fit_rows, score_rows, 0.01, 0.9, 0.999, 1.0e-08, 0.0, 8, 2, 7, "10.0.0.1"
    )
    assert scores[1] >= 0.0
    assert scores[0] >= 0.0
    first = batch_permutation_seed(7, "10.0.0.1", 0)
    second = batch_permutation_seed(7, "10.0.0.1", 0)
    later = batch_permutation_seed(7, "10.0.0.1", 1)
    assert first == second
    assert first != later


def test_isolation_forest_locks_non_configurable_library_options() -> None:
    source = Path(isolation_forest_anomaly_scores.__code__.co_filename).read_text(encoding="utf-8")
    assert "bootstrap=False" in source
    assert "warm_start=False" in source
    assert 'contamination="auto"' in source


def test_isolation_forest_scores_larger_outliers() -> None:
    fit_rows = tuple((float(index), 0.0) for index in range(20))
    score_rows = ((0.0, 0.0), (100.0, 0.0))
    scores = isolation_forest_anomaly_scores(fit_rows, score_rows, 10, 16, 1.0, 1, 7)
    assert scores[1] > scores[0]


def test_sample_standard_deviation_uses_n_minus_one() -> None:
    assert abs(sample_standard_deviation((1.0, 3.0)) - (2.0**0.5)) < 1.0e-12
    scaled = center_and_scale_atom((3.0,), (1.0,), (2.0,), 1.0e-06)
    assert abs(scaled[0] - 1.0) < 1.0e-12


def test_strongest_comparator_prefers_lower_error_then_runtime() -> None:
    selected = select_strongest_comparator(
        (
            MethodName.CONDITIONAL_PAIR_DEPENDENCE,
            MethodName.CONNECTED_INFORMATION_REFERENCE,
        ),
        (0.2, 0.2),
        (3.0, 1.0),
        0.01,
        1.0e-06,
    )
    assert selected is MethodName.CONNECTED_INFORMATION_REFERENCE
