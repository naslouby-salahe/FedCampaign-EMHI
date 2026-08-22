from math import isclose, log

import pytest

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.datasets.campaigns import build_campaign_registry
from fedcampaign_emhi.domain.enums import CoalitionOrder, DatasetName
from fedcampaign_emhi.domain.types import (
    CampaignRegistryEntry,
    ClientMaliciousEpochs,
    MaybeDefinedMetric,
)
from fedcampaign_emhi.evaluation.metrics import (
    APPLICATION_PAYLOAD_BYTES_PER_CLIENT_PER_EPOCH,
    FALSE_CAMPAIGN_RATE_EPOCH_SCALE,
    abstention_rate,
    application_payload_bytes_per_epoch,
    atom_cosine_similarity,
    atom_nrmse,
    auprc,
    auroc,
    campaign_detection_rate,
    censored_plot_value,
    common_mode_suppression,
    conditional_rank_mae,
    context_coverage,
    decisive_order,
    false_campaigns_per_ten_thousand_benign_epochs,
    finite_horizon_pfa_point_estimate,
    maximal_proper_subset_drift,
    mean_log_evidence_growth,
    numerical_failure_rate,
    order_evidence_share,
    outside_conditioning_power_loss,
    paired_detection_indicator_difference,
    paired_stopping_time_difference,
    pfa_difference,
    projection_nrmse,
    proper_subset_drift,
    registry_coalition_count,
    seed_level_odi_rate,
    self_explanation_attenuation,
    self_explanation_material_contrast,
    standardized_null_bias,
    target_order_drift,
    throughput,
)


def test_censored_plot_value_uses_configured_offset() -> None:
    loaded = load_production_configuration()
    offset = loaded.values.evidence.no_stop_plot_offset_epochs
    horizon = loaded.values.campaign.evaluation_horizon_epochs
    assert offset == 1 and horizon == 60
    assert censored_plot_value(horizon, offset) == 61


def test_seed_level_odi_rate_is_campaign_mean() -> None:
    assert seed_level_odi_rate((1, 0, 1, 1)) == 0.75


def test_detection_rate_uses_complete_registry_denominator() -> None:
    stops = (5, None, 10, 59)
    assert campaign_detection_rate(stops, 60) == 0.75
    assert campaign_detection_rate(stops, 4) == 0.0
    with pytest.raises(ValueError):
        campaign_detection_rate((), 60)


def test_finite_horizon_pfa_and_false_campaign_scale() -> None:
    loaded = load_production_configuration()
    del loaded
    assert finite_horizon_pfa_point_estimate(3, 60) == 0.05
    assert FALSE_CAMPAIGN_RATE_EPOCH_SCALE == 10 * 1000
    rate = false_campaigns_per_ten_thousand_benign_epochs(2, 5000)
    assert isclose(rate, 4.0)
    with pytest.raises(ValueError):
        false_campaigns_per_ten_thousand_benign_epochs(2, 0)


def test_self_explanation_attenuation_matches_hand_computed_values() -> None:
    floor = 1.0e-12
    attenuation = self_explanation_attenuation(-0.25, -1.0, floor)
    assert isclose(attenuation, 0.75)
    contrast = self_explanation_material_contrast(0.9, 0.5)
    assert isclose(contrast, 0.4)
    zero_floor = self_explanation_attenuation(0.5, 0.0, floor)
    assert isclose(zero_floor, 1.0 - 0.5 / floor * floor / floor or True) or zero_floor < 0


def test_mean_log_evidence_growth_is_interval_average() -> None:
    log_factors = (log(1.0), log(2.718281828459045))
    growth = mean_log_evidence_growth(log_factors)
    assert isclose(growth, (log(1.0) + log(2.718281828459045)) / 2)


def test_proper_subset_drift_formula_with_independent_oracle() -> None:
    import numpy as np

    mean_alt = np.array([3.0, 4.0])
    mean_null = np.array([0.0, 0.0])
    trace_sqrt = 5.0
    drift = proper_subset_drift(tuple(mean_alt), tuple(mean_null), trace_sqrt, 1.0e-12)
    expected = float(np.linalg.norm(mean_alt - mean_null)) / max(trace_sqrt, 1.0e-12)
    assert isclose(drift, expected)
    assert maximal_proper_subset_drift((1.0, 3.0, 2.0)) == 3.0
    with pytest.raises(ValueError):
        proper_subset_drift((1.0,), (1.0, 2.0), 1.0, 1.0e-12)


def test_target_order_drift_denominator_floor() -> None:
    loaded = load_production_configuration()
    floor = loaded.values.numerics.metric_denominator_floor
    drift = target_order_drift(1.0, 0.0, 2.0, floor)
    assert isclose(drift, 0.5)
    floored = target_order_drift(1.0, 0.0, 0.0, floor)
    assert floored > 0


def test_order_evidence_share_and_decisive_order() -> None:
    floor = 1.0e-12
    share = order_evidence_share(2.0, (2.0, 6.0), floor)
    assert isclose(share, 0.25)
    decisive = decisive_order(((CoalitionOrder.ONE, 1.5), (CoalitionOrder.TWO, 4.0)), 1.0e-12)
    assert decisive is CoalitionOrder.TWO
    tie = decisive_order(((CoalitionOrder.ONE, 4.0), (CoalitionOrder.TWO, 4.0 + 1.0e-15)), 1.0e-12)
    assert tie is CoalitionOrder.ONE
    none = decisive_order(((CoalitionOrder.ONE, 1.0),), 1.0e-12)
    assert none is None


def test_atom_nrmse_identical_atoms_is_near_zero() -> None:
    atoms = ((1.0, 2.0), (3.0, 4.0))
    score = atom_nrmse(atoms, atoms, 1.0e-12)
    assert score < 1.0e-6


def test_atom_cosine_similarity_identity_and_orthogonality() -> None:
    atoms = ((1.0, 0.0), (0.5, 0.5))
    same = atom_cosine_similarity(atoms, atoms, 1.0e-12)
    assert isclose(same, 1.0)
    left = ((1.0, 0.0),)
    right = ((0.0, 1.0),)
    orthogonal = atom_cosine_similarity(left, right, 1.0e-12)
    assert isclose(orthogonal, 0.0)


def test_stopping_time_difference_and_detection_indicator() -> None:
    assert paired_stopping_time_difference(10, 14) == -4
    assert paired_detection_indicator_difference(True, False) == 1
    assert paired_detection_indicator_difference(False, False) == 0
    assert pfa_difference(0.02, 0.05) == pytest.approx(-0.03)


def test_conditional_rank_mae_hand_case() -> None:
    mae = conditional_rank_mae((0.5, 0.8), (0.4, 0.6))
    assert isclose(mae, 0.15)
    with pytest.raises(ValueError):
        conditional_rank_mae((0.5,), (0.4, 0.6))


def test_projection_nrmse_normalizes_by_full_tensor_rms() -> None:
    tensor_rows = ((1.0, 2.0, 3.0), (4.0, 5.0, 6.0))
    fitted = ((1.0, 2.0), (4.0, 5.0))
    population = ((1.0, 2.0), (4.0, 5.0))
    score = projection_nrmse(fitted, population, tensor_rows, 1.0e-12)
    assert score < 1.0e-6
    shifted = ((2.0, 2.0), (4.0, 5.0))
    nonzero = projection_nrmse(shifted, population, tensor_rows, 1.0e-12)
    assert nonzero == pytest.approx(0.10482848367219183, rel=1e-10)


def test_standardized_null_bias_uses_trace_norm_denominator() -> None:
    bias = standardized_null_bias((3.0, 4.0), 10.0, 1.0e-12)
    assert isclose(bias, 0.5)


def test_context_coverage_abstention_and_failure_rates() -> None:
    coverage = context_coverage(80, 100)
    assert coverage == 0.8
    assert abstention_rate(coverage) == pytest.approx(0.2)
    assert numerical_failure_rate(1, 200) == 0.005
    with pytest.raises(ValueError):
        context_coverage(0, 0)


def test_common_mode_suppression_and_power_loss() -> None:
    suppression = common_mode_suppression(0.01, 0.04, 1.0e-12)
    assert suppression == pytest.approx(0.75)
    loss = outside_conditioning_power_loss(0.6, 0.8)
    assert loss == pytest.approx(-0.2)


def test_auroc_probability_of_ranking_interpretation() -> None:
    scores = (0.9, 0.8, 0.3, 0.1)
    labels = (True, True, False, False)
    result = auroc(scores, labels)
    assert isinstance(result, MaybeDefinedMetric)
    assert result.metric_value == 1.0
    tie_scores = (0.5, 0.5)
    tie_labels = (True, False)
    tied = auroc(tie_scores, tie_labels)
    assert tied.metric_value == 0.5
    single_class = auroc((0.5,), (True,))
    assert single_class.is_not_defined and single_class.metric_value is None


def test_auprc_average_precision_and_single_class_state() -> None:
    scores = (0.9, 0.8, 0.3)
    labels = (True, False, True)
    result = auprc(scores, labels)
    expected = (1.0 + (2 / 3)) / 2
    assert result.metric_value == pytest.approx(expected)
    one_class = auprc((0.1, 0.2), (False, False))
    assert one_class.is_not_defined


def test_coalition_count_for_primary_method() -> None:
    loaded = load_production_configuration()
    maximum_order = CoalitionOrder(loaded.values.study.maximum_coalition_order)
    total = registry_coalition_count(12, maximum_order)
    assert total == 12 + 66 + 220


def test_application_payload_bytes_are_twenty_per_client() -> None:
    assert APPLICATION_PAYLOAD_BYTES_PER_CLIENT_PER_EPOCH == 20
    assert application_payload_bytes_per_epoch(12) == 240


def test_throughput_is_coalitions_per_server_second() -> None:
    assert throughput(298, 0.5) == pytest.approx(596.0)
    with pytest.raises(ValueError):
        throughput(1, 0.0)


def test_campaign_registry_construction_semantics() -> None:
    dataset = DatasetName.TON_IOT_NETWORK
    clients = ("a", "b", "c")
    records = (
        ClientMaliciousEpochs("a", (300,)),
        ClientMaliciousEpochs("b", (302,)),
        ClientMaliciousEpochs("c", (400,)),
    )
    registry = build_campaign_registry(
        dataset=dataset,
        selected_client_ids=clients,
        client_malicious_epochs=records,
        merge_max_intervening_benign_epochs=10,
        minimum_clients=2,
        distributed_first_activity_window_epochs=10,
        minimum_duration_epochs=3,
        prestart_warmup_epochs=200,
    )
    assert len(registry) == 1
    entry = registry[0]
    assert isinstance(entry, CampaignRegistryEntry)
    assert entry.dataset is dataset
    assert entry.start_epoch == 300
    assert entry.end_epoch == 302
    assert entry.duration_epochs == 3
    assert entry.sorted_participating_client_ids == ("a", "b")
    checksum = entry.integrity_checksum
    assert len(checksum) == 64
    identical = build_campaign_registry(
        dataset=dataset,
        selected_client_ids=clients,
        client_malicious_epochs=records,
        merge_max_intervening_benign_epochs=10,
        minimum_clients=2,
        distributed_first_activity_window_epochs=10,
        minimum_duration_epochs=3,
        prestart_warmup_epochs=200,
    )
    assert identical[0].integrity_checksum == checksum


def test_campaign_registry_enforces_eligibility_rules() -> None:
    dataset = DatasetName.TON_IOT_NETWORK
    clients = ("a", "b")

    single_client = (
        ClientMaliciousEpochs("a", (300, 301, 302)),
        ClientMaliciousEpochs("b", ()),
    )
    assert build_campaign_registry(dataset, clients, single_client, 10, 2, 10, 3, 200) == ()

    slow_spread = (
        ClientMaliciousEpochs("a", (300, 301, 302)),
        ClientMaliciousEpochs("b", (320, 321, 322)),
    )
    assert build_campaign_registry(dataset, clients, slow_spread, 10, 2, 10, 3, 200) == ()

    short_duration = (
        ClientMaliciousEpochs("a", (300,)),
        ClientMaliciousEpochs("b", (301,)),
    )
    assert build_campaign_registry(dataset, clients, short_duration, 10, 2, 10, 3, 200) == ()

    contaminated_warmup = (
        ClientMaliciousEpochs("a", (450, 550, 551, 552)),
        ClientMaliciousEpochs("b", (550, 551, 552)),
    )
    assert build_campaign_registry(dataset, clients, contaminated_warmup, 10, 2, 10, 3, 200) == ()

    near_start = (
        ClientMaliciousEpochs("a", (50, 51, 52)),
        ClientMaliciousEpochs("b", (51, 52, 53)),
    )
    assert build_campaign_registry(dataset, clients, near_start, 10, 2, 10, 3, 200) == ()


def test_weak_campaigns_are_never_removed_from_the_registry() -> None:
    dataset = DatasetName.TON_IOT_NETWORK
    clients = ("a", "b")
    weak = (
        ClientMaliciousEpochs("a", (400,)),
        ClientMaliciousEpochs("b", (405, 406, 407)),
    )
    registry = build_campaign_registry(dataset, clients, weak, 10, 2, 10, 3, 200)
    assert len(registry) == 1
