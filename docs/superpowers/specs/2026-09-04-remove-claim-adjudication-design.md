# Phase 1: Remove claim/manuscript adjudication from production

Date: 2026-09-04
Status: Approved

## Context

This is phase 1 of an end-to-end destructive cleanup of `FedCampaign-EMHI` (full scope tracked outside this doc). Production `src/` currently computes and persists manuscript-facing verdicts ("is this paper claim supported") via `SupportState` and related constructs. `docs/Roadmap.md` (§14/§21) already prohibits this; `tests/architecture/test_forbidden_vocabulary.py` already bans `claim`/`gate` identifier fragments but does not catch this vocabulary. This phase removes it completely, with no renamed replacement abstraction that reintroduces the same concept.

Production may keep computing and persisting: measurements, metrics, confidence intervals, p-values, adjusted p-values, effect sizes, equivalence intervals, diagnostics, scientific validity/error states, experiment completion states, missing/infeasible conditions, and plain boolean threshold comparisons. It must not interpret those into a categorical claim-support verdict.

## Non-goals

- No compatibility shims, aliases, or re-exports for anything deleted here.
- No change to the underlying scientific thresholds, criteria definitions, or measurement values — only how pass/fail is represented and whether an aggregate "claim supported" verdict is computed.
- Does not touch `experiments/campaigns.py` structural splitting (phase 2), PyTorch/Flower/stats-library migrations (later phases), or Polars/Matplotlib work (later phases). Only touch campaigns.py lines directly implicated by this removal.

## Design

### 1. `domain/enums.py`

Delete `SupportState` (all 7 members: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `MECHANISM_ONLY`, `CONDITIONAL`, `NULL_RESULT`, `NOT_SUPPORTED`, `NOT_TESTED`).

Add:

```python
class FitStatus(StrEnum):
    FITTED = "FITTED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
```

`FitStatus` is used exclusively for the EMHI calibration fit-sufficiency gate (item 2 below). It is not a claim-verdict type; it answers "did this coalition/order-context/projection-cell have enough data to fit" — confirmed binary in current usage (only `SUPPORTED`/`NOT_TESTED` values ever assigned in `emhi/calibration.py`).

### 2. Fit-sufficiency gate: `SupportState` → `FitStatus`

Files: `src/fedcampaign_emhi/emhi/calibration.py`, `src/fedcampaign_emhi/evaluation/sequential.py`, `src/fedcampaign_emhi/artifacts/records.py`.

Fields changing type from `SupportState` to `FitStatus`:
- `OrderContextFitRecord.state`
- `ProjectionCellFitRecord.state`
- `CoalitionFitRecord.state`

Value mapping: `SupportState.SUPPORTED` → `FitStatus.FITTED`; `SupportState.NOT_TESTED` → `FitStatus.INSUFFICIENT_DATA`.

Comparison sites (`emhi/calibration.py:616,855,915-917`; `evaluation/sequential.py:488,573,618`) updated from `is SupportState.SUPPORTED` / `is not SupportState.SUPPORTED` to the `FitStatus.FITTED` equivalents.

### 3. Threshold-verdict fields → plain `Boolean`, no threshold duplication

Threshold values already live in `ScientificConfig` (materiality settings) and are traceable through each record's `dependency_fingerprint`. Storing the threshold again inside the artifact would duplicate a governed value outside its authoritative owner (forbidden by project convention), so only the comparison result is persisted — not the threshold.

Field renames (all `SupportState` → `Boolean`, semantics: `True` = metric met/passed its threshold):

| Record | Old field | New field |
|---|---|---|
| `StatisticalRecord` | `decision: SupportState` | `meets_threshold: Boolean` |
| `EstimatorFeasibilityAggregationRecord` | `decision: SupportState` | `meets_threshold: Boolean` |
| `FiniteHorizonAggregationRecord` | `decision: SupportState` | `meets_threshold: Boolean` |
| `HolmFamilyResultRecord` | `decision: SupportState` | `meets_threshold: Boolean` |
| `PreparedDatasetRecord` | `selection_support_state: SupportState` | `has_sufficient_clients: Boolean` |
| `DatasetSplitRecord` | `support_state: SupportState` | `has_sufficient_clients: Boolean` |
| `domain/types.py: PrimaryClientSelection` | `support_state: SupportState` | `has_sufficient_clients: Boolean` |
| `domain/types.py: SecondaryClientSelection` | `support_state: SupportState` | `has_sufficient_clients: Boolean` |
| `evaluation/scalability.py: ScalabilitySummary` | `latency_criterion_state: SupportState` | `latency_within_target: Boolean` |
| `evaluation/scalability.py: ScalabilitySummary` | `numerical_criterion_state: SupportState` | `numerical_failure_rate_within_bound: Boolean` |

Producer sites to update (assign the boolean comparison result directly instead of constructing a `SupportState`):
- `experiments/campaigns.py` — all identified sites across `materialize_self_explanation_statistics`, `materialize_pure_order_statistics`, `materialize_hofd_equivalence_statistics`, `materialize_estimator_feasibility_statistics`, `materialize_signed_theorem_statistics`, `materialize_finite_horizon_statistics`, `_materialize_not_tested_primary_holm_statistic`, `_materialize_paired_confirmatory_odi_contrast`, `materialize_benign_common_mode_statistic`.
- `evaluation/scalability.py:232-237,422`
- `experiments/synthetic.py:621`
- `experiments/calibration.py:210,522`
- `datasets/ton_iot_network/validation.py:65,71`
- `datasets/edge_iiotset/validation.py:140,147,153`
- `execution/preprocessing.py:621,778,830,975,993`

Consumer sites to update:
- `analysis/statistics.py` — `HolmHypothesisInput.decision` / `HolmHypothesisResult.decision` dataclasses (lines ~263-276) rename to `meets_threshold: Boolean`; forwarding through `fixed_holm_family`/`primary_holm_family`/`secondary_holm_family` updated. `holm_adjusted_p_values` itself is unaffected (does not compute the field).
- `analysis/results.py:225,254,300,329` — forwards `record.decision` → `record.meets_threshold`.

### 4. Whole-construct deletion — no replacement

Delete entirely (no renamed successor — this recombines already-persisted per-metric measurements into one aggregate "is the full method's paper claim supported" verdict; each underlying metric already has its own persisted measurement + `meets_threshold` boolean from item 3, so no scientific data is lost):

- `experiments/registry.py`: `FullMethodSupportInputs`, `FullMethodSupportResult` (incl. `.all_criteria_pass`), `evaluate_full_method_support`, `strict_odi_rate_criterion`, `paired_odi_advantage_criterion`, `median_operational_lead_criterion`, `matched_operating_point_requirement`, `median_of` (only consumer is this construct).
- `artifacts/records.py`: `FullMethodSupportRecord`.
- `experiments/campaigns.py`: `_materialize_full_method_support`, `_assert_full_method_criteria`, and the call site inside `_materialize_confirmatory_odi_inferences` (`_materialize_full_method_support(loaded, repository, contrast)` at line ~3324 — remove the call; the function no longer needs to produce this artifact).

Verify before deleting: confirm nothing downstream (reporting, other experiments, CLI) reads `full-method-support.json` or imports the deleted symbols beyond the sites already inventoried. If a genuine consumer is found, surface it before deleting rather than silently breaking it.

### 5. `docs/Roadmap.md`

Update any remaining sections describing `SupportState`/full-method-support/criterion-satisfaction as *runtime output* to instead describe the same measurements as persisted metrics + boolean threshold comparisons, with no aggregate claim-verdict. Do not change the underlying thresholds, criteria definitions, or hypotheses — only the description of what the implementation persists and returns. Roadmap §14/§21 prohibition language stays as-is (already correct); align inconsistent sections to match it.

### 6. `tests/architecture/test_forbidden_vocabulary.py`

Extend the forbidden-identifier check to also reject: `SupportState`, `support_state` (as a field/identifier fragment, excluding the new `has_sufficient_clients`/`meets_threshold` names being introduced), `FullMethodSupport`, `evaluate_full_method_support`, `criterion_satisfied`, `all_criteria_pass`. This closes the gap that let this vocabulary exist despite the roadmap's existing prohibition.

### 7. Tests

Update the following test files identified as referencing the deleted/renamed symbols (field/type renames only — no test-only production code introduced, no compatibility shims):

`tests/scientific/test_sequential_routes_contracts.py`, `tests/unit/execution/test_composition_calibration.py`, `tests/unit/execution/test_signed_theorem_statistics.py`, `tests/unit/execution/test_estimator_feasibility_statistics.py`, `tests/unit/emhi/test_basis_projection_crossfit.py`, `tests/unit/analysis/test_project.py`, `tests/unit/analysis/test_multiplicity.py`, `tests/unit/evaluation/test_scalability.py`, `tests/unit/config/test_scientific_configuration.py`, `tests/unit/synthetic/test_pure_order_separation.py`, `tests/unit/synthetic/test_context_boundaries.py`, `tests/unit/experiments/test_registry.py`, `tests/unit/comparators/test_composition_challenge.py`, `tests/unit/comparators/test_contracts.py`, `tests/unit/comparators/test_composition_selection.py`, `tests/unit/datasets/edge_iiotset/test_edge_iiotset_contract.py`, `tests/unit/models/test_autoencoder_shape.py`, `tests/integration/preprocessing/test_edge_iiotset_pipeline.py`.

Remove any test that exclusively covered deleted symbols (`evaluate_full_method_support` and friends) rather than adapting it to test nothing.

## Verification

- `ruff check`, `pyright` (strict), `semgrep`, `import-linter`, `vulture`, `deptry` all pass.
- `tests/architecture/test_forbidden_vocabulary.py` passes and its new patterns actually fail against a scratch reintroduction of `SupportState` (spot check during implementation, not committed).
- Full `pytest` suite passes, including the updated test files above.
- `grep -rn "SupportState\|FullMethodSupport\|evaluate_full_method_support\|criterion_satisfied\|all_criteria_pass" src/` returns zero matches.
- Manual read of `experiments/campaigns.py` around the deleted call site confirms `_materialize_confirmatory_odi_inferences` still behaves correctly for its remaining responsibilities (materializing the paired contrast) with the full-method-support branch removed.
