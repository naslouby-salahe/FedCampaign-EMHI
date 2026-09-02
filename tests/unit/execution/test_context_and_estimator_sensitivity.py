import pytest

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import ContextMethodName
from fedcampaign_emhi.experiments.campaigns import (
    sensitivity_base_specification,
    sensitivity_cell_slug,
    sensitivity_conditions,
)


def test_base_specification_matches_full_fedcampaign_emhi_registry() -> None:
    loaded = load_production_configuration()
    context_method, maximum_order, purification_enabled = sensitivity_base_specification(loaded)
    assert context_method is ContextMethodName.EXACT_COALITION_EXCLUSION
    assert int(maximum_order) == loaded.values.study.maximum_coalition_order
    assert purification_enabled is True


def test_conditions_cover_every_declared_one_factor_variant() -> None:
    loaded = load_production_configuration()
    context_method, _maximum_order, _purification = sensitivity_base_specification(loaded)
    conditions = sensitivity_conditions(loaded, context_method)
    basis_sizes = loaded.values.basis.sensitivity_sizes
    cell_counts = loaded.values.context.cell_count_sensitivity
    context_variants = loaded.values.experiments.context_and_estimator_sensitivity.context_variants
    assert len(conditions) == len(basis_sizes) + len(cell_counts) + 1 + len(context_variants)

    basis_conditions = [condition for condition in conditions if condition[0] is not None]
    assert {condition[0] for condition in basis_conditions} == set(basis_sizes)
    for condition in basis_conditions:
        (
            basis_override,
            cell_override,
            ridge_override,
            method_override,
            basis_size,
            cell_count,
            ridge_candidates,
            resolved_context_method,
            forced_no_abstention,
        ) = condition
        assert cell_override is None
        assert ridge_override is None
        assert method_override is None
        assert basis_size == basis_override
        assert cell_count == loaded.values.context.primary_cell_count
        assert ridge_candidates is None
        assert resolved_context_method is context_method
        assert forced_no_abstention is False

    cell_conditions = [
        condition for condition in conditions if condition[0] is None and condition[1] is not None
    ]
    assert {condition[1] for condition in cell_conditions} == set(cell_counts)

    ridge_conditions = [condition for condition in conditions if condition[2] is not None]
    assert len(ridge_conditions) == 1
    ridge_condition = ridge_conditions[0]
    forced_ridge = loaded.values.experiments.context_and_estimator_sensitivity.forced_ridge
    assert ridge_condition[2] == forced_ridge
    assert ridge_condition[6] == (forced_ridge,)

    method_conditions = [condition for condition in conditions if condition[3] is not None]
    assert {condition[3] for condition in method_conditions} == set(context_variants)
    forced_no_abstention_condition = next(
        condition
        for condition in method_conditions
        if condition[3] is ContextMethodName.FORCED_NO_ABSTENTION
    )
    assert forced_no_abstention_condition[7] is context_method
    assert forced_no_abstention_condition[8] is True
    shuffled_condition = next(
        condition
        for condition in method_conditions
        if condition[3] is ContextMethodName.SHUFFLED_OUTSIDE_CONTEXT
    )
    assert shuffled_condition[7] is ContextMethodName.SHUFFLED_OUTSIDE_CONTEXT
    assert shuffled_condition[8] is False


def test_cell_slug_names_exactly_one_factor() -> None:
    assert sensitivity_cell_slug(4, None, None, None) == "basis-size-4"
    assert sensitivity_cell_slug(None, 8, None, None) == "context-cell-count-8"
    assert sensitivity_cell_slug(None, None, 0.05, None) == "forced-ridge-0.05"
    assert (
        sensitivity_cell_slug(None, None, None, ContextMethodName.LOCAL_HISTORY_ONLY_CONTEXT)
        == "local-history-only-context"
    )
    with pytest.raises(ValueError):
        sensitivity_cell_slug(None, None, None, None)
