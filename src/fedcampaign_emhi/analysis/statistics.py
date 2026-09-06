from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy import stats as sps

from fedcampaign_emhi.domain.enums import (
    PrimaryHolmHypothesis,
    SecondaryHolmHypothesis,
    SignFlipDirection,
)
from fedcampaign_emhi.domain.types import (
    Boolean,
    ComponentName,
    EquivalenceBoundary,
    PairedDifference,
    Probability,
    RecordCount,
    SeedValue,
    StatisticValue,
)


def sign_flip_assignment_count(confirmatory_seed_count: RecordCount) -> RecordCount:
    if confirmatory_seed_count < 0:
        raise ValueError("confirmatory_seed_count must be non-negative")
    return 2**confirmatory_seed_count


def sign_flip_p_value(
    observed: StatisticValue, flipped: tuple[StatisticValue, ...], alternative_greater: Boolean
) -> Probability:
    if not flipped:
        raise ValueError("flipped statistics must be non-empty")
    if alternative_greater:
        extreme = sum(1 for statistic in flipped if statistic >= observed)
    else:
        extreme = sum(1 for statistic in flipped if statistic <= observed)
    return extreme / len(flipped)


def paired_difference(
    treatment: tuple[StatisticValue, ...], reference: tuple[StatisticValue, ...]
) -> tuple[PairedDifference, ...]:
    if len(treatment) != len(reference):
        raise ValueError("paired samples must have equal length")
    return tuple(left - right for left, right in zip(treatment, reference, strict=True))


def exact_sign_pattern(
    assignment_index: SeedValue, unit_count: RecordCount
) -> tuple[SignFlipDirection, ...]:
    if assignment_index < 0 or assignment_index >= 2**unit_count:
        raise ValueError("assignment_index is outside the exact sign-flip family")
    pattern: list[SignFlipDirection] = []
    remaining = assignment_index
    for _offset in range(unit_count):
        pattern.append(
            SignFlipDirection.POSITIVE if remaining % 2 == 0 else SignFlipDirection.NEGATIVE
        )
        remaining //= 2
    return tuple(pattern)


def flipped_mean(
    differences: tuple[PairedDifference, ...], pattern: tuple[SignFlipDirection, ...]
) -> StatisticValue:
    if len(differences) != len(pattern):
        raise ValueError("differences and sign pattern must be aligned")
    signed = tuple(difference * sign for difference, sign in zip(differences, pattern, strict=True))
    return sum(signed) / len(signed)


def exact_sign_flip_means(differences: tuple[PairedDifference, ...]) -> tuple[StatisticValue, ...]:
    if not differences:
        raise ValueError("exact sign-flip inference requires paired differences")
    return tuple(
        flipped_mean(differences, exact_sign_pattern(index, len(differences)))
        for index in range(sign_flip_assignment_count(len(differences)))
    )


def one_sided_synthetic_sign_flip_p_value(
    differences: tuple[PairedDifference, ...],
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
    values = np.asarray(differences, dtype=np.float64)
    generator = np.random.default_rng(seed)
    draw_count = monte_carlo_replicates - 1
    directions = np.asarray(
        (SignFlipDirection.NEGATIVE, SignFlipDirection.POSITIVE), dtype=np.float64
    )
    patterns = generator.choice(directions, size=(draw_count, len(values)), replace=True)
    all_positive = np.all(patterns == SignFlipDirection.POSITIVE, axis=1)
    while np.any(all_positive):
        replacement = generator.choice(
            directions, size=(int(np.sum(all_positive)), len(values)), replace=True
        )
        patterns[all_positive] = replacement
        all_positive = np.all(patterns == SignFlipDirection.POSITIVE, axis=1)
    flipped = patterns * values[np.newaxis, :]
    extreme = 1 + int(np.sum(flipped.sum(axis=1) / len(values) >= observed))
    return monte_carlo_sign_flip_p_value(extreme, monte_carlo_replicates)


def enumerate_exact_when_family_fits(
    unit_count: RecordCount, maximum_replicates: RecordCount
) -> Boolean:
    return sign_flip_assignment_count(unit_count) <= maximum_replicates


def monte_carlo_sign_flip_p_value(
    extreme_count: RecordCount, replicate_count: RecordCount
) -> Probability:
    return (1 + extreme_count) / (1 + replicate_count)


def _degenerate_bootstrap_values(
    observed: StatisticValue, replicates: NDArray[np.float64]
) -> Boolean:
    return replicates.size > 0 and bool(np.all(replicates == observed))


def _bounded_tie_proportion(
    replicates: NDArray[np.float64],
    observed: StatisticValue,
    replicate_count: RecordCount,
) -> StatisticValue:
    less = int(np.count_nonzero(replicates < observed))
    ties = int(np.count_nonzero(replicates == observed))
    proportion = (less + 0.5 * ties) / replicate_count
    boundary = 0.5 / replicate_count
    return min(max(proportion, boundary), 1.0 - boundary)


def _jackknife_acceleration(values: NDArray[np.float64]) -> StatisticValue:
    sample_count = len(values)
    if sample_count < 2:
        return 0.0
    total = float(np.sum(values))
    jackknife = (total - values) / (sample_count - 1)
    jackknife_mean = float(np.mean(jackknife))
    deviations = jackknife_mean - jackknife
    squared_sum = float(np.sum(np.square(deviations)))
    if squared_sum <= 0.0:
        return 0.0
    numerator = float(np.sum(deviations**3))
    return numerator / (6 * (squared_sum ** (3 / 2)))


def _adjusted_probability(
    nominal_probability: Probability, bias_correction: StatisticValue, acceleration: StatisticValue
) -> Probability:
    nominal_z = float(sps.norm.ppf(nominal_probability))
    numerator = bias_correction + nominal_z
    denominator = 1.0 - acceleration * numerator
    if denominator == 0.0:
        return 0.0 if numerator < 0.0 else 1.0
    adjusted = float(sps.norm.cdf(bias_correction + numerator / denominator))
    return min(max(adjusted, 0.0), 1.0)


def _bca_interval(
    values: NDArray[np.float64],
    confidence_level: Probability,
    replicate_count: RecordCount,
    seed: SeedValue,
) -> tuple[StatisticValue, StatisticValue]:
    observed = float(np.mean(values))
    generator = np.random.default_rng(seed)
    resamples = generator.choice(values, size=(replicate_count, len(values)), replace=True)
    replicates = np.mean(resamples, axis=1)
    if _degenerate_bootstrap_values(observed, replicates):
        return (observed, observed)
    proportion = _bounded_tie_proportion(replicates, observed, replicate_count)
    bias_correction = float(sps.norm.ppf(proportion))
    acceleration = _jackknife_acceleration(values)
    tail = (1.0 - confidence_level) / 2.0
    lower_probability = _adjusted_probability(tail, bias_correction, acceleration)
    upper_probability = _adjusted_probability(1.0 - tail, bias_correction, acceleration)
    quantiles = np.quantile(replicates, (lower_probability, upper_probability))
    return (float(quantiles[0]), float(quantiles[1]))


def paired_mean_bca_interval(
    paired_values: tuple[PairedDifference, ...],
    confidence_level: Probability,
    replicate_count: RecordCount,
    seed: SeedValue,
) -> tuple[StatisticValue, StatisticValue]:
    if not paired_values:
        raise ValueError("BCa interval requires independent paired seed values")
    if confidence_level <= 0.0 or confidence_level >= 1.0:
        raise ValueError("confidence level must lie strictly between zero and one")
    if replicate_count <= 0:
        raise ValueError("BCa interval requires positive bootstrap replicate count")
    values = np.asarray(paired_values, dtype=np.float64)
    return _bca_interval(values, confidence_level, replicate_count, seed)


def mean_bca_one_sided_lower_bound(
    values: tuple[StatisticValue, ...],
    confidence_level: Probability,
    replicate_count: RecordCount,
    seed: SeedValue,
) -> StatisticValue:
    if not values:
        raise ValueError("one-sided BCa bound requires independent seed values")
    if confidence_level <= 0.0 or confidence_level >= 1.0:
        raise ValueError("confidence level must lie strictly between zero and one")
    if replicate_count <= 0:
        raise ValueError("one-sided BCa bound requires positive bootstrap replicate count")
    sample = np.asarray(values, dtype=np.float64)
    observed = float(np.mean(sample))
    generator = np.random.default_rng(seed)
    resamples = generator.choice(sample, size=(replicate_count, len(sample)), replace=True)
    replicates = np.mean(resamples, axis=1)
    if _degenerate_bootstrap_values(observed, replicates):
        return observed
    proportion = _bounded_tie_proportion(replicates, observed, replicate_count)
    bias_correction = float(sps.norm.ppf(proportion))
    probability = _adjusted_probability(
        1.0 - confidence_level, bias_correction, _jackknife_acceleration(sample)
    )
    return float(np.quantile(replicates, probability))


@dataclass(frozen=True)
class HolmHypothesisInput:
    identifier: ComponentName
    raw_p_value: Probability | None
    meets_threshold: Boolean


@dataclass(frozen=True)
class HolmHypothesisResult:
    identifier: ComponentName
    raw_p_value: Probability | None
    holm_input_p_value: Probability
    adjusted_p_value: Probability | None
    meets_threshold: Boolean


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
    ordered_values = tuple(item[1] for item in ordered_by_p)
    adjusted_by_index = [0.0] * family_size
    running = 0.0
    for rank, (_identifier, _raw_p_value, original_index) in enumerate(ordered_by_p):
        candidate = min(1.0, (family_size - rank) * ordered_values[rank])
        running = max(running, candidate)
        adjusted_by_index[original_index] = running
    return tuple(adjusted_by_index)


def primary_holm_family_identifiers() -> tuple[ComponentName, ...]:
    return tuple(hypothesis.value for hypothesis in PrimaryHolmHypothesis)


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
            meets_threshold=by_identifier[identifier].meets_threshold,
        )
        for index, identifier in enumerate(identifiers)
    )


def primary_holm_family(
    inputs: tuple[HolmHypothesisInput, ...],
) -> tuple[HolmHypothesisResult, ...]:
    return fixed_holm_family(primary_holm_family_identifiers(), inputs)


def hodges_lehmann_shift(differences: tuple[PairedDifference, ...]) -> StatisticValue:
    if not differences:
        raise ValueError("Hodges-Lehmann shift requires paired differences")
    values = np.asarray(differences, dtype=np.float64)
    pairwise_means = (np.add.outer(values, values) / 2.0)[np.triu_indices(len(values))]
    return float(np.median(pairwise_means))


def interval_establishes_equivalence(
    lower: StatisticValue,
    upper: StatisticValue,
    region_lower: EquivalenceBoundary,
    region_upper: EquivalenceBoundary,
) -> Boolean:
    return lower >= region_lower and upper <= region_upper


def secondary_holm_family_identifiers() -> tuple[ComponentName, ...]:
    return tuple(hypothesis.value for hypothesis in SecondaryHolmHypothesis)


def secondary_holm_family(
    inputs: tuple[HolmHypothesisInput, ...],
) -> tuple[HolmHypothesisResult, ...]:
    return fixed_holm_family(secondary_holm_family_identifiers(), inputs)
