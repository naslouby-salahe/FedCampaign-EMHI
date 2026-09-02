import pytest
from scipy.stats import norm

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import CoalitionOrder, ContextMethodName, DatasetName
from fedcampaign_emhi.emhi.contexts import (
    NO_OUTSIDE_CONTEXT_CELL_COUNT,
    ORACLE_QUARTILE_BOUNDARIES,
    ORACLE_QUARTILE_CELL_COUNT,
    inclusive_context_members,
    leave_one_out_context_members,
    local_history_context_member_ranks,
    partial_coalition_context_members,
    shuffled_context_permutation,
    shuffled_outside_context_lag_lookup,
)

SELECTED = ("c1", "c2", "c3", "c4", "c5")


def test_registry_contains_all_ablation_variants_as_one_factor_contrasts() -> None:
    loaded = load_production_configuration()
    validation_methods = (
        loaded.values.experiments.self_explanation_exclusion_validation.context_methods
    )
    sensitivity_variants = (
        loaded.values.experiments.context_and_estimator_sensitivity.context_variants
    )
    expected_validation = (
        ContextMethodName.INCLUSIVE_CONTEXT,
        ContextMethodName.LEAVE_ONE_OUT_INSUFFICIENT_EXCLUSION,
        ContextMethodName.PARTIAL_COALITION_EXCLUSION,
        ContextMethodName.EXACT_COALITION_EXCLUSION,
        ContextMethodName.ORACLE_OUTSIDE_LATENT_CONTEXT,
    )
    assert validation_methods == expected_validation
    expected_sensitivity = (
        ContextMethodName.SHUFFLED_OUTSIDE_CONTEXT,
        ContextMethodName.LOCAL_HISTORY_ONLY_CONTEXT,
        ContextMethodName.FORCED_NO_ABSTENTION,
    )
    assert sensitivity_variants == expected_sensitivity


def test_exact_exclusion_members_are_complement() -> None:
    from fedcampaign_emhi.emhi.contexts import exact_exclusion_members

    assert exact_exclusion_members(SELECTED, ("c2", "c4")) == ("c1", "c3", "c5")


def test_inclusive_context_uses_all_selected_clients() -> None:
    members = inclusive_context_members(SELECTED, ("c1",))
    assert members == tuple(sorted(SELECTED))


def test_leave_one_out_removes_only_lexicographically_first_member() -> None:
    members = leave_one_out_context_members(SELECTED, ("c3", "c1"))
    assert "c1" not in members
    assert set(members) == {"c2", "c3", "c4", "c5"}
    with pytest.raises(ValueError):
        leave_one_out_context_members(SELECTED, ())


def test_partial_coalition_exclusion_for_triple_keeps_third_member() -> None:
    members = partial_coalition_context_members(SELECTED, ("c3", "c1", "c2"))
    assert "c1" not in members
    assert "c2" not in members
    assert "c3" in members
    assert set(members) == {"c3", "c4", "c5"}


def test_partial_exclusion_equals_leave_one_out_for_pairs() -> None:
    coalition = ("c4", "c2")
    assert partial_coalition_context_members(SELECTED, coalition) == (
        leave_one_out_context_members(SELECTED, coalition)
    )


def test_partial_coalition_exclusion_requires_two_members() -> None:
    with pytest.raises(ValueError):
        partial_coalition_context_members(SELECTED, ("c1",))


def test_oracle_cells_use_four_fixed_normal_quartile_boundaries() -> None:
    loaded = load_production_configuration()
    del loaded
    assert ORACLE_QUARTILE_CELL_COUNT == 4
    for index, boundary in enumerate(ORACLE_QUARTILE_BOUNDARIES):
        assert boundary == pytest.approx(norm.ppf((index + 1) / 4), abs=1e-12)
    assert ORACLE_QUARTILE_BOUNDARIES[1] == 0.0


def test_no_outside_context_uses_single_global_cell_without_kmeans() -> None:
    loaded = load_production_configuration()
    primary = loaded.values.context.primary_cell_count
    assert primary != NO_OUTSIDE_CONTEXT_CELL_COUNT
    assert NO_OUTSIDE_CONTEXT_CELL_COUNT == 1


def test_shuffled_permutation_is_deterministic_and_split_dependent() -> None:
    from fedcampaign_emhi.domain.enums import PartitionRole

    rows = ("r1", "r2", "r3", "r4", "r5")
    first = shuffled_context_permutation(rows, PartitionRole.NUISANCE_FIT, 7)
    repeat = shuffled_context_permutation(rows, PartitionRole.NUISANCE_FIT, 7)
    other_split = shuffled_context_permutation(rows, PartitionRole.HELDOUT_BENIGN, 7)
    other_seed = shuffled_context_permutation(rows, PartitionRole.NUISANCE_FIT, 8)
    assert first == repeat
    assert first != other_split or other_seed != first
    assert sorted(first) == list(range(len(rows)))
    with pytest.raises(ValueError):
        shuffled_context_permutation((), PartitionRole.NUISANCE_FIT, 7)


def test_shuffled_lag_lookup_is_a_permutation_of_lagged_epochs() -> None:
    from fedcampaign_emhi.domain.enums import PartitionRole

    epochs = (100, 101, 102, 103, 104)
    lookup = shuffled_outside_context_lag_lookup(epochs, PartitionRole.NUISANCE_FIT, 1, 7)
    assert set(lookup.keys()) == set(epochs)
    unshuffled = {epoch: epoch - 1 for epoch in epochs}
    assert dict(lookup) != unshuffled
    assert sorted(lookup.values()) == sorted(epoch - 1 for epoch in epochs)


def test_shuffled_lag_lookup_is_deterministic_and_split_scoped() -> None:
    from fedcampaign_emhi.domain.enums import PartitionRole

    epochs = (10, 11, 12, 13)
    first = shuffled_outside_context_lag_lookup(epochs, PartitionRole.NUISANCE_FIT, 2, 3)
    repeat = shuffled_outside_context_lag_lookup(epochs, PartitionRole.NUISANCE_FIT, 2, 3)
    other_role = shuffled_outside_context_lag_lookup(epochs, PartitionRole.HELDOUT_BENIGN, 2, 3)
    assert dict(first) == dict(repeat)
    assert dict(first) != dict(other_role)


def test_local_history_uses_only_lagged_coalition_member_ranks() -> None:
    lagged = (("c1", 0.1), ("c9", 0.4), ("c3", 0.8))
    ranks = local_history_context_member_ranks(("c3", "c1"), lagged)
    assert ranks == (0.1, 0.8)


def test_identity_preserves_normalized_dataset_and_order_terms() -> None:
    from fedcampaign_emhi.emhi.contexts import context_cluster_identity

    identity = context_cluster_identity(
        DatasetName.TON_IOT_NETWORK,
        CoalitionOrder.TWO,
        ContextMethodName.EXACT_COALITION_EXCLUSION,
        None,
    )
    assert identity.dataset is DatasetName.TON_IOT_NETWORK
    assert identity.coalition_order is CoalitionOrder.TWO
