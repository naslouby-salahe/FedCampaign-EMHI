from fedcampaign_emhi.comparators.dependence import (
    gaussian_h_function,
    hofd_atom_rows,
    lancaster_triple_moment,
    pair_dependence_moment,
    pair_dependence_nonconformity,
    selected_factor_rank,
    uniform_probability_table,
)
from fedcampaign_emhi.comparators.fusion import max_rank_fusion, mean_rank_fusion
from fedcampaign_emhi.comparators.sequential import (
    centered_rank_increment,
    global_cusum_score,
    next_cusum_state,
)
from fedcampaign_emhi.domain.types import RankReference
from fedcampaign_emhi.emhi.structure import midrank


def test_mean_and_max_rank_fusion() -> None:
    ranks = (0.2, 0.4, 0.9)
    assert abs(mean_rank_fusion(ranks) - (1.5 / 3)) < 1.0e-12
    assert max_rank_fusion(ranks) == 0.9


def test_smoke_midrank_fixture() -> None:
    rank = midrank(0.5, RankReference(scores=(0.0, 0.5, 0.5, 1.0)))
    assert rank == 0.5


def test_cusum_does_not_go_negative() -> None:
    assert next_cusum_state(0.0, 0.5, 0.5, 0.05) == 0.0
    assert abs(next_cusum_state(1.0, 0.9, 0.5, 0.05) - 1.35) < 1.0e-12


def test_pair_and_lancaster_moments_at_one_half_are_zero() -> None:
    assert pair_dependence_moment(0.5, 0.5) == 0.0
    assert lancaster_triple_moment(0.5, 0.5, 0.5) == 0.0
    assert pair_dependence_moment(1.0, 1.0) == 1.0
    assert lancaster_triple_moment(1.0, 1.0, 0.0) == -1.0
    assert pair_dependence_nonconformity(-2.0, 0.0, 1.0, 1.0e-06) == 2.0


def test_hofd_zero_when_tensor_in_design_span() -> None:
    design = ((1.0, 0.0), (1.0, 1.0), (1.0, 2.0))
    tensor = ((0.0,), (1.0,), (2.0,))
    residuals = hofd_atom_rows(tensor, design, 0.0, 1.0e-12)
    assert all(abs(row[0]) < 1.0e-10 for row in residuals)


def test_connected_information_initial_table_is_uniform() -> None:
    table = uniform_probability_table(2)
    assert abs(table[0][0][0] - 0.125) < 1.0e-12


def test_gaussian_h_function_is_identity_at_independence() -> None:
    independent = gaussian_h_function(0.3, 0.8, 0.0, 1.0e-12)
    assert abs(independent - 0.3) < 1.0e-8


def test_cusum_increment_and_global_max() -> None:
    assert centered_rank_increment(0.9, 0.5) == 0.4
    assert global_cusum_score((0.1, 0.4, 0.2)) == 0.4
    assert next_cusum_state(0.0, 0.5, 0.5, 0.05) == 0.0


def test_selected_factor_rank_uses_smallest_candidate_meeting_target() -> None:
    assert selected_factor_rank((2.0, 1.0, 0.1), 0.8, 3, (1, 2, 3)) == 2
