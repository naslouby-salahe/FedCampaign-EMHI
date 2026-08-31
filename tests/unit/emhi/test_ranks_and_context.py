import inspect

from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    ContextMethodName,
    DatasetName,
)
from fedcampaign_emhi.domain.types import (
    CoalitionMembers,
    ContextTrainingRow,
    RankReference,
)
from fedcampaign_emhi.emhi.contexts import (
    assign_context_cell,
    cap_context_training_rows,
    coalition_context_support_is_sufficient,
    context_cluster_identity,
    context_row_ranking_value,
    exact_exclusion_members,
    fit_context_centroids,
    histogram_one_hot,
    maximal_outside_field,
    minimum_support_epochs_for_order,
    nuisance_field_is_admissible,
    outside_context_histogram,
)
from fedcampaign_emhi.emhi.ranks import coalition_conditioned_residual_rank, midrank


def test_midrank_matches_independent_oracle() -> None:
    reference = RankReference(scores=(0.0, 1.0, 1.0, 2.0))
    less = 1
    equal = 2
    observation_count = 4
    expected = (less + (0.5 * equal) + 0.5) / (observation_count + 1)
    assert midrank(1.0, reference) == expected
    assert midrank(2.0, reference) > midrank(1.0, reference)
    assert inspect.signature(midrank).parameters["score"]


def test_maximal_outside_field_excludes_coalition_members() -> None:
    coalition = CoalitionMembers(client_ids=("a", "b"), order=CoalitionOrder.TWO)
    field = maximal_outside_field(("a", "b", "c", "d"), coalition)
    assert field.complement_client_ids == ("c", "d")
    assert nuisance_field_is_admissible(("c",), ("a", "b", "c", "d"), coalition)
    assert not nuisance_field_is_admissible(("a", "c"), ("a", "b", "c", "d"), coalition)
    assert exact_exclusion_members(("a", "b", "c"), ("a",)) == ("b", "c")


def test_outside_histogram_uses_lagged_complement_ranks_and_abstains() -> None:
    lagged = (("c", 0.0), ("d", 0.99), ("a", 0.5))
    histogram = outside_context_histogram(lagged, ("c", "d"), ("c", "d"), 2, 2, 0.5)
    assert histogram.abstained is False
    assert histogram.bin_mass == (0.5, 0.5)
    abstained = outside_context_histogram(lagged, ("c",), ("c", "d"), 2, 2, 0.5)
    assert abstained.abstained is True
    assert next(iter(inspect.signature(outside_context_histogram).parameters)) == "lagged_ranks"
    assert histogram_one_hot(0.0, 2) == (1.0, 0.0)


def test_context_row_cap_is_independent_of_iteration_order() -> None:
    first = ContextTrainingRow(
        dataset=DatasetName.TON_IOT_NETWORK,
        coalition_order=CoalitionOrder.ONE,
        coalition_client_ids=("b",),
        epoch_index=2,
        histogram=(1.0, 0.0),
    )
    second = ContextTrainingRow(
        dataset=DatasetName.TON_IOT_NETWORK,
        coalition_order=CoalitionOrder.ONE,
        coalition_client_ids=("a",),
        epoch_index=1,
        histogram=(0.0, 1.0),
    )
    third = ContextTrainingRow(
        dataset=DatasetName.TON_IOT_NETWORK,
        coalition_order=CoalitionOrder.ONE,
        coalition_client_ids=("c",),
        epoch_index=3,
        histogram=(0.5, 0.5),
    )
    forward = cap_context_training_rows((first, second, third), 7, 2)
    reverse = cap_context_training_rows((third, second, first), 7, 2)
    assert forward == reverse
    assert len(forward) == 2
    ranking = context_row_ranking_value(first, 7)
    other_seed = context_row_ranking_value(first, 8)
    assert ranking != other_seed
    identity = context_cluster_identity(
        DatasetName.TON_IOT_NETWORK,
        CoalitionOrder.ONE,
        ContextMethodName.EXACT_COALITION_EXCLUSION,
        11,
    )
    assert identity.dataset is DatasetName.TON_IOT_NETWORK
    assert identity.coalition_order is CoalitionOrder.ONE
    assert identity.context_method is ContextMethodName.EXACT_COALITION_EXCLUSION
    assert identity.experiment_seed == 11


def test_centroid_assignment_uses_euclidean_distance_and_smaller_index_ties() -> None:
    histogram = (0.5, 0.5)
    centroids = ((0.0, 0.0), (1.0, 1.0), (0.5, 0.5))
    assigned = assign_context_cell(histogram, centroids, 1.0e-12)
    assert assigned == 2
    tied = assign_context_cell((0.0, 0.0), ((1.0, 0.0), (0.0, 1.0)), 2.0)
    assert tied == 0


def test_residual_rank_uses_midrank_and_support_criterion() -> None:
    reference = RankReference(scores=(0.1, 0.2, 0.8))
    residual = coalition_conditioned_residual_rank(0.2, reference, 1.0e-12)
    assert residual == midrank(0.2, reference)
    assert minimum_support_epochs_for_order(CoalitionOrder.TWO, 100, 200, 400) == 200
    assert coalition_context_support_is_sufficient(200, 200)
    assert not coalition_context_support_is_sufficient(199, 200)


def test_kmeans_fits_separated_histograms() -> None:
    identity = context_cluster_identity(
        DatasetName.TON_IOT_NETWORK,
        CoalitionOrder.ONE,
        ContextMethodName.EXACT_COALITION_EXCLUSION,
        None,
    )
    rows = tuple(
        ContextTrainingRow(
            dataset=DatasetName.TON_IOT_NETWORK,
            coalition_order=CoalitionOrder.ONE,
            coalition_client_ids=(f"c{index}",),
            epoch_index=index,
            histogram=(1.0, 0.0) if index < 3 else (0.0, 1.0),
        )
        for index in range(6)
    )
    fitted = fit_context_centroids(rows, identity, 2, 3, 20, 0.0001, 1.0e-12, 5)
    assert fitted is not None
    assert len(fitted.centroids) == 2
