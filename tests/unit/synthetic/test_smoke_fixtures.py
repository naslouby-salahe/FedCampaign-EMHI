from math import sqrt

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.datasets.campaigns import campaign_duration_epochs, merge_malicious_runs
from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.emhi.sequential import distributed_support_predicate
from fedcampaign_emhi.synthetic.generators import (
    contaminate_rank,
    contaminated_outside_count,
    equally_spaced_loadings,
    gaussian_copula_pair,
    marginal_campaign_targets,
)
from fedcampaign_emhi.synthetic.pure_order import (
    lexicographic_target_clients,
    polynomial_density_is_valid,
    polynomial_envelope,
    polynomial_scale,
    sample_xor_ranks,
)
from fedcampaign_emhi.synthetic.self_explanation import analytic_direct_derivative


def test_loadings_are_equally_spaced() -> None:
    loadings = equally_spaced_loadings(3, 0.6, 1.0)
    assert loadings[0] == 0.6
    assert loadings[-1] == 1.0
    assert abs(loadings[1] - 0.8) < 1.0e-12


def test_campaign_merge_and_duration() -> None:
    merged = merge_malicious_runs((1, 2, 4, 20), 2)
    assert merged == ((1, 4), (20, 20))
    assert campaign_duration_epochs(1, 4) == 4


def test_polynomial_scale_and_illegal_order_three_thetas() -> None:
    independent_scale = sqrt(3.0) ** 3
    assert abs(polynomial_scale(CoalitionOrder.THREE) - independent_scale) < 1.0e-12
    assert polynomial_density_is_valid(0.18, CoalitionOrder.THREE) is True
    assert polynomial_density_is_valid(0.20, CoalitionOrder.THREE) is False
    assert polynomial_density_is_valid(0.40, CoalitionOrder.THREE) is False
    assert polynomial_envelope(0.1, CoalitionOrder.ONE) == 1.0 + (0.1 * sqrt(3.0))


def test_lexicographic_targets() -> None:
    clients = ("c3", "c1", "c2", "c4")
    assert lexicographic_target_clients(clients, 3) == ("c1", "c2", "c3")
    assert marginal_campaign_targets(clients) == ("c1", "c2", "c3")


def test_single_client_cannot_satisfy_distributed_support() -> None:
    loaded = load_production_configuration()
    minimum = loaded.values.distributed_support.minimum_clients
    assert distributed_support_predicate(("c1",), minimum) is False
    assert distributed_support_predicate(("c1", "c2"), minimum) is True


def test_xor_rank_count_and_copula_uniforms() -> None:
    ranks = sample_xor_ranks(0.5, 9, 11)
    assert len(ranks) == 12
    left, right = gaussian_copula_pair(0.6, 5)
    assert 0.0 < left < 1.0
    assert 0.0 < right < 1.0


def test_contamination_round_half_up_and_clip() -> None:
    assert contaminated_outside_count(0.25, 9) == 2
    loaded = load_production_configuration()
    clipped = contaminate_rank(0.99, 0.25, loaded.values.context.rank_clip_epsilon)
    assert clipped == 1.0 - loaded.values.context.rank_clip_epsilon
    assert analytic_direct_derivative() == 1.0
