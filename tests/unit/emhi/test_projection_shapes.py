from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.domain.types import RankReference
from fedcampaign_emhi.emhi.basis import bounded_basis, tensor_representation
from fedcampaign_emhi.emhi.coalitions import enumerate_coalitions, required_outside_client_count
from fedcampaign_emhi.emhi.evidence import signed_evidence_factor
from fedcampaign_emhi.emhi.projection import blocked_fold_sizes, proper_subset_design_shape
from fedcampaign_emhi.emhi.ranks import clipped_midrank
from fedcampaign_emhi.emhi.sequential import initial_global_state, next_global_state
from fedcampaign_emhi.emhi.thresholds import clopper_pearson_one_sided_upper_bound


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


def test_midrank_orientation_and_clipping() -> None:
    reference = RankReference(scores=(0.0, 1.0, 1.0, 2.0))
    rank = clipped_midrank(1.0, reference, 1.0e-12)
    assert 0.0 < rank < 1.0
    assert clipped_midrank(2.0, reference, 1.0e-12) > rank


def test_signed_evidence_uses_roadmap_compensator() -> None:
    factor = signed_evidence_factor(0.0, 1.0, 0.5)
    assert abs(factor - 0.8824969025845955) < 1.0e-12


def test_global_state_recursion() -> None:
    state = initial_global_state()
    state = next_global_state(state, 2.0)
    assert state == 2.0
    state = next_global_state(state, 1.5)
    assert state == 4.5


def test_outside_requirement_uses_max_of_count_and_fraction() -> None:
    assert required_outside_client_count(10, 2, 0.5) == 5
    assert required_outside_client_count(3, 2, 0.5) == 2


def test_tensor_dimension_matches_basis_power() -> None:
    tensor = tensor_representation((0.25, 0.75), 2)
    assert len(tensor) == 4
    assert len(bounded_basis(0.5, 3)) == 3


def test_enumerate_coalitions_respects_maximum_order() -> None:
    coalitions = enumerate_coalitions(("c1", "c2", "c3"), CoalitionOrder.TWO)
    assert len(coalitions) == 6


def test_clopper_pearson_zero_false_stops() -> None:
    upper = clopper_pearson_one_sided_upper_bound(0, 59, 0.95)
    assert upper <= 0.05
    assert clopper_pearson_one_sided_upper_bound(59, 59, 0.95) == 1.0
