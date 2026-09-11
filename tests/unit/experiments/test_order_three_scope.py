from pathlib import Path

from fedcampaign_emhi.artifacts.records import OrderThreeScopeRecord, StatisticalRecord
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import ExperimentName
from fedcampaign_emhi.experiments.seed_statistics import materialize_order_three_scope_outcome
from fedcampaign_emhi.reporting.evidence import validate_materiality_effect_records


def _contrast(repository: Path, estimate: float) -> StatisticalRecord:
    source_path = repository / "source.json"
    source_path.write_text("{}", encoding="utf-8")
    return StatisticalRecord(
        hypothesis_identifier="Full FedCampaign-EMHI vs Order at Most Two",
        metric_name="paired_strict_odi_rate_advantage",
        method_name="Full FedCampaign-EMHI",
        independent_unit_count=10,
        estimate=estimate,
        raw_p_value=0.01,
        adjusted_p_value=None,
        confidence_level=0.95,
        confidence_lower=estimate - 0.05,
        confidence_upper=estimate + 0.05,
        hodges_lehmann_shift=estimate,
        meets_threshold=True,
        source_result_ids=("source.json",),
        dependency_fingerprint="a" * 64,
        content_digest="b" * 64,
    )


def test_order_three_scope_supported_when_contribution_meets_threshold(
    tmp_path: Path, production_configuration: LoadedScientificConfiguration
) -> None:
    threshold = production_configuration.values.materiality.order_three_real.minimum_material_odi_contribution
    contrast = _contrast(tmp_path, estimate=threshold + 0.01)

    path = materialize_order_three_scope_outcome(
        production_configuration,
        tmp_path,
        ExperimentName.PURIFICATION_AND_ORDER_ABLATION,
        contrast,
    )

    record = OrderThreeScopeRecord.model_validate_json(path.read_bytes())
    assert record.material_scope_supported is True
    assert record.real_order_three_contribution == contrast.estimate
    assert record.minimum_material_odi_contribution == threshold
    validate_materiality_effect_records(tmp_path, (path,))


def test_order_three_scope_mechanism_only_when_contribution_below_threshold(
    tmp_path: Path, production_configuration: LoadedScientificConfiguration
) -> None:
    threshold = production_configuration.values.materiality.order_three_real.minimum_material_odi_contribution
    contrast = _contrast(tmp_path, estimate=threshold - 0.01)

    path = materialize_order_three_scope_outcome(
        production_configuration,
        tmp_path,
        ExperimentName.PURIFICATION_AND_ORDER_ABLATION,
        contrast,
    )

    record = OrderThreeScopeRecord.model_validate_json(path.read_bytes())
    assert record.material_scope_supported is False
