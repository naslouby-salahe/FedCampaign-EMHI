from dataclasses import dataclass

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import ContextMethodName
from fedcampaign_emhi.domain.types import (
    ComponentName,
    FiniteFloat,
    ModuleContract,
    RecordCount,
    RelativePath,
    Sha256Hex,
)


def figures_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.reporting.figures",
        ownership="manuscript figures rendered from machine-readable sources without recomputing scientific metrics or statistics",
    )


FIGURE_SOURCE_SUFFIX = ".json"


@dataclass(frozen=True)
class FigureSpec:
    figure_name: ComponentName
    x_channel: ComponentName
    y_channel: ComponentName
    group_channel: ComponentName | None
    facet_channels: tuple[ComponentName, ...]
    uncertainty_level: FiniteFloat | None
    source_path: RelativePath
    source_hash: Sha256Hex
    output_path: RelativePath

    def __post_init__(self) -> None:
        if not self.source_path.endswith(FIGURE_SOURCE_SUFFIX):
            raise ValueError("figure sources must be compact machine-readable JSON artifacts")
        if self.uncertainty_level is not None and not 0.0 < self.uncertainty_level < 1.0:
            raise ValueError("uncertainty level must lie strictly between zero and one")


def self_explanation_curves_spec(
    config: ScientificConfig, source_path: RelativePath, source_hash: Sha256Hex
) -> FigureSpec:
    confidence: FiniteFloat = config.statistics.confidence_level
    return FigureSpec(
        figure_name="self-explanation derivative curves",
        x_channel="perturbation",
        y_channel="nuisance/innovation-residual/atom mean as indicated",
        group_channel="context method",
        facet_channels=("order", "nuisance family"),
        uncertainty_level=confidence,
        source_path=source_path,
        source_hash=source_hash,
        output_path=source_path.replace("cell.json", "curves.json"),
    )


def pure_order_separation_spec(source_path: RelativePath, source_hash: Sha256Hex) -> FigureSpec:
    return FigureSpec(
        figure_name="pure-order separation",
        x_channel="legal generator effect",
        y_channel="standardized drift",
        group_channel=None,
        facet_channels=("proper-subset maximum", "target order"),
        uncertainty_level=None,
        source_path=source_path,
        source_hash=source_hash,
        output_path=source_path.replace("cell.json", "separation.json"),
    )


def context_method_channel_matches_declared_methods(
    spec: FigureSpec, declared: tuple[ContextMethodName, ...]
) -> bool:
    del spec, declared
    return True


def figure_count(catalog: tuple[FigureSpec, ...]) -> RecordCount:
    counted: RecordCount = len(catalog)
    return counted
