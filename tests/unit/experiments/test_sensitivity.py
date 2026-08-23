from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import ContextMethodName, DatasetName, MethodName
from fedcampaign_emhi.experiments.sensitivity import (
    SensitivityVariantName,
    enumerate_sensitivity_cells,
    exactly_one_factor_changes,
    sensitivity_p_value_never_claimed,
)


def test_matrix_reads_configuration_and_locks_base_method() -> None:
    loaded = load_production_configuration()
    matrix = enumerate_sensitivity_cells(loaded.values)
    assert matrix.dataset_name is DatasetName.TON_IOT_NETWORK
    assert matrix.base_method is MethodName.FULL_FEDCAMPAIGN_EMHI
    assert matrix.development_seed_count == len(loaded.values.randomness.real_development_roots)


def test_one_factor_cells_match_configured_grids() -> None:
    loaded = load_production_configuration()
    matrix = enumerate_sensitivity_cells(loaded.values)
    basis_count = len(loaded.values.basis.sensitivity_sizes)
    cell_count_grid = len(loaded.values.context.cell_count_sensitivity)
    assert len(matrix.cells) == basis_count + cell_count_grid + 1 + 3


def test_every_cell_changes_exactly_one_factor() -> None:
    loaded = load_production_configuration()
    matrix = enumerate_sensitivity_cells(loaded.values)
    for cell in matrix.cells:
        assert exactly_one_factor_changes(cell), cell.variant_name.label


def test_forced_ridge_cell_uses_configured_value() -> None:
    loaded = load_production_configuration()
    matrix = enumerate_sensitivity_cells(loaded.values)
    forced = [cell for cell in matrix.cells if cell.forced_ridge is not None]
    assert len(forced) == 1
    assert forced[0].forced_ridge == (
        loaded.values.experiments.context_and_estimator_sensitivity.forced_ridge
    )


def test_context_method_variants_are_the_three_declared_diagnostic_methods() -> None:
    loaded = load_production_configuration()
    matrix = enumerate_sensitivity_cells(loaded.values)
    method_variants = [cell.context_method for cell in matrix.cells if cell.context_method]
    assert set(method_variants) == {
        ContextMethodName.SHUFFLED_OUTSIDE_CONTEXT,
        ContextMethodName.LOCAL_HISTORY_ONLY_CONTEXT,
        ContextMethodName.FORCED_NO_ABSTENTION,
    }


def test_no_unadjusted_p_value_creates_claim() -> None:
    assert sensitivity_p_value_never_claimed(0.001) is True


def test_exactly_one_factor_rejects_multi_factor_cells() -> None:
    from fedcampaign_emhi.experiments.sensitivity import SensitivityCell

    multi = SensitivityCell(
        variant_name=SensitivityVariantName(label="bad"),
        basis_size=2,
        context_cell_count=8,
        forced_ridge=None,
        context_method=None,
    )
    assert exactly_one_factor_changes(multi) is False
