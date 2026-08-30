from fedcampaign_emhi.domain.enums import CoalitionOrder, ExecutionRole
from fedcampaign_emhi.synthetic.context_boundaries import generate_deterministic_context_support
from fedcampaign_emhi.synthetic.feasibility import (
    evaluate_estimator_feasibility_condition,
    feasibility_conditions,
)


def test_context_support_generator_has_exact_balanced_usable_cell_counts() -> None:
    sequence = generate_deterministic_context_support(
        ("client-01", "client-02", "client-03", "client-04"),
        CoalitionOrder.TWO,
        2,
        3,
        11,
    )

    assert len(sequence.ranks) == 7
    assert sequence.target_client_ids == ("client-01", "client-02")
    assert sequence.latent_cell_indexes[1:] == (0, 1, 0, 1, 0, 1)
    assert sequence.latent_cell_indexes[1:].count(0) == 3
    assert sequence.latent_cell_indexes[1:].count(1) == 3


def test_context_support_generator_uses_deterministic_outside_midpoints_and_seeded_targets() -> (
    None
):
    first = generate_deterministic_context_support(
        ("client-01", "client-02", "client-03", "client-04"),
        CoalitionOrder.TWO,
        2,
        2,
        11,
    )
    second = generate_deterministic_context_support(
        ("client-01", "client-02", "client-03", "client-04"),
        CoalitionOrder.TWO,
        2,
        2,
        11,
    )

    assert first == second
    assert first.ranks[1][2:] == (0.25, 0.25)
    assert first.ranks[2][2:] == (0.75, 0.75)
    assert first.ranks[1][:2] != first.ranks[2][:2]


def test_feasibility_evaluator_fits_from_lagged_outside_context_without_latent_labels() -> None:
    from fedcampaign_emhi.config.loading import load_smoke_configuration

    config = load_smoke_configuration().values
    metrics = evaluate_estimator_feasibility_condition(
        config,
        7,
        CoalitionOrder.TWO,
        20,
        2,
        2,
    )

    assert not metrics.numerical_failure
    assert metrics.context_coverage == 1.0
    assert metrics.abstention_rate == 0.0
    assert metrics.condition_number is not None
    assert metrics.conditional_rank_mae >= 0.0
    assert metrics.projection_nrmse >= 0.0
    assert metrics.standardized_null_bias >= 0.0


def test_feasibility_grid_keeps_confirmatory_primary_distinct_from_development_sensitivity() -> (
    None
):
    from fedcampaign_emhi.config.loading import load_smoke_configuration

    config = load_smoke_configuration().values
    confirmatory = feasibility_conditions(config, ExecutionRole.CONFIRMATORY)
    development = feasibility_conditions(config, ExecutionRole.DEVELOPMENT)

    assert tuple(condition.identifier for condition in confirmatory) == ("primary-order-three",)
    assert len(development) > len(confirmatory)
    assert any(condition.identifier.startswith("forced-ridge") for condition in development)
    assert any(condition.identifier.startswith("context-sensitivity") for condition in development)
