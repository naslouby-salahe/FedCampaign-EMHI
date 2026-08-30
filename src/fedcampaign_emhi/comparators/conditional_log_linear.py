from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.domain.types import BasisSize, Boolean, DesignColumnCount
from fedcampaign_emhi.emhi.projection import proper_subset_design_column_count


def log_linear_includes_intercept() -> Boolean:
    return True


def log_linear_includes_singletons() -> Boolean:
    return True


def log_linear_includes_pairs() -> Boolean:
    return True


def log_linear_includes_triple() -> Boolean:
    return False


def log_linear_design_column_count(basis_size: BasisSize) -> DesignColumnCount:
    return proper_subset_design_column_count(CoalitionOrder.THREE, basis_size)
