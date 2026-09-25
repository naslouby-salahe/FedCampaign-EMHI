from fedcampaign_emhi.artifacts.provenance import (
    calibration_threshold_boundary_digest,
    campaign_evaluation_boundary_digest,
    evidence_export_boundary_digest,
    material_fingerprint,
    nuisance_context_boundary_digest,
    real_campaign_comparison_contract_digest,
    statistical_analysis_boundary_digest,
    synthetic_invariant_boundary_digest,
)
from fedcampaign_emhi.artifacts.records import CampaignRecord
from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import CampaignEligibilityStatus, ScientificSemanticDependency


def test_boundary_digests_are_deterministic() -> None:
    loaded = load_production_configuration()
    for boundary in (
        nuisance_context_boundary_digest,
        calibration_threshold_boundary_digest,
        campaign_evaluation_boundary_digest,
        statistical_analysis_boundary_digest,
        evidence_export_boundary_digest,
    ):
        first = boundary(loaded.values)
        second = boundary(loaded.values)
        assert first == second


def test_scientific_semantic_dependency_changes_only_its_material_fingerprint() -> None:
    upstream = ("a" * 64,)
    coarse_rule = material_fingerprint(
        "b" * 64, upstream, (ScientificSemanticDependency.TON_COMPLETE_RAW_ROW_IDENTITY,)
    )
    corrected_rule = material_fingerprint(
        "b" * 64,
        upstream,
        (ScientificSemanticDependency.FULL_RELEASE_SOURCE_IP_COHORT_SELECTION,),
    )
    unchanged_without_semantic_dependency = material_fingerprint("b" * 64, upstream)
    reordered = material_fingerprint(
        "b" * 64,
        upstream,
        (
            ScientificSemanticDependency.FULL_RELEASE_SOURCE_IP_COHORT_SELECTION,
            ScientificSemanticDependency.TON_COMPLETE_RAW_ROW_IDENTITY,
        ),
    )
    assert coarse_rule != corrected_rule
    assert reordered == material_fingerprint(
        "b" * 64,
        upstream,
        (
            ScientificSemanticDependency.TON_COMPLETE_RAW_ROW_IDENTITY,
            ScientificSemanticDependency.FULL_RELEASE_SOURCE_IP_COHORT_SELECTION,
        ),
    )
    assert unchanged_without_semantic_dependency == material_fingerprint("b" * 64, upstream)


def test_real_comparison_contract_locks_common_trace_and_replay() -> None:
    loaded = load_production_configuration()
    campaign = CampaignRecord(
        start_epoch=100,
        end_epoch=105,
        participating_client_ids=("source-a", "source-b"),
        attack_types=("DDoS", "XSS"),
        integrity_checksum="c" * 64,
        warmup_epochs=60,
        evaluation_horizon_epochs=60,
        eligibility_status=CampaignEligibilityStatus.ELIGIBLE,
    )
    shared = real_campaign_comparison_contract_digest(
        loaded.values,
        loaded.values.datasets.primary.name,
        21,
        ("a" * 64, "b" * 64),
        ("source-a", "source-b"),
        (campaign,),
        (tuple(range(100, 160)),),
        loaded.values.local_policy.primary_horizon_pfa_target,
    )
    assert shared == real_campaign_comparison_contract_digest(
        loaded.values,
        loaded.values.datasets.primary.name,
        21,
        ("a" * 64, "b" * 64),
        ("source-a", "source-b"),
        (campaign,),
        (tuple(range(100, 160)),),
        loaded.values.local_policy.primary_horizon_pfa_target,
    )
    changed_horizon = real_campaign_comparison_contract_digest(
        loaded.values,
        loaded.values.datasets.primary.name,
        21,
        ("a" * 64, "b" * 64),
        ("source-a", "source-b"),
        (campaign,),
        (tuple(range(100, 159)),),
        loaded.values.local_policy.primary_horizon_pfa_target,
    )
    assert changed_horizon != shared


def test_reporting_change_does_not_alter_statistical_analysis_boundary() -> None:
    loaded = load_production_configuration()
    before = statistical_analysis_boundary_digest(loaded.values)
    reporting = loaded.values.reporting.model_copy(
        update={
            "precision": loaded.values.reporting.precision.model_copy(
                update={
                    "probabilities_and_rates_decimals": (
                        loaded.values.reporting.precision.probabilities_and_rates_decimals + 1
                    )
                }
            )
        }
    )
    changed = loaded.values.model_copy(update={"reporting": reporting})
    assert statistical_analysis_boundary_digest(changed) == before


def test_reporting_change_alters_evidence_export_boundary() -> None:
    loaded = load_production_configuration()
    before = evidence_export_boundary_digest(loaded.values)
    reporting = loaded.values.reporting.model_copy(
        update={
            "precision": loaded.values.reporting.precision.model_copy(
                update={
                    "probabilities_and_rates_decimals": (
                        loaded.values.reporting.precision.probabilities_and_rates_decimals + 1
                    )
                }
            )
        }
    )
    changed = loaded.values.model_copy(update={"reporting": reporting})
    assert evidence_export_boundary_digest(changed) != before


def test_detector_change_does_not_alter_calibration_threshold_boundary() -> None:
    loaded = load_production_configuration()
    before = calibration_threshold_boundary_digest(loaded.values)
    autoencoder = loaded.values.detectors.autoencoder.model_copy(
        update={"epochs": loaded.values.detectors.autoencoder.epochs + 1}
    )
    detectors = loaded.values.detectors.model_copy(update={"autoencoder": autoencoder})
    changed = loaded.values.model_copy(update={"detectors": detectors})
    assert calibration_threshold_boundary_digest(changed) == before


def test_local_policy_change_alters_calibration_threshold_boundary() -> None:
    loaded = load_production_configuration()
    before = calibration_threshold_boundary_digest(loaded.values)
    local_policy = loaded.values.local_policy.model_copy(
        update={
            "primary_horizon_pfa_target": loaded.values.local_policy.primary_horizon_pfa_target
            / 2.0
        }
    )
    changed = loaded.values.model_copy(update={"local_policy": local_policy})
    assert calibration_threshold_boundary_digest(changed) != before


def test_campaign_change_does_not_alter_nuisance_context_boundary() -> None:
    loaded = load_production_configuration()
    before = nuisance_context_boundary_digest(loaded.values)
    campaign = loaded.values.campaign.model_copy(
        update={"evaluation_horizon_epochs": loaded.values.campaign.evaluation_horizon_epochs + 1}
    )
    changed = loaded.values.model_copy(update={"campaign": campaign})
    assert nuisance_context_boundary_digest(changed) == before


def test_context_change_alters_nuisance_context_boundary() -> None:
    loaded = load_production_configuration()
    before = nuisance_context_boundary_digest(loaded.values)
    context = loaded.values.context.model_copy(
        update={"primary_cell_count": loaded.values.context.primary_cell_count + 1}
    )
    changed = loaded.values.model_copy(update={"context": context})
    assert nuisance_context_boundary_digest(changed) != before


def test_fixture_context_change_alters_synthetic_invariant_boundary() -> None:
    loaded = load_production_configuration()
    before = synthetic_invariant_boundary_digest(loaded.values)
    context = loaded.values.context.model_copy(
        update={"outside_lag_epochs": loaded.values.context.outside_lag_epochs + 1}
    )
    changed = loaded.values.model_copy(update={"context": context})
    assert synthetic_invariant_boundary_digest(changed) != before


def test_statistics_change_does_not_alter_campaign_evaluation_boundary() -> None:
    loaded = load_production_configuration()
    before = campaign_evaluation_boundary_digest(loaded.values)
    statistics = loaded.values.statistics.model_copy(
        update={"bootstrap_replicates": loaded.values.statistics.bootstrap_replicates + 1}
    )
    changed = loaded.values.model_copy(update={"statistics": statistics})
    assert campaign_evaluation_boundary_digest(changed) == before
