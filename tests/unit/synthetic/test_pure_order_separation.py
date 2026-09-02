from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    ContextMethodName,
    ExperimentName,
    GeneratorName,
    LatentMarkovState,
    MethodName,
)
from fedcampaign_emhi.experiments.calibration import (
    emhi_method_settings,
    evaluate_fitted_pure_order_cell,
)
from fedcampaign_emhi.experiments.registry import experiment_registry
from fedcampaign_emhi.experiments.synthetic import run_synthetic_cell
from fedcampaign_emhi.synthetic.pure_order import (
    GeneratorPurityReport,
    enumerate_pure_order_grid,
    generator_effects,
    generator_enabled_orders,
    mixed_order_absent_terms_integrate_to_zero,
    polynomial_density,
    sample_context_dependent_pure_triple_ranks,
    sample_mixed_order_ranks,
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
        assert xor_exact_marginals(
            strength, loaded.values.numerics.deterministic_comparison_tolerance
        )


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


def test_invalid_density_fails_the_criterion() -> None:
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
    assert generator_effects(config, GeneratorName.CONTEXT_DEPENDENT_PURE_TRIPLE) == (
        config.generators.context_dependent_triple.primary_theta,
    )


def test_mixed_order_grid_cells_preserve_declared_enabled_orders() -> None:
    cell_orders = {
        cell.generator: cell.enabled_orders
        for cell in enumerate_pure_order_grid(load_production_configuration().values)
    }

    assert cell_orders[GeneratorName.MIXED_ORDER_ONE_PLUS_TWO] == frozenset(
        (CoalitionOrder.ONE, CoalitionOrder.TWO)
    )
    assert cell_orders[GeneratorName.MIXED_ORDER_TWO_PLUS_THREE] == frozenset(
        (CoalitionOrder.TWO, CoalitionOrder.THREE)
    )
    assert generator_enabled_orders(GeneratorName.MIXED_ORDER_ONE_PLUS_TWO_PLUS_THREE) == frozenset(
        (CoalitionOrder.ONE, CoalitionOrder.TWO, CoalitionOrder.THREE)
    )


def test_context_dependent_and_mixed_order_samplers_emit_declared_population_rows() -> None:
    context_dependent = sample_context_dependent_pure_triple_ranks(
        0.1, LatentMarkovState.POSITIVE, 9, 11
    )
    mixed = sample_mixed_order_ranks(
        frozenset((CoalitionOrder.ONE, CoalitionOrder.THREE)),
        0.05,
        9,
        12,
    )

    assert len(context_dependent) == 12
    assert len(mixed) == 12
    assert all(0.0 <= rank <= 1.0 for rank in (*context_dependent, *mixed))


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


def test_pure_order_producer_describes_the_execution_layer_grid() -> None:
    loaded = load_production_configuration()
    primary = loaded.values.experiments.pure_order_separation_validation.primary_condition
    sample_sizes = loaded.values.synthetic.sample_sizes.model_copy(
        update={
            "generic_nuisance_fit_epochs": 100,
            "pure_order_independent_evaluation_samples_per_condition_seed": 5,
        }
    )
    pure_order = loaded.values.experiments.pure_order_separation_validation.model_copy(
        update={
            "primary_client_count": 4,
            "generators": (primary.generator,),
            "methods": (primary.method,),
        }
    )
    experiments = loaded.values.experiments.model_copy(
        update={"pure_order_separation_validation": pure_order}
    )
    small_loaded = loaded.model_copy(
        update={
            "values": loaded.values.model_copy(
                update={
                    "synthetic": loaded.values.synthetic.model_copy(
                        update={"sample_sizes": sample_sizes}
                    ),
                    "experiments": experiments,
                }
            )
        }
    )

    outcome = run_synthetic_cell(
        small_loaded,
        ExperimentName.PURE_ORDER_SEPARATION_VALIDATION,
        small_loaded.values.randomness.synthetic_confirmatory_roots[0],
        primary.method,
    )

    assert outcome.pure_order_metrics is None
    assert outcome.failed_checks == ()
    assert outcome.evidence is not None
    assert isinstance(outcome.evidence, dict)
    assert outcome.evidence["implementation_state"] == "execution-layer-grid"


def test_exact_exclusion_artifact_scorer_reaches_the_fitted_path() -> None:
    loaded = load_production_configuration()
    primary = loaded.values.experiments.pure_order_separation_validation.primary_condition
    sample_sizes = loaded.values.synthetic.sample_sizes.model_copy(
        update={
            "generic_nuisance_fit_epochs": 100,
            "pure_order_independent_evaluation_samples_per_condition_seed": 5,
        }
    )
    support = loaded.values.context.minimum_support_epochs.model_copy(
        update={"order_one": 1, "order_two": 1, "order_three": 1}
    )
    pure_order = loaded.values.experiments.pure_order_separation_validation.model_copy(
        update={
            "primary_client_count": 5,
            "generators": (primary.generator,),
            "methods": (primary.method,),
        }
    )
    config = loaded.values.model_copy(
        update={
            "synthetic": loaded.values.synthetic.model_copy(update={"sample_sizes": sample_sizes}),
            "context": loaded.values.context.model_copy(
                update={"primary_cell_count": 1, "minimum_support_epochs": support}
            ),
            "experiments": loaded.values.experiments.model_copy(
                update={"pure_order_separation_validation": pure_order}
            ),
        }
    )
    cell = next(
        cell
        for cell in enumerate_pure_order_grid(config)
        if cell.method is primary.method and cell.generator is primary.generator
    )

    result = evaluate_fitted_pure_order_cell(config, cell, 17)

    assert result is not None
    assert result.artifact_path_complete


def test_native_comparator_producer_describes_the_execution_layer_grid() -> None:
    loaded = load_production_configuration()

    outcome = run_synthetic_cell(
        loaded,
        ExperimentName.PURE_ORDER_SEPARATION_VALIDATION,
        loaded.values.randomness.synthetic_confirmatory_roots[0],
        MethodName.CONDITIONAL_PAIR_DEPENDENCE,
    )

    assert outcome.evidence is not None
    assert isinstance(outcome.evidence, dict)
    assert outcome.evidence["implementation_state"] == "execution-layer-grid"
    assert outcome.failed_checks == ()


def test_emhi_variant_settings_preserve_declared_context_and_purification() -> None:
    assert emhi_method_settings(MethodName.INCLUSIVE_CONTEXT_FULL_HIERARCHY) == (
        ContextMethodName.INCLUSIVE_CONTEXT,
        CoalitionOrder.THREE,
        True,
    )
    assert emhi_method_settings(MethodName.NO_PROPER_SUBSET_PURIFICATION) == (
        ContextMethodName.EXACT_COALITION_EXCLUSION,
        CoalitionOrder.THREE,
        False,
    )


def test_every_declared_emhi_variant_has_fitted_artifact_settings() -> None:
    loaded = load_production_configuration()
    methods = frozenset(loaded.values.experiments.pure_order_separation_validation.methods)
    expected = frozenset(
        {
            MethodName.FULL_FEDCAMPAIGN_EMHI,
            MethodName.EXCLUSION_MATCHED_ORDER_ONE_EMHI,
            MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI,
            MethodName.INCLUSIVE_CONTEXT_FULL_HIERARCHY,
            MethodName.LEAVE_ONE_OUT_INSUFFICIENT_EXCLUSION,
            MethodName.PARTIAL_COALITION_EXCLUSION,
            MethodName.NO_PROPER_SUBSET_PURIFICATION,
            MethodName.NO_OUTSIDE_CONTEXT_FULL_HIERARCHY,
        }
    )

    missing = tuple(method for method in expected if emhi_method_settings(method) is None)

    assert expected <= methods
    assert missing == ()
