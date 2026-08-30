from dataclasses import dataclass

from fedcampaign_emhi.domain.enums import ClaimState, PrimaryHolmHypothesis, SecondaryHolmHypothesis
from fedcampaign_emhi.domain.types import ComponentName, Probability


@dataclass(frozen=True)
class HolmHypothesisInput:
    identifier: ComponentName
    raw_p_value: Probability | None
    decision: ClaimState


@dataclass(frozen=True)
class HolmHypothesisResult:
    identifier: ComponentName
    raw_p_value: Probability | None
    holm_input_p_value: Probability
    adjusted_p_value: Probability | None
    decision: ClaimState


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
