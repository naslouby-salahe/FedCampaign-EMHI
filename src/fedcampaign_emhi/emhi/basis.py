from math import sqrt

from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.domain.types import BasisSize, FiniteFloat, RankValue, TensorDimension


def shifted_legendre_phi_one(rank: RankValue) -> FiniteFloat:
    return sqrt(3.0) * ((2.0 * rank) - 1.0)


def shifted_legendre_phi_two(rank: RankValue) -> FiniteFloat:
    return sqrt(5.0) * ((6.0 * (rank**2)) - (6.0 * rank) + 1.0)


def shifted_legendre_phi_three(rank: RankValue) -> FiniteFloat:
    return sqrt(7.0) * ((20.0 * (rank**3)) - (30.0 * (rank**2)) + (12.0 * rank) - 1.0)


def shifted_legendre_phi_four(rank: RankValue) -> FiniteFloat:
    return 3.0 * (
        (70.0 * (rank**4)) - (140.0 * (rank**3)) + (90.0 * (rank**2)) - (20.0 * rank) + 1.0
    )


_BASIS_FUNCTIONS = (
    shifted_legendre_phi_one,
    shifted_legendre_phi_two,
    shifted_legendre_phi_three,
    shifted_legendre_phi_four,
)


def bounded_basis(rank: RankValue, basis_size: BasisSize) -> tuple[FiniteFloat, ...]:
    if basis_size < 1 or basis_size > len(_BASIS_FUNCTIONS):
        raise ValueError("basis_size must be between 1 and 4 inclusive")
    return tuple(function(rank) for function in _BASIS_FUNCTIONS[:basis_size])


def tensor_dimension(basis_size: BasisSize, coalition_order: CoalitionOrder) -> TensorDimension:
    return basis_size ** int(coalition_order)


def tensor_representation(
    member_ranks: tuple[RankValue, ...], basis_size: BasisSize
) -> tuple[FiniteFloat, ...]:
    if not member_ranks:
        raise ValueError("tensor representation requires at least one coalition member")
    coordinates = [1.0]
    for rank in member_ranks:
        member_basis = bounded_basis(rank, basis_size)
        expanded = []
        for left in coordinates:
            for right in member_basis:
                expanded.append(left * right)
        coordinates = expanded
    return tuple(coordinates)
