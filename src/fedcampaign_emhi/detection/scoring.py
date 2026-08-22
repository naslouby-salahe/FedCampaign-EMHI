from fedcampaign_emhi.domain.types import FiniteFloat


def oriented_score_stream(scores: tuple[FiniteFloat, ...]) -> tuple[FiniteFloat, ...]:
    if not scores:
        raise ValueError("score stream must contain at least one epoch")
    return scores
