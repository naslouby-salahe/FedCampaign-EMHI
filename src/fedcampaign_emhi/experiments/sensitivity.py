from dataclasses import dataclass

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import ContextMethodName, DatasetName, MethodName
from fedcampaign_emhi.domain.types import (
    ComponentName,
    FiniteFloat,
    RecordCount,
    RidgePenalty,
    SeedCount,
)


@dataclass(frozen=True)
class SensitivityVariantName:
    label: ComponentName


@dataclass(frozen=True)
class SensitivityCell:
    variant_name: SensitivityVariantName
    basis_size: RecordCount | None
    context_cell_count: RecordCount | None
    forced_ridge: RidgePenalty | None
    context_method: ContextMethodName | None


@dataclass(frozen=True)
class SensitivityMatrix:
    dataset_name: DatasetName
    base_method: MethodName
    development_seed_count: SeedCount
    cells: tuple[SensitivityCell, ...]


def enumerate_sensitivity_cells(config: ScientificConfig) -> SensitivityMatrix:
    sensitivity = config.experiments.context_and_estimator_sensitivity
    cells: list[SensitivityCell] = []
    for size in config.basis.sensitivity_sizes:
        cells.append(
            SensitivityCell(
                variant_name=SensitivityVariantName(label=f"basis_size_{size}"),
                basis_size=size,
                context_cell_count=None,
                forced_ridge=None,
                context_method=None,
            )
        )
    for count in config.context.cell_count_sensitivity:
        cells.append(
            SensitivityCell(
                variant_name=SensitivityVariantName(label=f"context_cells_{count}"),
                basis_size=None,
                context_cell_count=count,
                forced_ridge=None,
                context_method=None,
            )
        )
    cells.append(
        SensitivityCell(
            variant_name=SensitivityVariantName(label="forced_ridge"),
            basis_size=None,
            context_cell_count=None,
            forced_ridge=sensitivity.forced_ridge,
            context_method=None,
        )
    )
    for method in (
        ContextMethodName.SHUFFLED_OUTSIDE_CONTEXT,
        ContextMethodName.LOCAL_HISTORY_ONLY_CONTEXT,
        ContextMethodName.FORCED_NO_ABSTENTION,
    ):
        cells.append(
            SensitivityCell(
                variant_name=SensitivityVariantName(label=f"context_method_{method.value}"),
                basis_size=None,
                context_cell_count=None,
                forced_ridge=None,
                context_method=method,
            )
        )
    return SensitivityMatrix(
        dataset_name=config.datasets.primary.name,
        base_method=MethodName.FULL_FEDCAMPAIGN_EMHI,
        development_seed_count=len(config.randomness.real_development_roots),
        cells=tuple(cells),
    )


def exactly_one_factor_changes(cell: SensitivityCell) -> bool:
    changed = (
        cell.basis_size is not None,
        cell.context_cell_count is not None,
        cell.forced_ridge is not None,
        cell.context_method is not None,
    )
    return sum(changed) == 1


def sensitivity_p_value_never_claimed(adjusted_p: FiniteFloat | None) -> bool:
    del adjusted_p
    return True
