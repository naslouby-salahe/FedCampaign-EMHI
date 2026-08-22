from math import sqrt
from random import Random

from fedcampaign_emhi.domain.types import (
    ClientCount,
    FiniteFloat,
    LatentAutoregressiveCoefficient,
    PositiveEpochCount,
    SeedValue,
    StandardDeviation,
)
from fedcampaign_emhi.runtime.determinism import thirty_two_bit_seed


def equally_spaced_loadings(
    client_count: ClientCount, minimum_loading: FiniteFloat, maximum_loading: FiniteFloat
) -> tuple[FiniteFloat, ...]:
    if client_count == 1:
        return (minimum_loading,)
    span = maximum_loading - minimum_loading
    denominator = client_count - 1
    return tuple(minimum_loading + (span * index / denominator) for index in range(client_count))


def generate_unit_variance_autoregressive_latent(
    epoch_count: PositiveEpochCount,
    autoregressive_coefficient: LatentAutoregressiveCoefficient,
    seed: SeedValue,
) -> tuple[FiniteFloat, ...]:
    generator = Random(thirty_two_bit_seed(seed))
    innovation_scale = sqrt(1.0 - (autoregressive_coefficient**2))
    latent = 0.0
    series: list[FiniteFloat] = []
    for _epoch in range(epoch_count):
        latent = (autoregressive_coefficient * latent) + (
            innovation_scale * generator.gauss(0.0, 1.0)
        )
        series.append(latent)
    return tuple(series)


def generate_common_mode_scores(
    latent: tuple[FiniteFloat, ...],
    loadings: tuple[FiniteFloat, ...],
    noise_standard_deviation: StandardDeviation,
    seed: SeedValue,
) -> tuple[tuple[FiniteFloat, ...], ...]:
    generator = Random(thirty_two_bit_seed(seed))
    scores: list[tuple[FiniteFloat, ...]] = []
    for value in latent:
        epoch_scores = tuple(
            (loading * value) + (noise_standard_deviation * generator.gauss(0.0, 1.0))
            for loading in loadings
        )
        scores.append(epoch_scores)
    return tuple(scores)
