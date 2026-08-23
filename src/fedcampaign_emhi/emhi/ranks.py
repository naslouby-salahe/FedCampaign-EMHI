from fedcampaign_emhi.artifacts.records import (
    ClientMarginalRankStream,
    DetectorScoreArtifactRecord,
    MarginalRankArtifactRecord,
)
from fedcampaign_emhi.domain.types import (
    ClientId,
    EpochIndexValue,
    FiniteFloat,
    MaterialDependencyFingerprint,
    NumericalFloor,
    RankReference,
    RankValue,
)


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


def rank_at_epoch(
    ranks: MarginalRankArtifactRecord,
    client_id: ClientId,
    epoch_index: EpochIndexValue,
) -> RankValue | None:
    stream = next(
        (stream for stream in ranks.client_streams if stream.client_id == client_id),
        None,
    )
    if stream is None:
        return None
    return next(
        (
            rank
            for epoch, rank in zip(stream.epoch_indexes, stream.ranks, strict=True)
            if epoch == epoch_index
        ),
        None,
    )


def build_marginal_rank_artifact(
    scores: DetectorScoreArtifactRecord,
    reference_epochs: tuple[EpochIndexValue, ...],
    rank_clip_epsilon: NumericalFloor,
    dependency_fingerprint: MaterialDependencyFingerprint,
) -> MarginalRankArtifactRecord:
    reference_epoch_set = set(reference_epochs)
    streams: list[ClientMarginalRankStream] = []
    for score_stream in scores.client_streams:
        reference_scores = tuple(
            score
            for epoch, score in zip(
                score_stream.epoch_indexes,
                score_stream.scores,
                strict=True,
            )
            if epoch in reference_epoch_set
        )
        if not reference_scores:
            raise ValueError(
                f"client {score_stream.client_id} has no nuisance-fit rank reference scores"
            )
        reference = RankReference(scores=reference_scores)
        ranks = tuple(
            clipped_midrank(score, reference, rank_clip_epsilon) for score in score_stream.scores
        )
        streams.append(
            ClientMarginalRankStream(
                client_id=score_stream.client_id,
                nuisance_reference_scores=reference_scores,
                epoch_indexes=score_stream.epoch_indexes,
                ranks=ranks,
            )
        )
    return MarginalRankArtifactRecord(
        dataset_name=scores.dataset_name,
        root_seed=scores.root_seed,
        selected_client_ids=scores.selected_client_ids,
        client_streams=tuple(streams),
        dependency_fingerprint=dependency_fingerprint,
    )
