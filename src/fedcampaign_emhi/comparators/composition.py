from fedcampaign_emhi.domain.enums import MethodName
from fedcampaign_emhi.domain.types import FiniteFloat, NumericalTolerance, RuntimeSeconds


def select_strongest_comparator(
    candidates: tuple[MethodName, ...],
    standardized_errors: tuple[FiniteFloat, ...],
    runtimes_seconds: tuple[RuntimeSeconds, ...],
    error_tie_tolerance: NumericalTolerance,
    runtime_tie_tolerance: RuntimeSeconds,
) -> MethodName:
    if not candidates:
        raise ValueError("strong comparator composition requires at least one candidate")
    if len(candidates) != len(standardized_errors) or len(candidates) != len(runtimes_seconds):
        raise ValueError("candidates, errors, and runtimes must be aligned")
    selected_index = 0
    for index in range(1, len(candidates)):
        error_delta = standardized_errors[index] - standardized_errors[selected_index]
        if error_delta < -error_tie_tolerance:
            selected_index = index
            continue
        if abs(error_delta) <= error_tie_tolerance:
            runtime_delta = runtimes_seconds[index] - runtimes_seconds[selected_index]
            if runtime_delta < -runtime_tie_tolerance:
                selected_index = index
                continue
            if (
                abs(runtime_delta) <= runtime_tie_tolerance
                and candidates[index].value < candidates[selected_index].value
            ):
                selected_index = index
    return candidates[selected_index]
