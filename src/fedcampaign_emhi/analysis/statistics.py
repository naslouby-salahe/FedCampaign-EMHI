from fedcampaign_emhi.domain.enums import ExperimentalUnitKind
from fedcampaign_emhi.domain.types import (
    ClientId,
    FiniteFloat,
    PairingKey,
    Probability,
    RecordCount,
    SeedValue,
    SignedInt,
)


def sign_flip_assignment_count(confirmatory_seed_count: RecordCount) -> RecordCount:
    if confirmatory_seed_count < 0:
        raise ValueError("confirmatory_seed_count must be non-negative")
    return 2**confirmatory_seed_count


def sign_flip_p_value(
    observed: FiniteFloat, flipped: tuple[FiniteFloat, ...], alternative_greater: bool
) -> Probability:
    if not flipped:
        raise ValueError("flipped statistics must be non-empty")
    if alternative_greater:
        extreme = sum(1 for statistic in flipped if statistic >= observed)
    else:
        extreme = sum(1 for statistic in flipped if statistic <= observed)
    return extreme / len(flipped)


def paired_difference(
    treatment: tuple[FiniteFloat, ...], reference: tuple[FiniteFloat, ...]
) -> tuple[FiniteFloat, ...]:
    if len(treatment) != len(reference):
        raise ValueError("paired samples must have equal length")
    return tuple(left - right for left, right in zip(treatment, reference, strict=True))


def pairing_selected_clients(key: PairingKey) -> tuple[ClientId, ...]:
    return key.selected_client_ids


def controlled_experimental_unit() -> ExperimentalUnitKind:
    return ExperimentalUnitKind.GENERATOR_ROOT_SEED


def real_experimental_unit() -> ExperimentalUnitKind:
    return ExperimentalUnitKind.ALGORITHM_ROOT_SEED


def seed_level_aggregate(campaign_level_values: tuple[FiniteFloat, ...]) -> FiniteFloat:
    if not campaign_level_values:
        raise ValueError("seed-level aggregation requires at least one campaign-level value")
    return sum(campaign_level_values) / len(campaign_level_values)


def two_sided_sign_flip_p_value(
    observed_mean: FiniteFloat, flipped_means: tuple[FiniteFloat, ...]
) -> Probability:
    if not flipped_means:
        raise ValueError("flipped means must be non-empty")
    observed_abs = abs(observed_mean)
    extreme = sum(1 for statistic in flipped_means if abs(statistic) >= observed_abs)
    return extreme / len(flipped_means)


def enumerate_exact_when_family_fits(
    unit_count: RecordCount, maximum_replicates: RecordCount
) -> bool:
    return sign_flip_assignment_count(unit_count) <= maximum_replicates


def monte_carlo_sign_flip_p_value(
    extreme_count: RecordCount, replicate_count: RecordCount
) -> Probability:
    return (1 + extreme_count) / (1 + replicate_count)


def apply_sign_pattern(
    differences: tuple[FiniteFloat, ...], pattern: tuple[SignedInt, ...]
) -> tuple[FiniteFloat, ...]:
    if len(differences) != len(pattern):
        raise ValueError("differences and sign pattern must be aligned")
    return tuple(difference * sign for difference, sign in zip(differences, pattern, strict=True))


def flipped_mean(
    differences: tuple[FiniteFloat, ...], pattern: tuple[SignedInt, ...]
) -> FiniteFloat:
    signed = apply_sign_pattern(differences, pattern)
    return sum(signed) / len(signed)


def exact_sign_pattern(
    assignment_index: SeedValue, unit_count: RecordCount
) -> tuple[SignedInt, ...]:
    if assignment_index < 0 or assignment_index >= 2**unit_count:
        raise ValueError("assignment_index is outside the exact sign-flip family")
    pattern: list[SignedInt] = []
    remaining = assignment_index
    for _offset in range(unit_count):
        pattern.append(1 if remaining % 2 == 0 else -1)
        remaining //= 2
    return tuple(pattern)
