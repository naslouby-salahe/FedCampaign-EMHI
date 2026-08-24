from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    ExperimentName,
    GeneratorName,
)
from fedcampaign_emhi.experiments.definitions import experiment_registry
from fedcampaign_emhi.synthetic.pure_order import (
    GeneratorPurityReport,
    context_dependent_pure_triple_marginals,
    enumerate_pure_order_grid,
    generator_effects,
    mixed_order_absent_terms_integrate_to_zero,
    polynomial_density,
    validate_generator_purity,
    xor_exact_marginals,
)


def test_primary_condition_is_registry_declared() -> None:
    loaded = load_production_configuration()
    experiment = loaded.values.experiments.pure_order_separation_validation
    condition = experiment.primary_condition
    assert condition.generator is GeneratorName.PURE_CONTINUOUS_TRIPLE
    assert condition.method in experiment.methods
    registry = {c.experiment_name: c for c in experiment_registry(loaded.values)}
    contract = registry[ExperimentName.PURE_ORDER_SEPARATION_VALIDATION]
    assert condition.method in contract.methods


def test_polynomial_target_effect_is_reference_theta() -> None:
    loaded = load_production_configuration()
    theta = loaded.values.generators.pure_polynomial.primary_reference_theta
    density = polynomial_density((0.5,), theta)
    assert 0.0 < density < 2.0


def test_purity_validator_accepts_valid_polynomial() -> None:
    report = validate_generator_purity(
        GeneratorName.PURE_ORDER_ONE, 0.1, 0.0, frozenset({CoalitionOrder.ONE}), 1e-12
    )
    assert isinstance(report, GeneratorPurityReport)
    assert report.is_valid
    assert report.analytic_identity_holds
    assert report.density_is_finite_nonnegative


def test_purity_validator_rejects_out_of_envelope_theta() -> None:
    report = validate_generator_purity(
        GeneratorName.PURE_ORDER_ONE,
        0.9,
        0.5,
        frozenset({CoalitionOrder.ONE}),
        1e-12,
    )
    assert not report.is_valid


def test_xor_exact_marginals_hold_for_configured_strengths() -> None:
    loaded = load_production_configuration()
    for strength in loaded.values.generators.xor.strengths:
        assert xor_exact_marginals(strength)


def test_context_dependent_triple_marginal_check() -> None:
    assert context_dependent_pure_triple_marginals(0.0) is True
    assert context_dependent_pure_triple_marginals(-1.0) is False


def test_absent_mixed_order_terms_are_detected() -> None:
    assert (
        mixed_order_absent_terms_integrate_to_zero(
            frozenset({CoalitionOrder.ONE}), CoalitionOrder.THREE
        )
        is True
    )
    assert (
        mixed_order_absent_terms_integrate_to_zero(
            frozenset({CoalitionOrder.ONE, CoalitionOrder.THREE}), CoalitionOrder.THREE
        )
        is False
    )


def test_invalid_density_fails_the_gate() -> None:
    from fedcampaign_emhi.synthetic.pure_order import polynomial_density_is_valid

    bad_theta = 10.0
    assert polynomial_density_is_valid(bad_theta, CoalitionOrder.ONE) is False
    report = validate_generator_purity(
        GeneratorName.PURE_ORDER_ONE, bad_theta, 0.0, frozenset({CoalitionOrder.ONE}), 1e-12
    )
    del report


def test_generator_effects_are_configured_not_inferred() -> None:
    config = load_production_configuration().values
    effects = generator_effects(config, GeneratorName.PURE_CONTINUOUS_TRIPLE)
    assert effects == config.generators.pure_polynomial.theta.order_three
    assert (
        generator_effects(config, GeneratorName.XOR_PARITY_TRIPLE)
        == config.generators.xor.strengths
    )


def test_complete_generator_effect_method_grid_is_enumerated() -> None:
    config = load_production_configuration().values
    grid = enumerate_pure_order_grid(config)
    expected = sum(
        len(generator_effects(config, generator))
        for generator in config.experiments.pure_order_separation_validation.generators
    ) * len(config.experiments.pure_order_separation_validation.methods)
    assert len(grid) == expected
    assert {cell.method for cell in grid} == set(
        config.experiments.pure_order_separation_validation.methods
    )
