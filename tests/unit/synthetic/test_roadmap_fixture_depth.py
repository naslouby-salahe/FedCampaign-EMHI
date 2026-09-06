from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.emhi.contexts import (
    histogram_bin_index,
    minimum_support_epochs_for_order,
)
from fedcampaign_emhi.emhi.projection import select_ridge_penalty


def test_histogram_normalized_mass_vector_fixture() -> None:
    loaded = load_production_configuration()
    bins = loaded.values.context.outside_histogram_bin_count
    indices = tuple(histogram_bin_index(rank, bins) for rank in (0.01, 0.13, 0.99))
    masses = tuple(indices.count(index) / len(indices) for index in range(bins))
    assert masses == (1 / 3, 1 / 3, 0.0, 0.0, 0.0, 0.0, 0.0, 1 / 3)


def test_ridge_tie_prefers_larger_penalty_fixture() -> None:
    loaded = load_production_configuration()
    selected = select_ridge_penalty(
        (0.01, 0.1),
        (0.05, 0.05),
        loaded.values.projection.selection_tie_tolerance_mse,
    )
    assert selected == 0.1


def test_abstention_boundary_matches_configured_order_three_minimum() -> None:
    loaded = load_production_configuration()
    context = loaded.values.context
    minimum = minimum_support_epochs_for_order(
        CoalitionOrder.THREE,
        context.minimum_support_epochs.order_one,
        context.minimum_support_epochs.order_two,
        context.minimum_support_epochs.order_three,
    )
    assert minimum == context.minimum_support_epochs.order_three
    assert 399 < minimum <= 400
