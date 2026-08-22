from fedcampaign_emhi.domain.types import FiniteFloat, RankValue


def next_cusum_state(
    previous_state: FiniteFloat,
    rank: RankValue,
    rank_center: RankValue,
    drift_subtraction: FiniteFloat,
) -> FiniteFloat:
    candidate = previous_state + (rank - rank_center - drift_subtraction)
    if candidate < 0.0:
        return 0.0
    return candidate
