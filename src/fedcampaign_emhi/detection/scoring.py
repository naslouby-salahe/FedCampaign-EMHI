from fedcampaign_emhi.domain.types import (
    FiniteFloat,
    NumericalFloor,
    RankReference,
    RankValue,
    RecordCount,
)
from fedcampaign_emhi.emhi.ranks import clip_rank, midrank


def oriented_score_stream(scores: tuple[FiniteFloat, ...]) -> tuple[FiniteFloat, ...]:
    if not scores:
        raise ValueError("score stream must contain at least one epoch")
    return scores


def score_stream_isolation_check(score_count: RecordCount, epoch_count: RecordCount) -> None:
    if score_count != epoch_count:
        raise ValueError("detector score stream must contain exactly one score per scored epoch")


def rank_stream(
    scores: tuple[FiniteFloat, ...],
    benign_reference_scores: tuple[FiniteFloat, ...],
    rank_clip_epsilon: NumericalFloor,
) -> tuple[RankValue, ...]:
    if not benign_reference_scores:
        raise ValueError("marginal rank reference requires benign nuisance-fit scores")
    reference = RankReference(scores=benign_reference_scores)
    return tuple(clip_rank(midrank(score, reference), rank_clip_epsilon) for score in scores)
