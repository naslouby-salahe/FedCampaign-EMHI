from fedcampaign_emhi.domain.types import EffectCoefficient, FiniteFloat, RankValue, SignedInt
from fedcampaign_emhi.emhi.basis import shifted_legendre_phi_one


def pure_order_one_response(ranks: tuple[RankValue, ...], theta: EffectCoefficient) -> FiniteFloat:
    return theta * sum(shifted_legendre_phi_one(rank) for rank in ranks)


def xor_parity_response(bits: tuple[SignedInt, ...], strength: FiniteFloat) -> FiniteFloat:
    parity = 0
    for bit in bits:
        parity = (parity + bit) % 2
    signed = 1.0 if parity == 1 else -1.0
    return strength * signed
