import pytest

from fedcampaign_emhi.comparators.runtime import fit_comparator_state, score_comparator_ranks
from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import MethodName


def _uniform_rank_grid(client_count: int, row_count: int) -> tuple[tuple[float, ...], ...]:
    return tuple(
        tuple(
            ((index * client_count + client) + 0.5) / (row_count * client_count)
            for client in range(client_count)
        )
        for index in range(row_count)
    )


def test_hofd_runtime_scores_are_fitted_on_nuisance_rows() -> None:
    loaded = load_production_configuration()
    rows = _uniform_rank_grid(3, 400)
    fitted = fit_comparator_state(
        MethodName.EXCLUSION_MATCHED_CONDITIONAL_HOFD, rows, loaded.values
    )
    assert fitted is not None
    score, _state = score_comparator_ranks(
        MethodName.EXCLUSION_MATCHED_CONDITIONAL_HOFD,
        (0.5, 0.5, 0.5),
        loaded.values,
        (),
        fitted,
    )
    assert score > 0.0
    repeated, _state = score_comparator_ranks(
        MethodName.EXCLUSION_MATCHED_CONDITIONAL_HOFD,
        (0.5, 0.5, 0.5),
        loaded.values,
        (),
        fitted,
    )
    assert repeated == pytest.approx(score)


def test_hofd_runtime_requires_fitted_coefficients() -> None:
    loaded = load_production_configuration()
    with pytest.raises(ValueError, match="nuisance-fit"):
        score_comparator_ranks(
            MethodName.EXCLUSION_MATCHED_CONDITIONAL_HOFD,
            (0.5, 0.5, 0.5),
            loaded.values,
            (),
            None,
        )
