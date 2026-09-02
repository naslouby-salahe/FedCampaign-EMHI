import random
from dataclasses import dataclass
from statistics import NormalDist

from fedcampaign_emhi.domain.enums import (
    ExperimentalUnitKind,
    PrimaryHolmHypothesis,
    SecondaryHolmHypothesis,
    SupportState,
)
from fedcampaign_emhi.domain.types import (
    Boolean,
    ClientId,
    ComponentName,
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
    observed: FiniteFloat, flipped: tuple[FiniteFloat, ...], alternative_greater: Boolean
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


def one_sided_synthetic_sign_flip_p_value(
    differences: tuple[FiniteFloat, ...],
    maximum_exact_replicates: RecordCount,
    monte_carlo_replicates: RecordCount,
    seed: SeedValue,
) -> Probability:
    if not differences:
        raise ValueError("one-sided sign-flip inference requires paired differences")
    observed = sum(differences) / len(differences)
    if enumerate_exact_when_family_fits(len(differences), maximum_exact_replicates):
        return sign_flip_p_value(observed, exact_sign_flip_means(differences), True)
    if monte_carlo_replicates <= 0:
        raise ValueError("Monte Carlo sign-flip inference requires positive replicate count")
    generator = random.Random(seed)
    extreme_count = 0
    for _replicate in range(monte_carlo_replicates):
        pattern = tuple(generator.choice((-1, 1)) for _value in differences)
        while all(sign == 1 for sign in pattern):
            pattern = tuple(generator.choice((-1, 1)) for _value in differences)
        if flipped_mean(differences, pattern) >= observed:
            extreme_count += 1
    return monte_carlo_sign_flip_p_value(extreme_count, monte_carlo_replicates)


def enumerate_exact_when_family_fits(
    unit_count: RecordCount, maximum_replicates: RecordCount
) -> Boolean:
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


def exact_sign_flip_means(differences: tuple[FiniteFloat, ...]) -> tuple[FiniteFloat, ...]:
    if not differences:
        raise ValueError("exact sign-flip inference requires paired differences")
    return tuple(
        flipped_mean(differences, exact_sign_pattern(index, len(differences)))
        for index in range(sign_flip_assignment_count(len(differences)))
    )


def hodges_lehmann_shift(differences: tuple[FiniteFloat, ...]) -> FiniteFloat:
    if not differences:
        raise ValueError("Hodges-Lehmann shift requires at least one paired difference")
    walsh: list[FiniteFloat] = []
    for first_index, first in enumerate(differences):
        for second in differences[first_index:]:
            walsh.append((first + second) / 2.0)
    ordered = sorted(walsh)
    count = len(ordered)
    midpoint = count // 2
    if count % 2 == 1:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def interval_establishes_equivalence(
    lower: FiniteFloat,
    upper: FiniteFloat,
    region_lower: FiniteFloat,
    region_upper: FiniteFloat,
) -> Boolean:
    return lower >= region_lower and upper <= region_upper


def degenerate_bootstrap_interval(observed: FiniteFloat) -> tuple[FiniteFloat, FiniteFloat]:
    return (observed, observed)


def bootstrap_is_degenerate(observed: FiniteFloat, replicates: tuple[FiniteFloat, ...]) -> Boolean:
    return bool(replicates) and all(statistic == observed for statistic in replicates)


def _linear_quantile(values: tuple[FiniteFloat, ...], probability: Probability) -> FiniteFloat:
    if not values:
        raise ValueError("quantile requires observations")
    if probability < 0.0 or probability > 1.0:
        raise ValueError("quantile probability must lie in [0, 1]")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = probability * (len(ordered) - 1)
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = position - lower_index
    return ordered[lower_index] + fraction * (ordered[upper_index] - ordered[lower_index])


def _jackknife_acceleration(values: tuple[FiniteFloat, ...]) -> FiniteFloat:
    if len(values) < 2:
        return 0.0
    jackknife = tuple(
        sum(value for index, value in enumerate(values) if index != omitted) / (len(values) - 1)
        for omitted in range(len(values))
    )
    jackknife_mean = sum(jackknife) / len(jackknife)
    deviations = tuple(jackknife_mean - value for value in jackknife)
    squared_sum = sum(value * value for value in deviations)
    if squared_sum == 0.0:
        return 0.0
    numerator = sum(value**3 for value in deviations)
    return numerator / (6 * (squared_sum ** (3 / 2)))


def _bca_adjusted_probability(
    nominal_probability: Probability,
    bias_correction: FiniteFloat,
    acceleration: FiniteFloat,
) -> Probability:
    normal = NormalDist()
    nominal_z = normal.inv_cdf(nominal_probability)
    numerator = bias_correction + nominal_z
    denominator = 1.0 - acceleration * numerator
    if denominator == 0.0:
        return 0.0 if numerator < 0.0 else 1.0
    adjusted = normal.cdf(bias_correction + numerator / denominator)
    return min(max(adjusted, 0.0), 1.0)


def paired_mean_bca_interval(
    paired_values: tuple[FiniteFloat, ...],
    confidence_level: Probability,
    replicate_count: RecordCount,
    seed: SeedValue,
) -> tuple[FiniteFloat, FiniteFloat]:
    if not paired_values:
        raise ValueError("BCa interval requires independent paired seed values")
    if confidence_level <= 0.0 or confidence_level >= 1.0:
        raise ValueError("confidence level must lie strictly between zero and one")
    if replicate_count <= 0:
        raise ValueError("BCa interval requires positive bootstrap replicate count")
    observed = sum(paired_values) / len(paired_values)
    generator = random.Random(seed)
    replicates = tuple(
        sum(generator.choice(paired_values) for _index in paired_values) / len(paired_values)
        for _replicate in range(replicate_count)
    )
    if bootstrap_is_degenerate(observed, replicates):
        return degenerate_bootstrap_interval(observed)
    less = sum(1 for value in replicates if value < observed)
    ties = sum(1 for value in replicates if value == observed)
    proportion = (less + 0.5 * ties) / replicate_count
    boundary = 0.5 / replicate_count
    bounded = min(max(proportion, boundary), 1.0 - boundary)
    bias_correction = NormalDist().inv_cdf(bounded)
    acceleration = _jackknife_acceleration(paired_values)
    tail = (1.0 - confidence_level) / 2.0
    lower_probability = _bca_adjusted_probability(tail, bias_correction, acceleration)
    upper_probability = _bca_adjusted_probability(1.0 - tail, bias_correction, acceleration)
    lower = _linear_quantile(replicates, lower_probability)
    upper = _linear_quantile(replicates, upper_probability)
    return (lower, upper)


def mean_bca_one_sided_lower_bound(
    values: tuple[FiniteFloat, ...],
    confidence_level: Probability,
    replicate_count: RecordCount,
    seed: SeedValue,
) -> FiniteFloat:
    if not values:
        raise ValueError("one-sided BCa bound requires independent seed values")
    if confidence_level <= 0.0 or confidence_level >= 1.0:
        raise ValueError("confidence level must lie strictly between zero and one")
    if replicate_count <= 0:
        raise ValueError("one-sided BCa bound requires positive bootstrap replicate count")
    observed = sum(values) / len(values)
    generator = random.Random(seed)
    replicates = tuple(
        sum(generator.choice(values) for _index in values) / len(values)
        for _replicate in range(replicate_count)
    )
    if bootstrap_is_degenerate(observed, replicates):
        return observed
    less = sum(1 for value in replicates if value < observed)
    ties = sum(1 for value in replicates if value == observed)
    proportion = (less + 0.5 * ties) / replicate_count
    boundary = 0.5 / replicate_count
    bounded = min(max(proportion, boundary), 1.0 - boundary)
    bias_correction = NormalDist().inv_cdf(bounded)
    probability = _bca_adjusted_probability(
        1.0 - confidence_level,
        bias_correction,
        _jackknife_acceleration(values),
    )
    return _linear_quantile(replicates, probability)


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


@dataclass(frozen=True)
class HolmHypothesisInput:
    identifier: ComponentName
    raw_p_value: Probability | None
    decision: SupportState


@dataclass(frozen=True)
class HolmHypothesisResult:
    identifier: ComponentName
    raw_p_value: Probability | None
    holm_input_p_value: Probability
    adjusted_p_value: Probability | None
    decision: SupportState


def holm_adjusted_p_values(
    identifiers: tuple[ComponentName, ...], raw_p_values: tuple[Probability, ...]
) -> tuple[Probability, ...]:
    if len(identifiers) != len(raw_p_values):
        raise ValueError("identifiers and raw_p_values must have equal length")
    family_size = len(identifiers)
    if family_size == 0:
        return ()
    ordered_by_p = sorted(
        zip(identifiers, raw_p_values, range(family_size), strict=True),
        key=lambda item: (item[1], item[0]),
    )
    adjusted_by_index = [0.0] * family_size
    running = 0.0
    for rank, (_identifier, raw_p, original_index) in enumerate(ordered_by_p):
        remaining = family_size - rank
        candidate = min(1.0, remaining * raw_p)
        running = max(running, candidate)
        adjusted_by_index[original_index] = running
    return tuple(adjusted_by_index)


def primary_holm_family_identifiers() -> tuple[ComponentName, ...]:
    return tuple(hypothesis.value for hypothesis in PrimaryHolmHypothesis)


def secondary_holm_family_identifiers() -> tuple[ComponentName, ...]:
    return tuple(hypothesis.value for hypothesis in SecondaryHolmHypothesis)


def holm_nonrejecting_input_p_value() -> Probability:
    return 1.0


def fixed_holm_family(
    identifiers: tuple[ComponentName, ...], inputs: tuple[HolmHypothesisInput, ...]
) -> tuple[HolmHypothesisResult, ...]:
    by_identifier = {input.identifier: input for input in inputs}
    if len(by_identifier) != len(inputs) or set(by_identifier) != set(identifiers):
        raise ValueError("Holm inputs must contain each declared family identifier exactly once")
    holm_input_values: list[Probability] = []
    for identifier in identifiers:
        raw_p_value = by_identifier[identifier].raw_p_value
        holm_input_values.append(
            holm_nonrejecting_input_p_value() if raw_p_value is None else raw_p_value
        )
    holm_inputs = tuple(holm_input_values)
    adjusted = holm_adjusted_p_values(identifiers, holm_inputs)
    return tuple(
        HolmHypothesisResult(
            identifier=identifier,
            raw_p_value=by_identifier[identifier].raw_p_value,
            holm_input_p_value=holm_inputs[index],
            adjusted_p_value=(
                None if by_identifier[identifier].raw_p_value is None else adjusted[index]
            ),
            decision=by_identifier[identifier].decision,
        )
        for index, identifier in enumerate(identifiers)
    )


def primary_holm_family(
    inputs: tuple[HolmHypothesisInput, ...],
) -> tuple[HolmHypothesisResult, ...]:
    return fixed_holm_family(primary_holm_family_identifiers(), inputs)


def secondary_holm_family(
    inputs: tuple[HolmHypothesisInput, ...],
) -> tuple[HolmHypothesisResult, ...]:
    return fixed_holm_family(secondary_holm_family_identifiers(), inputs)
