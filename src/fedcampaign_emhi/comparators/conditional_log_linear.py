from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.domain.types import BasisSize, DesignColumnCount
from fedcampaign_emhi.emhi.projection import proper_subset_design_column_count


def log_linear_includes_intercept() -> bool:
    return True


def log_linear_includes_singletons() -> bool:
    return True


def log_linear_includes_pairs() -> bool:
    return True


def log_linear_includes_triple() -> bool:
    return False


def log_linear_design_column_count(basis_size: BasisSize) -> DesignColumnCount:
    return proper_subset_design_column_count(CoalitionOrder.THREE, basis_size)
