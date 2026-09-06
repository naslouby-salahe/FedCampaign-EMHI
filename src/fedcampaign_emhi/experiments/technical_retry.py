from collections.abc import Callable

from fedcampaign_emhi.config.schema import LoadedScientificConfiguration


def with_technical_retry[TechnicalRetryResult](
    loaded: LoadedScientificConfiguration,
    operation: Callable[[], TechnicalRetryResult],
) -> TechnicalRetryResult:
    retries = loaded.values.runtime.automatic_technical_retries_after_initial_failure
    last_error: OSError | MemoryError | None = None
    for _attempt in range(retries + 1):
        try:
            return operation()
        except (OSError, MemoryError) as error:
            last_error = error
    if last_error is None:
        raise RuntimeError("technical retry loop exited without an attempt")
    raise last_error
