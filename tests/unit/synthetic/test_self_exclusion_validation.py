from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    ContextMethodName,
    NuisanceTransformName,
)
from fedcampaign_emhi.synthetic.self_explanation import (
    analytic_direct_derivative,
    enumerate_self_exclusion_grid,
    exact_nuisance_derivative_within_margin,
    material_attenuation_gate,
    primary_directional_test_passes,
)


def test_grid_uses_roadmap_owned_grids_only() -> None:
    loaded = load_production_configuration()
    plan = enumerate_self_exclusion_grid(loaded.values)
    expected_orders = 3
    client_counts = len(loaded.values.robustness.scalability_client_counts)
    perturbations = len(loaded.values.generators.self_explanation.perturbations)
    transforms = 3
    methods = len(loaded.values.experiments.self_explanation_exclusion_validation.context_methods)
    assert len(plan.cells) == client_counts * expected_orders * perturbations * transforms * methods


def test_grid_seed_namespaces_are_separate() -> None:
    loaded = load_production_configuration()
    plan = enumerate_self_exclusion_grid(loaded.values)
    randomness = loaded.values.randomness
    assert plan.development_seed_count == len(randomness.synthetic_development_roots)
    assert plan.confirmatory_seed_count == len(randomness.synthetic_confirmatory_roots)
    assert randomness.synthetic_development_roots != randomness.synthetic_confirmatory_roots


def test_primary_condition_is_registry_declared() -> None:
    loaded = load_production_configuration()
    condition = loaded.values.experiments.self_explanation_exclusion_validation.primary_condition
    grid = enumerate_self_exclusion_grid(loaded.values)
    matching = [
        cell
        for cell in grid.cells
        if cell.client_count == condition.client_count
        and int(cell.coalition_order) == condition.coalition_order
        and cell.nuisance_transform is condition.nuisance_transform
        and cell.context_method in condition.comparison
        and cell.perturbation != 0.0
    ]
    assert matching


def test_exact_nuisance_derivative_gate() -> None:
    loaded = load_production_configuration()
    margin = loaded.values.claim_materiality.self_explanation.exact_exclusion_nuisance_derivative_equivalence_fraction_of_direct
    assert exact_nuisance_derivative_within_margin(0.0, margin) is True
    assert (
        exact_nuisance_derivative_within_margin(margin * analytic_direct_derivative(), margin)
        is True
    )
    assert (
        exact_nuisance_derivative_within_margin(
            margin * analytic_direct_derivative() + 0.01, margin
        )
        is False
    )


def test_material_attenuation_gate() -> None:
    loaded = load_production_configuration()
    minimum = loaded.values.claim_materiality.self_explanation.minimum_attenuation_difference
    assert material_attenuation_gate(minimum, minimum) is True
    assert material_attenuation_gate(minimum - 0.01, minimum) is False


def test_primary_directional_test() -> None:
    assert primary_directional_test_passes(0.049, 0.05) is True
    assert primary_directional_test_passes(0.05, 0.05) is False


def test_all_coalition_orders_up_to_maximum_present() -> None:
    loaded = load_production_configuration()
    maximum = loaded.values.study.maximum_coalition_order
    grid = enumerate_self_exclusion_grid(loaded.values)
    orders_in_grid = {int(cell.coalition_order) for cell in grid.cells}
    assert orders_in_grid == set(range(1, maximum + 1))


def test_context_methods_come_from_configuration() -> None:
    loaded = load_production_configuration()
    declared = loaded.values.experiments.self_explanation_exclusion_validation.context_methods
    grid = enumerate_self_exclusion_grid(loaded.values)
    methods_in_grid = {cell.context_method for cell in grid.cells}
    assert methods_in_grid == set(declared)
    assert ContextMethodName.FORCED_NO_ABSTENTION not in methods_in_grid
    assert NuisanceTransformName.LINEAR is not None
    assert CoalitionOrder.ONE is not None
