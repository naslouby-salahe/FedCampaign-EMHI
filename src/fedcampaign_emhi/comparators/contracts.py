from dataclasses import dataclass

from fedcampaign_emhi.domain.enums import CoalitionOrder, ContextMethodName, MethodName
from fedcampaign_emhi.domain.types import Boolean, PositiveEpochCount


@dataclass(frozen=True)
class ComparatorMethodContract:
    method_name: MethodName
    context_method: ContextMethodName | None
    enabled_order_set: tuple[CoalitionOrder, ...] | None
    proper_subset_purification_enabled: Boolean | None
    native_maximum_interaction_order: PositiveEpochCount | None
    is_equivalence_comparator: Boolean
    establishes_primary_effect: Boolean


def native_target_order(method_name: MethodName) -> CoalitionOrder | None:
    if method_name is MethodName.CONDITIONAL_PAIR_DEPENDENCE:
        return CoalitionOrder.TWO
    if method_name in {
        MethodName.EXCLUSION_MATCHED_LANCASTER_TRIPLE,
        MethodName.CONNECTED_INFORMATION_REFERENCE,
        MethodName.D_VINE_CONDITIONAL_REFERENCE,
        MethodName.CONDITIONAL_LOG_LINEAR_REFERENCE,
    }:
        return CoalitionOrder.THREE
    return None


def full_hierarchy_order_set() -> tuple[CoalitionOrder, ...]:
    return (CoalitionOrder.ONE, CoalitionOrder.TWO, CoalitionOrder.THREE)


def comparator_method_contracts() -> tuple[ComparatorMethodContract, ...]:
    full_orders = full_hierarchy_order_set()
    exact = ContextMethodName.EXACT_COALITION_EXCLUSION
    return (
        ComparatorMethodContract(
            method_name=MethodName.RAW_MEAN_RANK_FUSION,
            context_method=None,
            enabled_order_set=None,
            proper_subset_purification_enabled=None,
            native_maximum_interaction_order=None,
            is_equivalence_comparator=False,
            establishes_primary_effect=False,
        ),
        ComparatorMethodContract(
            method_name=MethodName.RAW_MAX_RANK_FUSION,
            context_method=None,
            enabled_order_set=None,
            proper_subset_purification_enabled=None,
            native_maximum_interaction_order=None,
            is_equivalence_comparator=False,
            establishes_primary_effect=False,
        ),
        ComparatorMethodContract(
            method_name=MethodName.FULL_FEDCAMPAIGN_EMHI,
            context_method=exact,
            enabled_order_set=full_orders,
            proper_subset_purification_enabled=True,
            native_maximum_interaction_order=None,
            is_equivalence_comparator=False,
            establishes_primary_effect=True,
        ),
        ComparatorMethodContract(
            method_name=MethodName.EXCLUSION_MATCHED_ORDER_ONE_EMHI,
            context_method=exact,
            enabled_order_set=(CoalitionOrder.ONE,),
            proper_subset_purification_enabled=True,
            native_maximum_interaction_order=None,
            is_equivalence_comparator=False,
            establishes_primary_effect=False,
        ),
        ComparatorMethodContract(
            method_name=MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI,
            context_method=exact,
            enabled_order_set=(CoalitionOrder.ONE, CoalitionOrder.TWO),
            proper_subset_purification_enabled=True,
            native_maximum_interaction_order=None,
            is_equivalence_comparator=False,
            establishes_primary_effect=False,
        ),
        ComparatorMethodContract(
            method_name=MethodName.INCLUSIVE_CONTEXT_FULL_HIERARCHY,
            context_method=ContextMethodName.INCLUSIVE_CONTEXT,
            enabled_order_set=full_orders,
            proper_subset_purification_enabled=True,
            native_maximum_interaction_order=None,
            is_equivalence_comparator=False,
            establishes_primary_effect=False,
        ),
        ComparatorMethodContract(
            method_name=MethodName.LEAVE_ONE_OUT_INSUFFICIENT_EXCLUSION,
            context_method=ContextMethodName.LEAVE_ONE_OUT_INSUFFICIENT_EXCLUSION,
            enabled_order_set=full_orders,
            proper_subset_purification_enabled=True,
            native_maximum_interaction_order=None,
            is_equivalence_comparator=False,
            establishes_primary_effect=False,
        ),
        ComparatorMethodContract(
            method_name=MethodName.PARTIAL_COALITION_EXCLUSION,
            context_method=ContextMethodName.PARTIAL_COALITION_EXCLUSION,
            enabled_order_set=full_orders,
            proper_subset_purification_enabled=True,
            native_maximum_interaction_order=None,
            is_equivalence_comparator=False,
            establishes_primary_effect=False,
        ),
        ComparatorMethodContract(
            method_name=MethodName.NO_PROPER_SUBSET_PURIFICATION,
            context_method=exact,
            enabled_order_set=full_orders,
            proper_subset_purification_enabled=False,
            native_maximum_interaction_order=None,
            is_equivalence_comparator=False,
            establishes_primary_effect=False,
        ),
        ComparatorMethodContract(
            method_name=MethodName.NO_OUTSIDE_CONTEXT_FULL_HIERARCHY,
            context_method=ContextMethodName.NO_OUTSIDE_CONTEXT,
            enabled_order_set=full_orders,
            proper_subset_purification_enabled=True,
            native_maximum_interaction_order=None,
            is_equivalence_comparator=False,
            establishes_primary_effect=False,
        ),
        ComparatorMethodContract(
            method_name=MethodName.EXCLUSION_MATCHED_CONDITIONAL_HOFD,
            context_method=exact,
            enabled_order_set=None,
            proper_subset_purification_enabled=None,
            native_maximum_interaction_order=None,
            is_equivalence_comparator=True,
            establishes_primary_effect=False,
        ),
        ComparatorMethodContract(
            method_name=MethodName.CONDITIONAL_PAIR_DEPENDENCE,
            context_method=None,
            enabled_order_set=None,
            proper_subset_purification_enabled=None,
            native_maximum_interaction_order=native_target_order(
                MethodName.CONDITIONAL_PAIR_DEPENDENCE
            ),
            is_equivalence_comparator=False,
            establishes_primary_effect=False,
        ),
        ComparatorMethodContract(
            method_name=MethodName.EXCLUSION_MATCHED_LANCASTER_TRIPLE,
            context_method=None,
            enabled_order_set=None,
            proper_subset_purification_enabled=None,
            native_maximum_interaction_order=CoalitionOrder.THREE,
            is_equivalence_comparator=False,
            establishes_primary_effect=False,
        ),
        ComparatorMethodContract(
            method_name=MethodName.CONNECTED_INFORMATION_REFERENCE,
            context_method=None,
            enabled_order_set=None,
            proper_subset_purification_enabled=None,
            native_maximum_interaction_order=CoalitionOrder.THREE,
            is_equivalence_comparator=False,
            establishes_primary_effect=False,
        ),
        ComparatorMethodContract(
            method_name=MethodName.D_VINE_CONDITIONAL_REFERENCE,
            context_method=None,
            enabled_order_set=None,
            proper_subset_purification_enabled=None,
            native_maximum_interaction_order=CoalitionOrder.THREE,
            is_equivalence_comparator=False,
            establishes_primary_effect=False,
        ),
        ComparatorMethodContract(
            method_name=MethodName.CONDITIONAL_LOG_LINEAR_REFERENCE,
            context_method=None,
            enabled_order_set=None,
            proper_subset_purification_enabled=None,
            native_maximum_interaction_order=CoalitionOrder.THREE,
            is_equivalence_comparator=False,
            establishes_primary_effect=False,
        ),
        ComparatorMethodContract(
            method_name=MethodName.GLOBAL_FACTOR_RESIDUAL_REFERENCE,
            context_method=None,
            enabled_order_set=None,
            proper_subset_purification_enabled=None,
            native_maximum_interaction_order=None,
            is_equivalence_comparator=False,
            establishes_primary_effect=False,
        ),
        ComparatorMethodContract(
            method_name=MethodName.MULTISTREAM_CUSUM_REFERENCE,
            context_method=None,
            enabled_order_set=None,
            proper_subset_purification_enabled=None,
            native_maximum_interaction_order=None,
            is_equivalence_comparator=False,
            establishes_primary_effect=False,
        ),
        ComparatorMethodContract(
            method_name=MethodName.FEDAVG_AUTOENCODER_REFERENCE,
            context_method=None,
            enabled_order_set=None,
            proper_subset_purification_enabled=None,
            native_maximum_interaction_order=None,
            is_equivalence_comparator=False,
            establishes_primary_effect=False,
        ),
    )
