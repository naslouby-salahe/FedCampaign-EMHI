from math import isfinite
from typing import cast

import numpy as np

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import ExperimentName
from fedcampaign_emhi.domain.types import RankValue
from fedcampaign_emhi.emhi.evidence import signed_evidence_factor, signed_statistic
from fedcampaign_emhi.emhi.sequential import next_global_state
from fedcampaign_emhi.experiments.calibration import evaluate_finite_horizon_common_mode_seed
from fedcampaign_emhi.experiments.synthetic import run_synthetic_cell
from fedcampaign_emhi.synthetic.sequential import (
    _trajectory_restricted_stop,  # pyright: ignore[reportPrivateUsage]
    evaluate_signed_theorem_seed,
    signed_theorem_coordinate,
)


def test_signed_theorem_coordinate_is_the_declared_order_three_basis_product() -> None:
    assert signed_theorem_coordinate((0.5, 0.5, 0.5)) == 0.0


def test_restricted_trajectory_specialization_preserves_rng_and_stop_semantics() -> None:
    maximum_epochs = 37
    clip_bound = 1.0
    bet_lambda = 0.5
    threshold = 3.0
    optimized_generator = np.random.default_rng(29)
    reference_generator = np.random.default_rng(29)

    optimized = _trajectory_restricted_stop(
        optimized_generator, maximum_epochs, clip_bound, bet_lambda, threshold
    )
    state = 0.0
    assumptions_hold = True
    for epoch in range(maximum_epochs):
        ranks = cast(
            tuple[RankValue, RankValue, RankValue],
            tuple(float(reference_generator.random()) for _ in range(3)),
        )
        coordinate = signed_theorem_coordinate(ranks)
        clipped = signed_statistic((coordinate,), (1.0,), clip_bound)
        factor = signed_evidence_factor(clipped, clip_bound, bet_lambda)
        assumptions_hold = assumptions_hold and (
            isfinite(coordinate)
            and isfinite(clipped)
            and -clip_bound <= clipped <= clip_bound
            and isfinite(factor)
            and factor >= 0.0
        )
        state = next_global_state(state, factor)
        if state >= threshold:
            reference = (epoch + 1, True, assumptions_hold)
            break
    else:
        reference = (maximum_epochs, False, assumptions_hold)

    assert optimized == reference


def test_signed_theorem_seed_checks_bounded_evidence_and_restricted_arl() -> None:
    loaded = load_production_configuration()
    signed = loaded.values.experiments.sequential_evidence_validation.signed_theorem.model_copy(
        update={"trajectories_per_seed": 3, "maximum_trajectory_epochs": 7}
    )
    sequential = loaded.values.experiments.sequential_evidence_validation.model_copy(
        update={"signed_theorem": signed}
    )
    experiments = loaded.values.experiments.model_copy(
        update={"sequential_evidence_validation": sequential}
    )
    config = loaded.values.model_copy(update={"experiments": experiments})

    result = evaluate_signed_theorem_seed(config, 11)

    assert result.assumptions_hold
    assert result.metrics.trajectory_count == 3
    assert result.metrics.maximum_trajectory_epochs == 7
    assert 0 <= result.metrics.stopped_trajectory_count <= 3
    assert 1.0 <= result.metrics.restricted_arl <= 7.0
    assert result.metrics.threshold == 1000.0
    assert result.metrics.compensator == 0.125


def test_sequential_experiment_materializes_signed_theorem_seed_evidence() -> None:
    loaded = load_production_configuration()
    signed = loaded.values.experiments.sequential_evidence_validation.signed_theorem.model_copy(
        update={"trajectories_per_seed": 2, "maximum_trajectory_epochs": 5}
    )
    sequential = loaded.values.experiments.sequential_evidence_validation.model_copy(
        update={"signed_theorem": signed}
    )
    experiments = loaded.values.experiments.model_copy(
        update={"sequential_evidence_validation": sequential}
    )
    small_loaded = loaded.model_copy(
        update={"values": loaded.values.model_copy(update={"experiments": experiments})}
    )

    outcome = run_synthetic_cell(
        small_loaded,
        ExperimentName.SEQUENTIAL_EVIDENCE_VALIDATION,
        11,
        None,
    )

    assert outcome.failed_checks == ()
    assert outcome.signed_theorem_metrics is not None
    assert outcome.evidence is not None


def test_finite_horizon_route_uses_the_fitted_operational_path_on_small_configuration() -> None:
    loaded = load_production_configuration()
    sample_sizes = loaded.values.synthetic.sample_sizes.model_copy(
        update={
            "generic_nuisance_fit_epochs": 25,
            "finite_horizon_calibration_horizons_per_seed": 1,
            "finite_horizon_heldout_null_horizons_per_seed": 1,
        }
    )
    synthetic = loaded.values.synthetic.model_copy(update={"sample_sizes": sample_sizes})
    campaign = loaded.values.campaign.model_copy(
        update={"prestart_warmup_epochs": 1, "evaluation_horizon_epochs": 2}
    )
    support = loaded.values.context.minimum_support_epochs.model_copy(
        update={"order_one": 1, "order_two": 1, "order_three": 1}
    )
    context = loaded.values.context.model_copy(
        update={"primary_cell_count": 1, "minimum_support_epochs": support}
    )
    pure_order = loaded.values.experiments.pure_order_separation_validation.model_copy(
        update={"primary_client_count": 4}
    )
    experiments = loaded.values.experiments.model_copy(
        update={"pure_order_separation_validation": pure_order}
    )
    config = loaded.values.model_copy(
        update={
            "synthetic": synthetic,
            "campaign": campaign,
            "context": context,
            "experiments": experiments,
        }
    )

    result = evaluate_finite_horizon_common_mode_seed(config, 11)

    assert result.assumptions_hold
    assert result.metrics.calibration_horizon_count == 1
    assert result.metrics.heldout_horizon_count == 1
