import pytest

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import MethodName
from fedcampaign_emhi.experiments.ablations import (
    enumerate_context_estimator_sensitivity,
    enumerate_exclusion_mechanism_ablation,
    enumerate_purification_and_order_ablation,
    order_three_material_contribution,
    order_three_scope_gate,
)


def test_exclusion_ablation_plan_reads_configuration() -> None:
    loaded = load_production_configuration()
    plan = enumerate_exclusion_mechanism_ablation(loaded.values)
    assert plan.dataset_name is loaded.values.datasets.primary.name
    assert plan.methods == tuple(loaded.values.experiments.exclusion_mechanism_ablation.methods)
    assert plan.development_seed_count == len(loaded.values.randomness.real_development_roots)
    assert plan.confirmatory_seed_count == len(loaded.values.randomness.real_confirmatory_roots)
    assert plan.secondary_holm_contrast_count == 3


def test_purification_ablation_plan_reads_configuration() -> None:
    loaded = load_production_configuration()
    plan = enumerate_purification_and_order_ablation(loaded.values)
    assert plan.methods == tuple(loaded.values.experiments.purification_and_order_ablation.methods)
    assert plan.secondary_holm_contrast_count == 0


def test_order_three_material_contribution_and_scope_gate() -> None:
    loaded = load_production_configuration()
    minimum = loaded.values.claim_materiality.order_three_real.minimum_material_odi_contribution
    contribution = order_three_material_contribution(0.30, 0.27)
    assert contribution == pytest.approx(0.03, abs=1e-12)
    passing_gate = order_three_scope_gate(contribution, minimum)
    assert passing_gate == (contribution >= minimum)
    failing = order_three_material_contribution(0.20, 0.25)
    assert order_three_scope_gate(failing, minimum) is False


def test_sensitivity_plan_is_one_factor_and_development_only() -> None:
    loaded = load_production_configuration()
    plan = enumerate_context_estimator_sensitivity(loaded.values)
    sensitivity = loaded.values.experiments.context_and_estimator_sensitivity
    assert plan.base_method is MethodName.FULL_FEDCAMPAIGN_EMHI
    assert plan.basis_sizes == tuple(loaded.values.basis.sensitivity_sizes)
    assert plan.context_cell_counts == tuple(loaded.values.context.cell_count_sensitivity)
    assert plan.forced_ridge == sensitivity.forced_ridge
    assert plan.one_factor_variant_count == 3
