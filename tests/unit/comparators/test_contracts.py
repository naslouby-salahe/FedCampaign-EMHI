from fedcampaign_emhi.comparators.contracts import (
    comparator_method_contracts,
    full_hierarchy_order_set,
    native_target_order,
)
from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    ContextMethodName,
    ExperimentName,
    MethodName,
)


def test_method_contracts_cover_the_roadmap_method_surface() -> None:
    contracts = comparator_method_contracts()
    names = [contract.method_name for contract in contracts]
    assert len(names) == len(set(names))
    assert MethodName.FULL_FEDCAMPAIGN_EMHI in names
    assert MethodName.FEDAVG_AUTOENCODER_REFERENCE in names
    assert len(contracts) >= 17


def test_full_hierarchy_contract_locks_primary_configuration() -> None:
    contracts = {c.method_name: c for c in comparator_method_contracts()}
    full = contracts[MethodName.FULL_FEDCAMPAIGN_EMHI]
    assert full.enabled_order_set == full_hierarchy_order_set()
    assert full.context_method is ContextMethodName.EXACT_COALITION_EXCLUSION
    assert full.proper_subset_purification_enabled is True
    assert full.establishes_primary_effect is True


def test_order_sets_match_roadmap_locked_values() -> None:
    contracts = {c.method_name: c for c in comparator_method_contracts()}
    assert contracts[MethodName.EXCLUSION_MATCHED_ORDER_ONE_EMHI].enabled_order_set == (
        CoalitionOrder.ONE,
    )
    at_most_two = contracts[MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI]
    assert at_most_two.enabled_order_set == (CoalitionOrder.ONE, CoalitionOrder.TWO)
    assert at_most_two.establishes_primary_effect is False


def test_context_variants_differ_only_in_context() -> None:
    contracts = {c.method_name: c for c in comparator_method_contracts()}
    full = contracts[MethodName.FULL_FEDCAMPAIGN_EMHI]
    for variant in (
        MethodName.INCLUSIVE_CONTEXT_FULL_HIERARCHY,
        MethodName.LEAVE_ONE_OUT_INSUFFICIENT_EXCLUSION,
        MethodName.PARTIAL_COALITION_EXCLUSION,
    ):
        contract = contracts[variant]
        assert contract.enabled_order_set == full.enabled_order_set
        assert contract.proper_subset_purification_enabled == (
            full.proper_subset_purification_enabled
        )
        assert contract.context_method is not full.context_method
    no_purification = contracts[MethodName.NO_PROPER_SUBSET_PURIFICATION]
    assert no_purification.proper_subset_purification_enabled is False
    assert no_purification.context_method is ContextMethodName.EXACT_COALITION_EXCLUSION
    no_outside = contracts[MethodName.NO_OUTSIDE_CONTEXT_FULL_HIERARCHY]
    assert no_outside.enabled_order_set == full.enabled_order_set
    assert no_outside.proper_subset_purification_enabled is True
    assert no_outside.context_method is not ContextMethodName.EXACT_COALITION_EXCLUSION


def test_hofd_is_equivalence_not_superiority_comparator() -> None:
    contracts = {c.method_name: c for c in comparator_method_contracts()}
    hofd = contracts[MethodName.EXCLUSION_MATCHED_CONDITIONAL_HOFD]
    assert hofd.is_equivalence_comparator is True
    assert hofd.establishes_primary_effect is False


def test_native_target_orders_match_roadmap_table() -> None:
    loaded = load_production_configuration()
    candidates = loaded.values.experiments.strong_comparator_composition_challenge.candidates
    for candidate in candidates:
        if candidate is MethodName.SELECTED_STRONG_COMPARATOR_COMPOSITION:
            continue
        assert native_target_order(candidate) is not None, candidate
    assert native_target_order(MethodName.D_VINE_CONDITIONAL_REFERENCE) is CoalitionOrder.THREE
    assert native_target_order(MethodName.FULL_FEDCAMPAIGN_EMHI) is None


def test_registry_experiments_reference_declared_methods() -> None:
    from fedcampaign_emhi.experiments.registry import experiment_registry

    loaded = load_production_configuration()
    registry_names = {
        contract.experiment_name: contract.methods
        for contract in experiment_registry(loaded.values)
    }
    primary = registry_names[ExperimentName.PRIMARY_STRICT_ODI_EVALUATION]
    declared = loaded.values.experiments.primary_strict_odi_evaluation.methods
    assert set(primary) == set(declared)
    contracts = {c.method_name for c in comparator_method_contracts()}
    for method in declared:
        if method is MethodName.SELECTED_STRONG_COMPARATOR_COMPOSITION:
            continue
        assert method in contracts, method
