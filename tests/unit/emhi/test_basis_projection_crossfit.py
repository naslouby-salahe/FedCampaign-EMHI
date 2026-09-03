import inspect
from math import sqrt
from pathlib import Path

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.emhi.calibration import (
    calibrate_innovations_on_nuisance_fit,
    cross_validated_ridge_penalty,
)
from fedcampaign_emhi.emhi.innovations import (
    center_and_scale_atom,
    sample_standard_deviation,
    unsupported_context_observation_count,
)
from fedcampaign_emhi.emhi.projection import (
    blocked_fit_is_supported,
    blocked_fold_sizes,
    proper_subset_design_column_count,
    proper_subset_design_row,
    ridge_coefficient_matrix,
    select_ridge_penalty,
)
from fedcampaign_emhi.emhi.structure import (
    bounded_basis,
    shifted_legendre_phi_four,
    shifted_legendre_phi_one,
    shifted_legendre_phi_three,
    shifted_legendre_phi_two,
    tensor_dimension,
    tensor_representation,
)


def test_bounded_basis_matches_independent_shifted_legendre() -> None:
    rank = 0.25
    assert shifted_legendre_phi_one(rank) == sqrt(3.0) * ((2.0 * rank) - 1.0)
    assert shifted_legendre_phi_two(rank) == sqrt(5.0) * ((6.0 * (rank**2)) - (6.0 * rank) + 1.0)
    assert shifted_legendre_phi_three(rank) == sqrt(7.0) * (
        (20.0 * (rank**3)) - (30.0 * (rank**2)) + (12.0 * rank) - 1.0
    )
    assert shifted_legendre_phi_four(rank) == 3.0 * (
        (70.0 * (rank**4)) - (140.0 * (rank**3)) + (90.0 * (rank**2)) - (20.0 * rank) + 1.0
    )
    loaded = load_production_configuration()
    primary = loaded.values.basis.primary_size
    assert bounded_basis(rank, primary) == (
        shifted_legendre_phi_one(rank),
        shifted_legendre_phi_two(rank),
        shifted_legendre_phi_three(rank),
    )
    sensitivity = loaded.values.basis.sensitivity_sizes
    assert bounded_basis(rank, sensitivity[0]) == (
        shifted_legendre_phi_one(rank),
        shifted_legendre_phi_two(rank),
    )
    assert len(bounded_basis(rank, sensitivity[1])) == 4


def test_tensor_is_kronecker_product_of_member_bases() -> None:
    left = bounded_basis(0.25, 2)
    right = bounded_basis(0.75, 2)
    tensor = tensor_representation((0.25, 0.75), 2)
    expected = (
        left[0] * right[0],
        left[0] * right[1],
        left[1] * right[0],
        left[1] * right[1],
    )
    assert tensor == expected
    assert tensor_dimension(2, CoalitionOrder.THREE) == 8


def test_proper_subset_design_excludes_same_order_interactions() -> None:
    order_one = proper_subset_design_row((0.4,), 3)
    assert order_one == (1.0,)
    assert proper_subset_design_column_count(CoalitionOrder.ONE, 3) == 1
    order_two = proper_subset_design_row((0.25, 0.75), 2)
    assert order_two[0] == 1.0
    assert len(order_two) == 1 + 4
    assert order_two[1:] == bounded_basis(0.25, 2) + bounded_basis(0.75, 2)
    order_three = proper_subset_design_row((0.2, 0.4, 0.8), 2)
    assert len(order_three) == proper_subset_design_column_count(CoalitionOrder.THREE, 2)
    assert len(order_three) == 1 + 6 + 12
    assert len(tensor_representation((0.2, 0.4, 0.8), 2)) == 8
    assert len(order_three) != 8


def test_ridge_does_not_penalize_intercept_or_rescale_columns() -> None:
    source = Path(ridge_coefficient_matrix.__code__.co_filename).read_text(encoding="utf-8")
    assert "float64" in source
    assert "penalty[1:, 1:]" in source
    assert "np.std" not in source
    design = ((1.0, 0.0), (1.0, 1.0), (1.0, 2.0))
    responses = ((0.0,), (1.0,), (2.0,))
    unregularized = ridge_coefficient_matrix(design, responses, 0.0, 1.0e-12)
    regularized = ridge_coefficient_matrix(design, responses, 1.0, 1.0e-12)
    assert len(unregularized) == 2
    assert len(regularized) == 2
    selected = select_ridge_penalty((0.0, 0.1, 1.0), (1.0, 1.0, 2.0), 1.0e-12)
    assert selected == 0.1
    unsorted_selected = select_ridge_penalty((1.0, 0.0, 0.1), (2.0, 1.0, 1.0), 1.0e-12)
    assert unsorted_selected == 0.1


def test_blocked_folds_and_n_less_than_k_abstain() -> None:
    assert blocked_fold_sizes(11, 5) == (3, 2, 2, 2, 2)
    assert blocked_fit_is_supported(5, 5)
    assert not blocked_fit_is_supported(4, 5)
    unsupported = cross_validated_ridge_penalty(
        ((1.0,), (1.0,), (1.0,)),
        ((0.0,), (1.0,), (0.5,)),
        (0.0, 1.0),
        5,
        1.0e-12,
        1.0e-12,
    )
    assert unsupported is None


def test_crossfit_uses_held_fold_moments_and_refits_complete_nuisance() -> None:
    design = tuple((1.0, float(index)) for index in range(10))
    tensors = tuple((float(index),) for index in range(10))
    calibrated = calibrate_innovations_on_nuisance_fit(
        design, tensors, (0.0, 1.0), 5, 1.0e-12, 1.0e-12, 1.0e-06
    )
    assert calibrated is not None
    assert len(calibrated.held_fold_innovations) == 10
    assert len(calibrated.coordinate_means) == 1
    independent = sample_standard_deviation(
        tuple(atom[0] for atom in calibrated.held_fold_innovations)
    )
    assert abs(calibrated.coordinate_deviations[0] - independent) < 1.0e-12
    scaled = center_and_scale_atom(
        calibrated.held_fold_innovations[0],
        calibrated.coordinate_means,
        calibrated.coordinate_deviations,
        1.0e-06,
    )
    assert scaled == calibrated.standardized_held_fold_innovations[0]
    assert not unsupported_context_observation_count(2)
    assert unsupported_context_observation_count(1)
    assert "threshold" not in inspect.signature(calibrate_innovations_on_nuisance_fit).parameters
    loaded = load_production_configuration()
    assert loaded.values.projection.ridge_candidates[0] == 0.0
    assert loaded.values.projection.cross_validation.fold_count == 5
