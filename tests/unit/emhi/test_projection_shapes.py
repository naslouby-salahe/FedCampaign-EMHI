from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.emhi.projection import blocked_fold_sizes, proper_subset_design_shape


def test_primary_basis_design_columns() -> None:
    order_one = proper_subset_design_shape(CoalitionOrder.ONE, 3)
    order_two = proper_subset_design_shape(CoalitionOrder.TWO, 3)
    order_three = proper_subset_design_shape(CoalitionOrder.THREE, 3)
    assert order_one.tensor_dimension == 3
    assert order_two.tensor_dimension == 9
    assert order_three.tensor_dimension == 27
    assert order_one.design_column_count == 1
    assert order_two.design_column_count == 7
    assert order_three.design_column_count == 37


def test_blocked_fold_sizes_match_roadmap_fixture() -> None:
    assert blocked_fold_sizes(11, 5) == (3, 2, 2, 2, 2)
