from fedcampaign_emhi.artifacts.provenance import (
    calibration_threshold_boundary_digest,
    campaign_evaluation_boundary_digest,
    evidence_export_boundary_digest,
    nuisance_context_boundary_digest,
    plan_boundary_digest,
    report_summary_boundary_digest,
    statistical_analysis_boundary_digest,
)
from fedcampaign_emhi.config.loading import load_tests_configuration


def test_boundary_digests_are_deterministic() -> None:
    loaded = load_tests_configuration()
    for boundary in (
        nuisance_context_boundary_digest,
        calibration_threshold_boundary_digest,
        campaign_evaluation_boundary_digest,
        statistical_analysis_boundary_digest,
        evidence_export_boundary_digest,
        report_summary_boundary_digest,
        plan_boundary_digest,
    ):
        assert boundary(loaded.values) == boundary(loaded.values)


def test_reporting_change_does_not_alter_statistical_analysis_boundary() -> None:
    loaded = load_tests_configuration()
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
    loaded = load_tests_configuration()
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
    loaded = load_tests_configuration()
    before = calibration_threshold_boundary_digest(loaded.values)
    autoencoder = loaded.values.detectors.autoencoder.model_copy(
        update={"epochs": loaded.values.detectors.autoencoder.epochs + 1}
    )
    detectors = loaded.values.detectors.model_copy(update={"autoencoder": autoencoder})
    changed = loaded.values.model_copy(update={"detectors": detectors})
    assert calibration_threshold_boundary_digest(changed) == before


def test_local_policy_change_alters_calibration_threshold_boundary() -> None:
    loaded = load_tests_configuration()
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
    loaded = load_tests_configuration()
    before = nuisance_context_boundary_digest(loaded.values)
    campaign = loaded.values.campaign.model_copy(
        update={"evaluation_horizon_epochs": loaded.values.campaign.evaluation_horizon_epochs + 1}
    )
    changed = loaded.values.model_copy(update={"campaign": campaign})
    assert nuisance_context_boundary_digest(changed) == before


def test_context_change_alters_nuisance_context_boundary() -> None:
    loaded = load_tests_configuration()
    before = nuisance_context_boundary_digest(loaded.values)
    context = loaded.values.context.model_copy(
        update={"primary_cell_count": loaded.values.context.primary_cell_count + 1}
    )
    changed = loaded.values.model_copy(update={"context": context})
    assert nuisance_context_boundary_digest(changed) != before


def test_statistics_change_does_not_alter_campaign_evaluation_boundary() -> None:
    loaded = load_tests_configuration()
    before = campaign_evaluation_boundary_digest(loaded.values)
    statistics = loaded.values.statistics.model_copy(
        update={"bootstrap_replicates": loaded.values.statistics.bootstrap_replicates + 1}
    )
    changed = loaded.values.model_copy(update={"statistics": statistics})
    assert campaign_evaluation_boundary_digest(changed) == before


def test_support_grids_change_does_not_alter_report_summary_boundary() -> None:
    loaded = load_tests_configuration()
    before = report_summary_boundary_digest(loaded.values)
    changed_plan = plan_boundary_digest(loaded.values)
    assert changed_plan != before
