from collections.abc import Iterable

import pytest

from fedcampaign_emhi.comparators.conditioning import (
    CONDITIONED_COMPARATOR_METHODS,
    ComparatorConditioningModel,
    ComparatorEpochPanel,
    comparator_panel,
    condition_epoch_ranks,
    fit_comparator_conditioning,
)
from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import DatasetName, MethodName


def _panel(rows: list[tuple[float, ...]]) -> ComparatorEpochPanel:
    return comparator_panel(tuple(range(len(rows))), tuple(rows))


def _two_cell_panel(epoch_count: int) -> list[tuple[float, ...]]:
    rows: list[tuple[float, ...]] = []
    for index in range(epoch_count):
        member = 0.25 + 0.02 * (index % 3) if (index - 1) % 2 == 0 else 0.75 + 0.02 * (index % 3)
        complement_low = 0.1 if index % 2 == 0 else 0.9
        rows.append((member, 0.5, complement_low, 0.5, 0.5, 0.5))
    return rows


def _pair_model(
    loaded: LoadedScientificConfiguration,
    rows: list[tuple[float, ...]],
    nuisance_epochs: Iterable[int],
) -> ComparatorConditioningModel | None:
    return fit_comparator_conditioning(
        loaded.values,
        DatasetName.TON_IOT_NETWORK,
        _panel(rows),
        tuple(nuisance_epochs),
        2,
        ("c0", "c1", "c2", "c3", "c4", "c5"),
    )


def test_panel_requires_aligned_epochs_and_rows() -> None:
    with pytest.raises(ValueError):
        comparator_panel((1, 2), ((0.1, 0.2),))


def test_pair_conditioning_is_cell_conditional_not_marginal() -> None:
    loaded = load_production_configuration()
    training_rows = _two_cell_panel(480)
    model = _pair_model(loaded, training_rows, range(2, 242))
    assert model is not None
    assert len(model.centroids) == 2

    evaluation_rows: list[tuple[float, ...]] = []
    for index in range(480):
        complement_low = 0.1 if index % 2 == 0 else 0.9
        evaluation_rows.append((0.5, 0.5, complement_low, 0.5, 0.5, 0.5))
    evaluation_panel = _panel(evaluation_rows)
    conditioned: list[float] = []
    for epoch in range(243, 400):
        row = condition_epoch_ranks(loaded.values, evaluation_panel, epoch, model)
        assert row is not None
        conditioned.append(row[0])
    low_cell: list[float] = [value for value in conditioned if value > 0.9]
    high_cell: list[float] = [value for value in conditioned if value < 0.1]
    assert low_cell and high_cell
    # a mid query that is above every low-cell reference but below every high-cell
    # reference must be mapped to opposite extremes by cell, never to the marginal ~0.5
    assert not any(0.3 < value < 0.7 for value in conditioned)


def test_pair_conditioning_is_deterministic() -> None:
    loaded = load_production_configuration()
    rows = _two_cell_panel(480)
    assert _pair_model(loaded, rows, range(2, 242)) == _pair_model(loaded, rows, range(2, 242))


def test_order_three_unavailable_on_four_client_panel() -> None:
    loaded = load_production_configuration()
    rows = _two_cell_panel(480)
    model = fit_comparator_conditioning(
        loaded.values,
        DatasetName.TON_IOT_NETWORK,
        _panel([row[:4] for row in rows]),
        tuple(range(2, 122)),
        3,
        ("c0", "c1", "c2", "c3"),
    )
    assert model is None


def test_conditioning_requires_minimum_nuisance_rows() -> None:
    loaded = load_production_configuration()
    rows = _two_cell_panel(40)
    assert _pair_model(loaded, rows, range(1, 3)) is None


def test_first_epoch_without_lag_has_no_conditioned_rank() -> None:
    loaded = load_production_configuration()
    rows = _two_cell_panel(480)
    model = _pair_model(loaded, rows, range(2, 242))
    assert model is not None
    assert condition_epoch_ranks(loaded.values, _panel(rows), 0, model) is None


def test_conditioned_method_set_matches_roadmap_families() -> None:
    assert MethodName.CONDITIONAL_PAIR_DEPENDENCE in CONDITIONED_COMPARATOR_METHODS
    assert MethodName.EXCLUSION_MATCHED_LANCASTER_TRIPLE in CONDITIONED_COMPARATOR_METHODS
    assert MethodName.EXCLUSION_MATCHED_CONDITIONAL_HOFD in CONDITIONED_COMPARATOR_METHODS
    assert MethodName.CONNECTED_INFORMATION_REFERENCE in CONDITIONED_COMPARATOR_METHODS
    assert MethodName.CONDITIONAL_LOG_LINEAR_REFERENCE in CONDITIONED_COMPARATOR_METHODS
    assert len(CONDITIONED_COMPARATOR_METHODS) == 5
