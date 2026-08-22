from fedcampaign_emhi.datasets.preprocessing import (
    complete_benign_horizons,
    horizon_eligibility_state,
)
from fedcampaign_emhi.domain.enums import ClaimState
from fedcampaign_emhi.evaluation.benign_horizons import (
    horizons_are_nonoverlapping,
    sequential_stop_reset_epochs,
)


def test_horizons_are_consecutive_nonoverlapping_and_drop_trailing() -> None:
    epochs = tuple(range(10, 20))
    horizons = complete_benign_horizons(epochs, 3)
    assert len(horizons) == 3
    assert horizons[0].epoch_indexes == (10, 11, 12)
    assert horizons[2].epoch_indexes == (16, 17, 18)
    assert 19 not in horizons[2].epoch_indexes
    assert horizons_are_nonoverlapping(horizons)
    assert sequential_stop_reset_epochs(horizons) == (10, 13, 16)
    assert horizon_eligibility_state(len(horizons), 4) is ClaimState.NOT_TESTED
