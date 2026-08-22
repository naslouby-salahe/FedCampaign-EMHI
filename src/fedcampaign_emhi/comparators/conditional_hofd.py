from fedcampaign_emhi.domain.types import FiniteFloat, NumericalFloor, RidgePenalty
from fedcampaign_emhi.emhi.innovations import projection_residual
from fedcampaign_emhi.emhi.projection import ridge_coefficient_matrix


def hofd_atom_rows(
    tensor_rows: tuple[tuple[FiniteFloat, ...], ...],
    design_rows: tuple[tuple[FiniteFloat, ...], ...],
    ridge_penalty: RidgePenalty,
    relative_singular_cutoff: NumericalFloor,
) -> tuple[tuple[FiniteFloat, ...], ...]:
    coefficients = ridge_coefficient_matrix(
        design_rows, tensor_rows, ridge_penalty, relative_singular_cutoff
    )
    residuals: list[tuple[FiniteFloat, ...]] = []
    for tensor_row, design_row in zip(tensor_rows, design_rows, strict=True):
        residuals.append(projection_residual(tensor_row, coefficients, design_row))
    return tuple(residuals)
