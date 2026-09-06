import math

import pytest

from fedcampaign_emhi.emhi.calibration import fitted_values_are_finite
from fedcampaign_emhi.emhi.projection import design_within_gram_condition_limit


def test_design_within_condition_limit_accepts_well_conditioned_design() -> None:
    design = ((1.0, 0.0), (1.0, 1.0), (1.0, -1.0), (1.0, 0.5))
    assert design_within_gram_condition_limit(design, 1.0e6) is True


def test_design_within_condition_limit_rejects_ill_conditioned_design() -> None:
    design = ((1.0, 1.0), (1.0, 1.0 + 1e-9), (-1.0, -1.0), (-1.0, -1.0 - 1e-9))
    assert design_within_gram_condition_limit(design, 1.0e6) is False


def test_design_within_condition_limit_handles_empty_and_constant_designs() -> None:
    assert design_within_gram_condition_limit((), 1.0e6) is False
    assert design_within_gram_condition_limit(((1.0,), (1.0,)), 1.0e6) is True
    assert design_within_gram_condition_limit(((1.0, 0.0), (1.0, 0.0)), 1.0e6) is True


def test_design_within_condition_limit_rejects_non_positive_maximum() -> None:
    with pytest.raises(ValueError):
        design_within_gram_condition_limit(((1.0,),), 0.0)


def test_fitted_values_are_finite() -> None:
    assert fitted_values_are_finite((0.1,), (0.2,), 0.3) is True
    assert fitted_values_are_finite((0.1,), (0.2,), 0.3, 0.01, ((1.0, 2.0),)) is True


def test_fitted_values_reject_non_finite_outputs() -> None:
    assert fitted_values_are_finite((0.1, math.nan), (0.2,), 0.3) is False
    assert fitted_values_are_finite((0.1,), (0.2, math.inf), 0.3) is False
    assert fitted_values_are_finite((0.1,), (0.2,), math.inf) is False
    assert fitted_values_are_finite((0.1,), (0.2,), 0.3, math.nan) is False
    assert fitted_values_are_finite((0.1,), (0.2,), 0.3, 0.0, ((1.0, math.inf),)) is False
