from fedcampaign_emhi.domain.types import BinCount, FiniteFloat, NumericalTolerance, PositiveInt


def uniform_probability_table(
    bin_count: BinCount,
) -> tuple[tuple[tuple[FiniteFloat, ...], ...], ...]:
    cell = 1.0 / (bin_count**3)
    return tuple(
        tuple(tuple(cell for _i in range(bin_count)) for _j in range(bin_count))
        for _k in range(bin_count)
    )


def jeffreys_smoothed_probabilities(
    counts: tuple[tuple[tuple[FiniteFloat, ...], ...], ...],
    pseudocount: FiniteFloat,
) -> tuple[tuple[tuple[FiniteFloat, ...], ...], ...]:
    total = 0.0
    smoothed: list[tuple[tuple[FiniteFloat, ...], ...]] = []
    for first in counts:
        first_rows: list[tuple[FiniteFloat, ...]] = []
        for second in first:
            row = tuple(cell + pseudocount for cell in second)
            first_rows.append(row)
            total += sum(row)
        smoothed.append(tuple(first_rows))
    if total <= 0.0:
        raise ValueError("Jeffreys-smoothed table mass must be positive")
    return tuple(tuple(tuple(cell / total for cell in row) for row in layer) for layer in smoothed)


def iterative_proportional_fitting_step(
    table: tuple[tuple[tuple[FiniteFloat, ...], ...], ...],
    target_pair_ij: tuple[tuple[FiniteFloat, ...], ...],
) -> tuple[tuple[tuple[FiniteFloat, ...], ...], ...]:
    bin_count = len(table)
    updated = [[list(row) for row in layer] for layer in table]
    for i_index in range(bin_count):
        for j_index in range(bin_count):
            current = sum(updated[i_index][j_index][k_index] for k_index in range(bin_count))
            if current <= 0.0:
                continue
            scale = target_pair_ij[i_index][j_index] / current
            for k_index in range(bin_count):
                updated[i_index][j_index][k_index] *= scale
    return tuple(tuple(tuple(row) for row in layer) for layer in updated)


def ipf_converged(
    table: tuple[tuple[tuple[FiniteFloat, ...], ...], ...],
    target_pair_ij: tuple[tuple[FiniteFloat, ...], ...],
    maximum_marginal_absolute_error: NumericalTolerance,
) -> bool:
    bin_count = len(table)
    for i_index in range(bin_count):
        for j_index in range(bin_count):
            current = sum(table[i_index][j_index][k_index] for k_index in range(bin_count))
            if abs(current - target_pair_ij[i_index][j_index]) > maximum_marginal_absolute_error:
                return False
    return True


def maximum_ipf_iterations_bound(configured_limit: PositiveInt) -> PositiveInt:
    return configured_limit
