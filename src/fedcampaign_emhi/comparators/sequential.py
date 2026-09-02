from fedcampaign_emhi.domain.types import (
    CusumDriftSubtraction,
    CusumIncrement,
    CusumScore,
    CusumState,
    RankValue,
)


def centered_rank_increment(rank: RankValue, rank_center: RankValue) -> CusumIncrement:
    return rank - rank_center


def next_cusum_state(
    previous_state: CusumState,
    rank: RankValue,
    rank_center: RankValue,
    drift_subtraction: CusumDriftSubtraction,
) -> CusumState:
    candidate = previous_state + centered_rank_increment(rank, rank_center) - drift_subtraction
    if candidate < 0.0:
        return 0.0
    return candidate


def global_cusum_score(client_states: tuple[CusumState, ...]) -> CusumScore:
    if not client_states:
        raise ValueError("CUSUM global score requires at least one client state")
    return max(client_states)
