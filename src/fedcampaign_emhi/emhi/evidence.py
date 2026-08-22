from math import exp

from fedcampaign_emhi.domain.types import EvidenceFactor, FiniteFloat, PositiveFloat


def signed_evidence_factor(
    signed_statistic: FiniteFloat,
    clip_bound: PositiveFloat,
    bet_lambda: PositiveFloat,
) -> EvidenceFactor:
    compensator = (bet_lambda**2) * ((2.0 * clip_bound) ** 2) / 8.0
    return exp(bet_lambda * signed_statistic - compensator)
