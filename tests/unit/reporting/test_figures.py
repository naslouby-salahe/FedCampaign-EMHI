import pytest

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.reporting.figures import (
    FigureSpec,
    figure_count,
    figures_contract,
    pure_order_separation_spec,
    self_explanation_curves_spec,
)


def test_figures_contract_declares_ownership() -> None:
    contract = figures_contract()
    assert contract.module_name == "fedcampaign_emhi.reporting.figures"


def test_self_explanation_curves_spec_channels() -> None:
    loaded = load_production_configuration()
    spec = self_explanation_curves_spec(
        loaded.values,
        "results/experiments/self-explanation-exclusion-validation/cell.json",
        "a" * 64,
    )
    assert spec.x_channel == "perturbation"
    assert "nuisance" in str(spec.y_channel)
    assert spec.group_channel == "context method"
    assert set(spec.facet_channels) == {"order", "nuisance family"}
    assert spec.uncertainty_level == pytest.approx(loaded.values.statistics.confidence_level)


def test_pure_order_separation_spec_channels() -> None:
    spec = pure_order_separation_spec(
        "results/experiments/pure-order-separation-validation/cell.json", "b" * 64
    )
    assert spec.x_channel == "legal generator effect"
    assert spec.y_channel == "standardized drift"
    assert set(spec.facet_channels) == {"proper-subset maximum", "target order"}


def test_non_json_sources_are_rejected() -> None:
    with pytest.raises(ValueError):
        FigureSpec(
            figure_name="bad",
            x_channel="x",
            y_channel="y",
            group_channel=None,
            facet_channels=(),
            uncertainty_level=None,
            source_path="results/experiments/x/trace.log",
            source_hash="c" * 64,
            output_path="results/experiments/x/out.json",
        )


def test_invalid_uncertainty_level_rejected() -> None:
    with pytest.raises(ValueError):
        FigureSpec(
            figure_name="bad",
            x_channel="x",
            y_channel="y",
            group_channel=None,
            facet_channels=(),
            uncertainty_level=1.0,
            source_path="results/x.json",
            source_hash="c" * 64,
            output_path="results/x-out.json",
        )


def test_figure_count() -> None:
    loaded = load_production_configuration()
    catalog = (
        self_explanation_curves_spec(loaded.values, "results/a/cell.json", "a" * 64),
        pure_order_separation_spec("results/b/cell.json", "b" * 64),
    )
    assert figure_count(catalog) == 2
