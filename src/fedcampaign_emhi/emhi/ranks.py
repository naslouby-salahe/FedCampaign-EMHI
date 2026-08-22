from fedcampaign_emhi.domain.types import FiniteFloat, NumericalFloor, RankReference, RankValue


def clip_rank(rank: RankValue, epsilon: NumericalFloor) -> RankValue:
    if rank < epsilon:
        return epsilon
    upper = 1.0 - epsilon
    if rank > upper:
        return upper
    return rank


def midrank(score: FiniteFloat, reference: RankReference) -> RankValue:
    observation_count = len(reference.scores)
    if observation_count == 0:
        raise ValueError("rank reference must contain at least one score")
    less = sum(1 for reference_score in reference.scores if reference_score < score)
    equal = sum(1 for reference_score in reference.scores if reference_score == score)
    return (less + (0.5 * equal) + 0.5) / (observation_count + 1)


def clipped_midrank(
    score: FiniteFloat, reference: RankReference, epsilon: NumericalFloor
) -> RankValue:
    return clip_rank(midrank(score, reference), epsilon)


def coalition_conditioned_residual_rank(
    marginal_rank: RankValue, context_reference: RankReference, epsilon: NumericalFloor
) -> RankValue:
    return clipped_midrank(marginal_rank, context_reference, epsilon)
