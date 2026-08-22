from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.domain.types import BasisSize, TensorDimension


def tensor_dimension(basis_size: BasisSize, coalition_order: CoalitionOrder) -> TensorDimension:
    return basis_size ** int(coalition_order)
