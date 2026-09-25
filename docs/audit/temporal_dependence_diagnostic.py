"""One-development-seed temporal dependence diagnostic on the production path.

Run from the repository root with ``uv run python docs/audit/temporal_dependence_diagnostic.py``.
The script reads corrected preprocessing artifacts, builds scores/ranks/fits in memory with
production functions, calibrates through the production sequential evaluator, and writes only
descriptive diagnostics under the ignored ``docs/audit/pocs`` directory.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

import numpy as np

from fedcampaign_emhi.artifacts.records import (
    BenignPartitionRecord,
    CampaignRegistryRecord,
    DatasetSplitRecord,
    PreparedDatasetRecord,
)
from fedcampaign_emhi.artifacts.storage import payload_digest
from fedcampaign_emhi.config.loading import load_production_configuration, repository_root
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.detection import build_detector_score_artifact
from fedcampaign_emhi.domain.enums import DatasetName, ExperimentName, MethodName
from fedcampaign_emhi.domain.types import MaterialDependencyFingerprint
from fedcampaign_emhi.emhi.calibration import build_emhi_fit_artifact
from fedcampaign_emhi.emhi.sequential import next_global_state
from fedcampaign_emhi.emhi.structure import build_marginal_rank_artifact
from fedcampaign_emhi.evaluation.sequential import (
    TrajectoryCache,
    calibrate_operating_points,
    heldout_benign_false_stop_records,
)
from fedcampaign_emhi.experiments.execution import emhi_method_specification
from fedcampaign_emhi.experiments.seed_materialization import (
    local_pfa_target,
    preprocessing_paths,
)

MAX_EPOCH_LAG = 120
MAX_HORIZON_LAG = 30
SPACING_STRIDES = (1, 2, 5, 10)


def _acf(values: Sequence[float], max_lag: int) -> tuple[float, ...] | None:
    data = np.asarray(values, dtype=np.float64)
    if data.size < 2:
        return None
    centered = data - data.mean()
    denominator = float(centered @ centered)
    if denominator <= 0.0:
        return None
    correlated = np.correlate(centered, centered, mode="full")
    raw = correlated[data.size - 1 :]
    return tuple(float(value / denominator) for value in raw[: min(max_lag + 1, data.size)])


def _dependence_summary(values: Sequence[float], max_lag: int) -> dict[str, object]:
    acf = _acf(values, max_lag)
    if acf is None:
        return {
            "sample_count": len(values),
            "variance": 0.0,
            "lag_1_autocorrelation": None,
            "effective_sample_size_initial_positive_lags": None,
            "acf": [],
        }
    positive_lag_sum = 0.0
    for rho in acf[1:]:
        if rho <= 0.0:
            break
        positive_lag_sum += rho
    denominator = 1.0 + (2.0 * positive_lag_sum)
    return {
        "sample_count": len(values),
        "variance": float(np.var(np.asarray(values, dtype=np.float64), ddof=1)),
        "lag_1_autocorrelation": acf[1] if len(acf) > 1 else None,
        "effective_sample_size_initial_positive_lags": len(values) / denominator,
        "acf": list(acf),
    }


def _spacing_sensitivity(
    values: Sequence[float], outcomes: Sequence[int]
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for stride in SPACING_STRIDES:
        strata = [range(offset, len(values), stride) for offset in range(stride)]
        summaries: list[dict[str, object]] = []
        outcome_summaries: list[dict[str, object]] = []
        for indexes in strata:
            selected = tuple(values[index] for index in indexes)
            selected_outcomes = tuple(outcomes[index] for index in indexes)
            summaries.append(_dependence_summary(selected, max(1, MAX_HORIZON_LAG // stride)))
            outcome_summaries.append(
                _dependence_summary(selected_outcomes, max(1, MAX_HORIZON_LAG // stride))
            )
        lag_one_values: list[float] = []
        for summary in summaries:
            value = summary["lag_1_autocorrelation"]
            if isinstance(value, float):
                lag_one_values.append(value)
        outcome_lag_one_values: list[float] = []
        for summary in outcome_summaries:
            value = summary["lag_1_autocorrelation"]
            if isinstance(value, float):
                outcome_lag_one_values.append(value)
        results.append(
            {
                "stride_in_horizons": stride,
                "phase_sample_counts": [summary["sample_count"] for summary in summaries],
                "median_lag_1_autocorrelation_max_state": (
                    None if not lag_one_values else float(np.median(lag_one_values))
                ),
                "phase_lag_1_autocorrelation_range_max_state": (
                    None
                    if not lag_one_values
                    else [float(min(lag_one_values)), float(max(lag_one_values))]
                ),
                "median_lag_1_autocorrelation_false_stop": (
                    None if not outcome_lag_one_values else float(np.median(outcome_lag_one_values))
                ),
            }
        )
    return results


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    seed_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    loaded = load_production_configuration()
    repository = repository_root()
    dataset_name = DatasetName.TON_IOT_NETWORK
    inventory_path, prepared_path, split_path, partitions_path, campaigns_path = (
        preprocessing_paths(loaded, repository, dataset_name)
    )
    prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    partitions = BenignPartitionRecord.model_validate_json(partitions_path.read_bytes())
    campaigns = CampaignRegistryRecord.model_validate_json(campaigns_path.read_bytes())

    experiment_name = ExperimentName.PRIMARY_STRICT_ODI_EVALUATION
    development_roots = loaded.values.randomness.real_development_roots
    if seed_index < 0 or seed_index >= len(development_roots):
        raise ValueError(f"development seed index {seed_index} is out of range")
    seed = development_roots[seed_index]
    method_name = MethodName.FULL_FEDCAMPAIGN_EMHI
    specification = emhi_method_specification(method_name)
    if specification is None:
        raise RuntimeError("Full EMHI method specification is unavailable")

    diagnostic_identity: MaterialDependencyFingerprint = payload_digest(
        cast(
            YamlNode,
            {
                "diagnostic": "one-development-seed-production-score-evidence-temporal-dependence",
                "material_digest": loaded.material_digest,
                "seed": seed,
            },
        )
    )
    dependency_fingerprint = diagnostic_identity
    scores = build_detector_score_artifact(
        loaded.values, prepared, split, dataset_name, seed, dependency_fingerprint
    )
    ranks = build_marginal_rank_artifact(
        scores,
        split.nuisance_fit_epochs,
        loaded.values.context.rank_clip_epsilon,
        dependency_fingerprint,
    )
    fit = build_emhi_fit_artifact(
        loaded.values,
        scores,
        ranks,
        split,
        method_name,
        specification.context_method,
        specification.maximum_order,
        loaded.values.basis.primary_size,
        loaded.values.context.primary_cell_count,
        specification.purification_enabled,
        False,
        dependency_fingerprint,
    )
    cache = TrajectoryCache()
    calibration = calibrate_operating_points(
        loaded.values,
        scores,
        ranks,
        fit,
        split.nuisance_fit_epochs,
        partitions,
        local_pfa_target(loaded, experiment_name),
        maximum_order=specification.maximum_order,
        trajectory_cache=cache,
    )
    heldout = (
        heldout_benign_false_stop_records(
            loaded.values,
            ranks,
            fit,
            partitions,
            calibration.global_operating_point.threshold,
            maximum_order=specification.maximum_order,
            trajectory_cache=cache,
        )
        if calibration.global_operating_point.threshold is not None
        else ()
    )

    epoch_factors = tuple(
        factor
        for _horizon, trajectory, _stop in heldout
        for factor in (record.global_evidence_factor for record in trajectory.epochs)
    )
    horizon_maxima: list[float] = []
    false_stops: list[int] = []
    horizon_diagnostics: list[dict[str, object]] = []
    for _horizon, trajectory, stop in heldout:
        state = 0.0
        maximum_state = 0.0
        factors: list[float] = []
        for record in trajectory.epochs:
            factors.append(record.global_evidence_factor)
            state = next_global_state(state, record.global_evidence_factor)
            maximum_state = max(maximum_state, state)
        horizon_maxima.append(maximum_state)
        false_stops.append(int(stop is not None))
        horizon_diagnostics.append(
            {
                "start_epoch": _horizon.start_epoch,
                "end_epoch_inclusive": _horizon.epoch_indexes[-1],
                "maximum_cumulative_state": maximum_state,
                "final_cumulative_state": state,
                "first_false_stop_epoch": stop,
                "mean_global_evidence_factor": float(np.mean(factors)),
                "maximum_global_evidence_factor": max(factors, default=0.0),
            }
        )

    output: dict[str, object] = {
        "diagnostic_scope": "descriptive; one configured real development seed; no experiment cell or claim artifact written",
        "method": method_name.value,
        "dataset": dataset_name.value,
        "seed": seed,
        "seed_index_in_development_roots": seed_index,
        "material_digest": loaded.material_digest,
        "semantic_path": [
            "build_detector_score_artifact",
            "build_marginal_rank_artifact",
            "build_emhi_fit_artifact",
            "calibrate_operating_points",
            "heldout_benign_false_stop_records",
            "next_global_state",
        ],
        "input_sha256": {
            "inventory": _sha256(inventory_path),
            "prepared": _sha256(prepared_path),
            "splits": _sha256(split_path),
            "benign_partitions": _sha256(partitions_path),
            "campaign_registry": _sha256(campaigns_path),
        },
        "selected_clients": list(split.selected_client_ids),
        "eligible_campaign_count": len(campaigns.campaigns),
        "calibration_horizon_count": len(partitions.calibration_horizons),
        "heldout_horizon_count": len(partitions.heldout_horizons),
        "evaluation_horizon_epochs": loaded.values.campaign.evaluation_horizon_epochs,
        "calibrated_global_threshold": calibration.global_operating_point.threshold,
        "calibration_false_stop_counts": list(
            calibration.global_operating_point.calibration_false_stop_counts
        ),
        "heldout_horizons_materialized": len(heldout),
        "heldout_false_stop_count": sum(false_stops),
        "heldout_false_stop_rate": (
            None if not false_stops else sum(false_stops) / len(false_stops)
        ),
        "epoch_evidence_factor_dependence": _dependence_summary(epoch_factors, MAX_EPOCH_LAG),
        "horizon_max_cumulative_state_dependence": _dependence_summary(
            horizon_maxima, MAX_HORIZON_LAG
        ),
        "horizon_false_stop_dependence": _dependence_summary(false_stops, MAX_HORIZON_LAG),
        "horizon_spacing_sensitivity": _spacing_sensitivity(horizon_maxima, false_stops),
        "heldout_horizon_diagnostics": horizon_diagnostics,
        "limitations": [
            "A single seed is a diagnostic of the fixed trace conditional on one fitted detector and EMHI model; it is not an independence proof or confirmatory PFA evidence.",
            "Effective sample size is the descriptive initial-positive-lag estimate n/(1+2 sum rho_k), truncated at the first nonpositive lag and the prespecified maximum lag.",
            "Spacing sensitivity thins the ordered held-out horizon sequence by fixed strides and reports every phase; it does not alter calibration or the locked inferential procedure.",
        ],
    }
    outdir = repository / "docs" / "audit" / "pocs"
    outdir.mkdir(parents=True, exist_ok=True)
    output_path = outdir / f"temporal-dependence-dev-seed-{seed}.json"
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"diagnostic={output_path.relative_to(repository)}")
    print(
        json.dumps(
            {
                key: value
                for key, value in output.items()
                if key.endswith("dependence")
                or key.endswith("sensitivity")
                or key
                in {
                    "calibrated_global_threshold",
                    "heldout_false_stop_count",
                    "heldout_false_stop_rate",
                }
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
