from fedcampaign_emhi.domain.types import (
    FiniteFloat,
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
