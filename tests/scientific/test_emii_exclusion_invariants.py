from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.domain.types import CoalitionMembers
from fedcampaign_emhi.emhi.coalitions import complement_members, proper_subset_members
from fedcampaign_emhi.emhi.contexts import exact_exclusion_members
from fedcampaign_emhi.emhi.innovations import innovation_excludes_same_order_representation
from fedcampaign_emhi.emhi.projection import (
    proper_subset_design_column_count,
    proper_subset_design_shape,
)


def test_exact_exclusion_uses_complement_only() -> None:
    selected = ("c1", "c2", "c3", "c4", "c5", "c6")
    coalition = ("c1", "c2", "c3")
    assert exact_exclusion_members(selected, coalition) == ("c4", "c5", "c6")
    assert complement_members(selected, coalition) == ("c4", "c5", "c6")
    for member in coalition:
        assert member not in exact_exclusion_members(selected, coalition)


def test_proper_subsets_never_include_the_full_coalition() -> None:
    coalition = CoalitionMembers(client_ids=("a", "b", "c"), order=CoalitionOrder.THREE)
    subsets = proper_subset_members(coalition)
    assert coalition.client_ids not in {item.client_ids for item in subsets}
    assert all(item.order is not CoalitionOrder.THREE for item in subsets)


def test_proper_subset_design_excludes_same_order_interactions() -> None:
    order_two = proper_subset_design_shape(CoalitionOrder.TWO, 3)
    order_three = proper_subset_design_shape(CoalitionOrder.THREE, 3)
    assert proper_subset_design_column_count(CoalitionOrder.TWO, 3) == 1 + (2 * 3)
    assert order_two.design_column_count < 1 + (2 * 3) + (3**2)
    assert order_three.tensor_dimension == 27
    assert order_three.design_column_count == 1 + (3 * 3) + (3 * (3**2))


def test_innovation_is_tensor_minus_proper_subset_reconstruction() -> None:
    tensor = (1.0, 2.0)
    design_row = (1.0, 0.5)
    coefficients = ((0.0, 0.0), (2.0, 0.0))
    residual = innovation_excludes_same_order_representation(tensor, coefficients, design_row)
    assert residual == (0.0, 2.0)
