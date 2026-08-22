from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from fedcampaign_emhi.config.loading import (
    configuration_digest,
    histogram_edges,
    load_production_configuration,
    load_smoke_configuration,
    load_tests_configuration,
    minimum_zero_false_stop_horizons,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration, ScientificConfig
from fedcampaign_emhi.config.validation import (
    ConfigurationValidationError,
    reject_forbidden_derived_keys,
)
from fedcampaign_emhi.domain.enums import (
    ConfigurationProfile,
    DatasetName,
    MethodName,
)


def test_production_configuration_loads_locked_core_values(
    production_configuration: LoadedScientificConfiguration,
) -> None:
    values = production_configuration.values
    assert production_configuration.profile == ConfigurationProfile.PRODUCTION.value
    assert values.study.maximum_coalition_order == 3
    assert values.time.real_data_epoch_seconds == 60
    assert values.campaign.evaluation_horizon_epochs == 60
    assert values.campaign.prestart_warmup_epochs == 200
    assert values.distributed_support.minimum_clients == 2
    assert values.distributed_support.material_coalition_evidence_threshold == 1.25
    assert values.context.rank_clip_epsilon == 1.0e-12
    assert values.context.outside_histogram_bin_count == 8
    assert values.basis.primary_size == 3
    assert values.evidence.clip_bound == 1.0
    assert values.evidence.bet_lambda == 0.5
    assert values.evidence.calibrated_finite_horizon.target_pfa == 0.05
    assert values.datasets.primary.name is DatasetName.TON_IOT_NETWORK
    assert values.datasets.secondary.name is DatasetName.EDGE_IIOTSET
    assert values.detectors.isolation_forest.trees == 300
    assert values.randomness.engineering_smoke_root == 999
    assert values.randomness.statistical_analysis_base_seed == 3000
    assert values.randomness.context_base_seed == 4100
    assert values.numerics.metric_denominator_floor == 1.0e-12
    assert values.statistics.bootstrap_replicates == 10000
    assert values.runtime.automatic_technical_retries_after_initial_failure == 2
    assert values.reporting.precision.probabilities_and_rates_decimals == 3
    assert (
        values.experiments.primary_strict_odi_evaluation.methods[0]
        is MethodName.FULL_FEDCAMPAIGN_EMHI
    )


def test_derived_values_are_owned_by_implementation(
    production_configuration: LoadedScientificConfiguration,
) -> None:
    derived = production_configuration.derived
    assert derived.model_input_dimension == 66
    assert derived.heldout_benign_is_remainder is True
    assert derived.local_horizon_epochs == 60
    assert derived.synthetic_campaign_horizon_epochs == 60
    assert derived.synthetic_campaign_warmup_epochs == 200
    assert derived.synthetic_development_seed_count == 30
    assert derived.synthetic_confirmatory_seed_count == 30
    assert derived.real_development_seed_count == 10
    assert derived.real_confirmatory_seed_count == 10
    assert derived.exact_real_sign_flip_assignment_count == 1024
    assert derived.minimum_nonoverlapping_horizons_for_zero_false_stop == 59
    assert derived.signed_theorem_e_sr_threshold == 1000.0
    assert derived.signed_theorem_compensator == 0.125
    assert derived.histogram_edge_count == 9
    assert derived.outside_histogram_edges == histogram_edges(8)
    assert derived.primary_odi_table_method_order == (
        production_configuration.values.experiments.primary_strict_odi_evaluation.methods
    )
    assert derived.context_seed == 4100
    assert minimum_zero_false_stop_horizons(0.05, 0.95) == 59


def test_unknown_fields_are_rejected(repo_root: Path) -> None:
    payload = yaml.safe_load((repo_root / "configs" / "fedcampaign-emhi.yaml").read_text())
    payload["study"]["undocumented_knob"] = 1
    with pytest.raises(ValidationError):
        ScientificConfig.model_validate(payload)


def test_derived_keys_are_rejected(repo_root: Path) -> None:
    payload = yaml.safe_load((repo_root / "configs" / "fedcampaign-emhi.yaml").read_text())
    payload["model_input_dimension"] = 66
    with pytest.raises(ConfigurationValidationError):
        reject_forbidden_derived_keys(payload)


def test_digest_is_deterministic(
    production_configuration: LoadedScientificConfiguration,
) -> None:
    again = configuration_digest(production_configuration.values)
    assert again == production_configuration.material_digest
    assert len(production_configuration.material_digest) == 64


def test_reduced_configs_cannot_replace_production() -> None:
    production = load_production_configuration()
    tests = load_tests_configuration()
    smoke = load_smoke_configuration()
    assert tests.profile != production.profile
    assert smoke.profile != production.profile
    assert tests.material_digest != production.material_digest
    assert smoke.material_digest != production.material_digest
    assert production.values.claim_materiality.primary_real.minimum_strict_odi_rate == 0.2


def test_partition_fractions_leave_heldout_remainder(repo_root: Path) -> None:
    payload = deepcopy(
        yaml.safe_load((repo_root / "configs" / "fedcampaign-emhi.yaml").read_text())
    )
    payload["datasets"]["preprocessing"]["benign_partition_fractions"] = {
        "detector_fit": 0.4,
        "nuisance_fit": 0.4,
        "threshold_and_policy_calibration": 0.3,
    }
    with pytest.raises(ConfigurationValidationError):
        from fedcampaign_emhi.config.validation import validate_scientific_config

        validate_scientific_config(ScientificConfig.model_validate(payload))
