# Remove Claim/Manuscript Adjudication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete all claim/manuscript-adjudication vocabulary and logic (`SupportState`, `FullMethodSupport*`, criterion functions) from production `src/`, replacing threshold-verdict fields with plain booleans and the calibration fit-sufficiency gate with a new `FitStatus` enum, per `docs/superpowers/specs/2026-09-04-remove-claim-adjudication-design.md`.

**Architecture:** Mechanical, deterministic rename/type-change across ~20 producer sites in `experiments/campaigns.py` plus ~15 other production files, one whole-construct deletion (`FullMethodSupport*` family, no replacement), and a new architecture-test rule to prevent recurrence. No new abstractions — every change either changes a field's type/name or deletes code outright.

**Tech Stack:** Python, Pydantic (`FrozenConfigModel`), dataclasses, pytest, ruff, pyright, semgrep, import-linter, vulture, deptry.

**Terminology mapping (apply everywhere in this plan and in any test file touched):**

| Old | New |
|---|---|
| `SupportState.SUPPORTED` (as threshold-verdict) | `True` |
| `SupportState.NULL_RESULT` / `NOT_SUPPORTED` (as threshold-verdict) | `False` |
| `SupportState.NOT_TESTED` (as threshold-verdict, dataset/statistic not evaluated) | `False` |
| `SupportState.SUPPORTED` (as fit-sufficiency) | `FitStatus.FITTED` |
| `SupportState.NOT_TESTED` (as fit-sufficiency) | `FitStatus.INSUFFICIENT_DATA` |
| field `decision: SupportState` | field `meets_threshold: Boolean` |
| field `support_state` / `selection_support_state` | field `has_sufficient_clients: Boolean` |
| field `latency_criterion_state` | field `latency_within_target: Boolean` |
| field `numerical_criterion_state` | field `numerical_failure_rate_within_bound: Boolean` |
| field `state: SupportState` (OrderContextFitRecord/ProjectionCellFitRecord/CoalitionFitRecord) | field `state: FitStatus` |
| payload dict key `"decision"` | payload dict key `"meets_threshold"` |
| payload dict value `SupportState.X.value` | plain `bool` |

---

### Task 1: `domain/enums.py` — delete `SupportState`, add `FitStatus`

**Files:**
- Modify: `src/fedcampaign_emhi/domain/enums.py:112-119`

- [ ] **Step 1: Replace the enum**

Old:
```python
class SupportState(StrEnum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    MECHANISM_ONLY = "MECHANISM_ONLY"
    CONDITIONAL = "CONDITIONAL"
    NULL_RESULT = "NULL_RESULT"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    NOT_TESTED = "NOT_TESTED"
```

New:
```python
class FitStatus(StrEnum):
    FITTED = "FITTED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
```

- [ ] **Step 2: Commit**

```bash
git add src/fedcampaign_emhi/domain/enums.py
git commit -m "$(cat <<'EOF'
Replace SupportState with FitStatus in domain enums

EOF
)"
```

This commit will not build until Tasks 2-16 finish; that's expected for this task-by-task plan — run the full verification only at Task 17.

---

### Task 2: `domain/types.py` — `PrimaryClientSelection` / `SecondaryClientSelection`

**Files:**
- Modify: `src/fedcampaign_emhi/domain/types.py:8-19` (import), `:408-413`, `:423-428`

- [ ] **Step 1: Update the enum import**

Old (`domain/types.py:8-19`):
```python
from fedcampaign_emhi.domain.enums import (
    ArtifactNamespace,
    CoalitionOrder,
    ContextMethodName,
    DatasetName,
    DetectorFamily,
    ExperimentState,
    GroundTruthClass,
    PreprocessingLayer,
    RecordExclusionReason,
    SupportState,
)
```

New:
```python
from fedcampaign_emhi.domain.enums import (
    ArtifactNamespace,
    CoalitionOrder,
    ContextMethodName,
    DatasetName,
    DetectorFamily,
    ExperimentState,
    GroundTruthClass,
    PreprocessingLayer,
    RecordExclusionReason,
)
```

- [ ] **Step 2: Rename the field on both dataclasses**

Old (`:408-413`):
```python
@dataclass(frozen=True)
class PrimaryClientSelection:
    selected_client_ids: tuple[ClientId, ...]
    eligible_client_ids: tuple[ClientId, ...]
    eligibility: tuple[ClientEligibilityRecord, ...]
    support_state: SupportState
```

New:
```python
@dataclass(frozen=True)
class PrimaryClientSelection:
    selected_client_ids: tuple[ClientId, ...]
    eligible_client_ids: tuple[ClientId, ...]
    eligibility: tuple[ClientEligibilityRecord, ...]
    has_sufficient_clients: Boolean
```

Old (`:423-428`):
```python
@dataclass(frozen=True)
class SecondaryClientSelection:
    selected_client_ids: tuple[ClientId, ...]
    eligible_client_ids: tuple[ClientId, ...]
    eligibility: tuple[ClientEligibilityRecord, ...]
    support_state: SupportState
```

New:
```python
@dataclass(frozen=True)
class SecondaryClientSelection:
    selected_client_ids: tuple[ClientId, ...]
    eligible_client_ids: tuple[ClientId, ...]
    eligibility: tuple[ClientEligibilityRecord, ...]
    has_sufficient_clients: Boolean
```

- [ ] **Step 3: Grep for constructors of these two dataclasses and update the keyword argument**

```bash
grep -rn "PrimaryClientSelection(\|SecondaryClientSelection(" src/
```

For each call site found, change `support_state=<expr>` to `has_sufficient_clients=<expr>` (the expression itself is already a boolean-producing comparison at every call site — verify each one and adjust only the keyword name, not the value, unless the value is a stray `SupportState.X` literal, in which case replace it per the terminology mapping table above).

- [ ] **Step 4: Commit**

```bash
git add src/fedcampaign_emhi/domain/types.py
git commit -m "$(cat <<'EOF'
Rename client-selection support_state to has_sufficient_clients

EOF
)"
```

---

### Task 3: `artifacts/records.py` — field renames and whole-record deletion

**Files:**
- Modify: `src/fedcampaign_emhi/artifacts/records.py`

- [ ] **Step 1: Update the enum import (line 18, alphabetical position)**

Replace `SupportState,` with `FitStatus,` in the `from fedcampaign_emhi.domain.enums import (...)` block, keeping alphabetical order (so it moves before `GroundTruthClass`... actually `FitStatus` sorts before `GroundTruthClass` and after `ExecutionRole`/`ExperimentName`/`ExperimentState`/`ExecutionRole`-type entries — place it alphabetically among the existing names in that import block).

- [ ] **Step 2: `PreparedDatasetRecord`**

Old:
```python
class PreparedDatasetRecord(FrozenConfigModel):
    dataset_name: DatasetName
    selected_client_ids: tuple[ClientId, ...] = ()
    eligible_client_ids: tuple[ClientId, ...] = ()
    selection_support_state: SupportState = SupportState.NOT_TESTED
    epochs: tuple[PreparedEpochRecord, ...]
    client_scalers: tuple[ClientFeatureScalerRecord, ...] = ()
    excluded_record_count: RecordCount
    duplicate_record_count: RecordCount = 0
    ground_truth_discrepancy_count: RecordCount
```

New:
```python
class PreparedDatasetRecord(FrozenConfigModel):
    dataset_name: DatasetName
    selected_client_ids: tuple[ClientId, ...] = ()
    eligible_client_ids: tuple[ClientId, ...] = ()
    has_sufficient_clients: Boolean = False
    epochs: tuple[PreparedEpochRecord, ...]
    client_scalers: tuple[ClientFeatureScalerRecord, ...] = ()
    excluded_record_count: RecordCount
    duplicate_record_count: RecordCount = 0
    ground_truth_discrepancy_count: RecordCount
```

- [ ] **Step 3: `DatasetSplitRecord`**

Old:
```python
class DatasetSplitRecord(FrozenConfigModel):
    dataset_name: DatasetName
    selected_client_ids: tuple[ClientId, ...]
    eligible_client_ids: tuple[ClientId, ...]
    support_state: SupportState
    detector_fit_epochs: tuple[EpochIndexValue, ...]
    nuisance_fit_epochs: tuple[EpochIndexValue, ...]
    threshold_calibration_epochs: tuple[EpochIndexValue, ...]
    heldout_benign_epochs: tuple[EpochIndexValue, ...]
```

New:
```python
class DatasetSplitRecord(FrozenConfigModel):
    dataset_name: DatasetName
    selected_client_ids: tuple[ClientId, ...]
    eligible_client_ids: tuple[ClientId, ...]
    has_sufficient_clients: Boolean
    detector_fit_epochs: tuple[EpochIndexValue, ...]
    nuisance_fit_epochs: tuple[EpochIndexValue, ...]
    threshold_calibration_epochs: tuple[EpochIndexValue, ...]
    heldout_benign_epochs: tuple[EpochIndexValue, ...]
```

- [ ] **Step 4: `OrderContextFitRecord`, `ProjectionCellFitRecord`, `CoalitionFitRecord` — `state` type only**

Old:
```python
class OrderContextFitRecord(FrozenConfigModel):
    coalition_order: CoalitionOrder
    context_method: ContextMethodName
    centroids: tuple[tuple[InnovationCoordinate, ...], ...]
    state: SupportState
```

New:
```python
class OrderContextFitRecord(FrozenConfigModel):
    coalition_order: CoalitionOrder
    context_method: ContextMethodName
    centroids: tuple[tuple[InnovationCoordinate, ...], ...]
    state: FitStatus
```

Old:
```python
class ProjectionCellFitRecord(FrozenConfigModel):
    context_cell: BinIndex
    conditional_rank_references: tuple[ConditionalRankReferenceRecord, ...]
    selected_ridge_penalty: RidgePenalty | None
    complete_nuisance_coefficients: tuple[tuple[NuisanceCoefficient, ...], ...]
    coordinate_means: tuple[InnovationMean, ...]
    coordinate_deviations: tuple[InnovationDeviation, ...]
    operational_norm_reference: OperationalNormReference | None
    state: SupportState
    numerical_failure: Boolean
```

New:
```python
class ProjectionCellFitRecord(FrozenConfigModel):
    context_cell: BinIndex
    conditional_rank_references: tuple[ConditionalRankReferenceRecord, ...]
    selected_ridge_penalty: RidgePenalty | None
    complete_nuisance_coefficients: tuple[tuple[NuisanceCoefficient, ...], ...]
    coordinate_means: tuple[InnovationMean, ...]
    coordinate_deviations: tuple[InnovationDeviation, ...]
    operational_norm_reference: OperationalNormReference | None
    state: FitStatus
    numerical_failure: Boolean
```

Old:
```python
class CoalitionFitRecord(FrozenConfigModel):
    coalition_client_ids: tuple[ClientId, ...]
    coalition_order: CoalitionOrder
    cells: tuple[ProjectionCellFitRecord, ...]
    state: SupportState
```

New:
```python
class CoalitionFitRecord(FrozenConfigModel):
    coalition_client_ids: tuple[ClientId, ...]
    coalition_order: CoalitionOrder
    cells: tuple[ProjectionCellFitRecord, ...]
    state: FitStatus
```

- [ ] **Step 5: `StatisticalRecord`, `EstimatorFeasibilityAggregationRecord`, `FiniteHorizonAggregationRecord`, `HolmFamilyResultRecord` — `decision` → `meets_threshold`**

In each of these four classes, replace the line `decision: SupportState` with `meets_threshold: Boolean`. Exact old/new per class:

`StatisticalRecord`: old `    decision: SupportState` → new `    meets_threshold: Boolean`
`EstimatorFeasibilityAggregationRecord`: old `    decision: SupportState` → new `    meets_threshold: Boolean`
`FiniteHorizonAggregationRecord`: old `    decision: SupportState` → new `    meets_threshold: Boolean`
`HolmFamilyResultRecord`: old `    decision: SupportState` → new `    meets_threshold: Boolean`

- [ ] **Step 6: Delete `FullMethodSupportRecord` entirely**

Remove lines 432-448 (the whole `class FullMethodSupportRecord(FrozenConfigModel): ...` block, from `class FullMethodSupportRecord` through the `content_digest: ConfigurationDigest` line, plus the blank lines separating it from `ReportSourceRecord`).

- [ ] **Step 7: Run pyright on this file in isolation to confirm no leftover `SupportState` reference**

```bash
grep -n "SupportState" src/fedcampaign_emhi/artifacts/records.py
```
Expected: no output.

- [ ] **Step 8: Commit**

```bash
git add src/fedcampaign_emhi/artifacts/records.py
git commit -m "$(cat <<'EOF'
Replace SupportState fields with booleans/FitStatus, delete FullMethodSupportRecord

EOF
)"
```

---

### Task 4: `experiments/registry.py` — delete the full-method-support construct

**Files:**
- Modify: `src/fedcampaign_emhi/experiments/registry.py:1-120`

- [ ] **Step 1: Delete the dataclasses, functions, and now-unused imports/module**

Delete lines 36-120 entirely (from `@dataclass(frozen=True)\nclass FullMethodSupportInputs:` through the end of `evaluate_full_method_support`, i.e. up to and including the blank lines before `def experiment_registry`).

Also delete the now-unused `import statistics` at line 1 (only consumer was `median_of`, which is deleted) and remove `OdiRateAdvantage` and `OperationalLeadEpochs` from the `domain.types` import block at lines 6-15 (they were only used by the deleted dataclasses/functions — verify with `grep -n "OdiRateAdvantage\|OperationalLeadEpochs" src/fedcampaign_emhi/experiments/registry.py` after deletion; if either still appears elsewhere in the file, keep it).

The resulting file should start:
```python
from dataclasses import dataclass

from fedcampaign_emhi.config.schema import LoadedScientificConfiguration, ScientificConfig
from fedcampaign_emhi.domain.enums import ExecutionRole, ExperimentName, MethodName
from fedcampaign_emhi.domain.types import (
    ArtifactFilename,
    Boolean,
    Probability,
    ResumeStep,
    SeedCount,
    SeedValue,
)

RESUME_SEQUENCE: tuple[ResumeStep, ...] = (
    "validate required existing artifacts",
    "reuse compatible ancestors",
    "identify incompatible or incomplete artifacts",
    "invalidate only their descendants",
    "reconstruct the minimum required subgraph",
    "atomically publish completed outputs",
)


@dataclass(frozen=True)
class ExperimentContract:
    experiment_name: ExperimentName
    execution_roles: tuple[ExecutionRole, ...]
    methods: tuple[MethodName, ...]
    uses_real_seeds: Boolean
    uses_synthetic_seeds: Boolean


def experiment_registry(config: ScientificConfig) -> tuple[ExperimentContract, ...]:
    ...
```

(`Probability` stays imported — confirm it is still used later in the file by `confirmatory_completeness_within_tolerance` or other functions; if not, remove it too. Check with `grep -n "Probability" src/fedcampaign_emhi/experiments/registry.py`.)

- [ ] **Step 2: Verify no leftover references**

```bash
grep -n "FullMethodSupport\|evaluate_full_method_support\|strict_odi_rate_criterion\|paired_odi_advantage_criterion\|median_operational_lead_criterion\|matched_operating_point_requirement\|median_of" src/fedcampaign_emhi/experiments/registry.py
```
Expected: no output.

- [ ] **Step 3: Commit**

```bash
git add src/fedcampaign_emhi/experiments/registry.py
git commit -m "$(cat <<'EOF'
Delete FullMethodSupport adjudication construct from registry

EOF
)"
```

---

### Task 5: `analysis/statistics.py` — `HolmHypothesisInput`/`HolmHypothesisResult`

**Files:**
- Modify: `src/fedcampaign_emhi/analysis/statistics.py:6-11`, `:262-276`, `:330`

- [ ] **Step 1: Update the enum import**

Old (`:6-11`):
```python
from fedcampaign_emhi.domain.enums import (
    PrimaryHolmHypothesis,
    SecondaryHolmHypothesis,
    SignFlipDirection,
    SupportState,
)
```

New:
```python
from fedcampaign_emhi.domain.enums import (
    PrimaryHolmHypothesis,
    SecondaryHolmHypothesis,
    SignFlipDirection,
)
```

- [ ] **Step 2: Rename `decision` field on both dataclasses**

Old (`:262-267`):
```python
@dataclass(frozen=True)
class HolmHypothesisInput:
    identifier: ComponentName
    raw_p_value: Probability | None
    decision: SupportState
```

New:
```python
@dataclass(frozen=True)
class HolmHypothesisInput:
    identifier: ComponentName
    raw_p_value: Probability | None
    meets_threshold: Boolean
```

Old (`:269-276`):
```python
@dataclass(frozen=True)
class HolmHypothesisResult:
    identifier: ComponentName
    raw_p_value: Probability | None
    holm_input_p_value: Probability
    adjusted_p_value: Probability | None
    decision: SupportState
```

New:
```python
@dataclass(frozen=True)
class HolmHypothesisResult:
    identifier: ComponentName
    raw_p_value: Probability | None
    holm_input_p_value: Probability
    adjusted_p_value: Probability | None
    meets_threshold: Boolean
```

- [ ] **Step 3: Update the forwarding line inside `fixed_holm_family`**

Old (`:330`):
```python
            decision=by_identifier[identifier].decision,
```

New:
```python
            meets_threshold=by_identifier[identifier].meets_threshold,
```

- [ ] **Step 4: Commit**

```bash
git add src/fedcampaign_emhi/analysis/statistics.py
git commit -m "$(cat <<'EOF'
Rename Holm hypothesis decision field to meets_threshold

EOF
)"
```

---

### Task 6: `analysis/results.py` — forward the renamed field

**Files:**
- Modify: `src/fedcampaign_emhi/analysis/results.py:222-260`, `:296-336`

- [ ] **Step 1: `materialize_primary_holm_family` — update the three `decision` usages**

Old (`:225`, inside the `inputs.append(HolmHypothesisInput(...))` call):
```python
        inputs.append(
            HolmHypothesisInput(
                identifier=hypothesis.value,
                raw_p_value=record.raw_p_value,
                decision=record.decision,
            )
        )
```

New:
```python
        inputs.append(
            HolmHypothesisInput(
                identifier=hypothesis.value,
                raw_p_value=record.raw_p_value,
                meets_threshold=record.meets_threshold,
            )
        )
```

Old (`:239`, inside the `payload` dict comprehension):
```python
                "decision": result.decision.value,
```

New:
```python
                "meets_threshold": result.meets_threshold,
```

Old (`:249-256`, inside the `HolmFamilyResultRecord(...)` construction):
```python
            HolmFamilyResultRecord(
                hypothesis_identifier=result.identifier,
                raw_p_value=result.raw_p_value,
                holm_input_p_value=result.holm_input_p_value,
                adjusted_p_value=result.adjusted_p_value,
                decision=result.decision,
            )
```

New:
```python
            HolmFamilyResultRecord(
                hypothesis_identifier=result.identifier,
                raw_p_value=result.raw_p_value,
                holm_input_p_value=result.holm_input_p_value,
                adjusted_p_value=result.adjusted_p_value,
                meets_threshold=result.meets_threshold,
            )
```

- [ ] **Step 2: `materialize_secondary_holm_family` — same three edits at lines 296-330**

Apply the identical three old/new replacements shown in Step 1 to the corresponding lines inside `materialize_secondary_holm_family` (lines ~296, ~314, ~324-330 — same code shape, different function).

- [ ] **Step 3: Commit**

```bash
git add src/fedcampaign_emhi/analysis/results.py
git commit -m "$(cat <<'EOF'
Forward renamed meets_threshold field through Holm family materialization

EOF
)"
```

---

### Task 7: `experiments/campaigns.py` — producer sites (part 1: self-explanation, pure-order, HOFD equivalence)

**Files:**
- Modify: `src/fedcampaign_emhi/experiments/campaigns.py:125` (import), `:1081-1087`, `:1162-1166`, `:1225`, `:1280-1284`, `:1312`

- [ ] **Step 1: Remove `SupportState` from the enum import**

Find the import block around line 125 containing `SupportState,` (part of a larger `from fedcampaign_emhi.domain.enums import (...)` block) and delete that line.

- [ ] **Step 2: `materialize_self_explanation_statistics` — lines 1081-1087**

Old:
```python
        decision=(
            SupportState.SUPPORTED
            if primary_directional_test_passes(
                raw_p_value, loaded.values.statistics.nominal_significance_alpha
            )
            else SupportState.NULL_RESULT
        ),
```

New:
```python
        meets_threshold=primary_directional_test_passes(
            raw_p_value, loaded.values.statistics.nominal_significance_alpha
        ),
```

- [ ] **Step 3: `materialize_pure_order_statistics` — lines 1162-1166**

Old:
```python
        decision=(
            SupportState.SUPPORTED
            if raw_p_value < loaded.values.statistics.nominal_significance_alpha
            else SupportState.NULL_RESULT
        ),
```

New:
```python
        meets_threshold=raw_p_value < loaded.values.statistics.nominal_significance_alpha,
```

- [ ] **Step 4: `materialize_hofd_equivalence_statistics` — line 1225 (the "not enough matched observations" branch)**

Old:
```python
                conditions.append(
                    {
                        "coalition_order": order,
                        "support_per_context": support,
                        "decision": SupportState.NOT_TESTED.value,
                    }
                )
```

New:
```python
                conditions.append(
                    {
                        "coalition_order": order,
                        "support_per_context": support,
                        "meets_threshold": False,
                    }
                )
```

- [ ] **Step 5: same function — lines 1280-1284 (the per-condition decision inside the payload dict)**

Old:
```python
                    "decision": (
                        SupportState.SUPPORTED.value
                        if supported
                        else SupportState.NULL_RESULT.value
                    ),
```

New:
```python
                    "meets_threshold": supported,
```

- [ ] **Step 6: same function — line 1312 (the `StatisticalRecord(...)` construction)**

Old:
```python
        decision=SupportState.SUPPORTED if all_supported else SupportState.NULL_RESULT,
```

New:
```python
        meets_threshold=all_supported,
```

- [ ] **Step 7: Commit**

```bash
git add src/fedcampaign_emhi/experiments/campaigns.py
git commit -m "$(cat <<'EOF'
Replace SupportState verdicts with booleans in self-explanation/pure-order/HOFD statistics

EOF
)"
```

---

### Task 8: `experiments/campaigns.py` — producer sites (part 2: estimator feasibility, signed theorem, finite horizon)

**Files:**
- Modify: `src/fedcampaign_emhi/experiments/campaigns.py:1437-1477`, `:1546`, `:1588-1616`

- [ ] **Step 1: `materialize_estimator_feasibility_statistics` — lines 1437-1449 (the `decision` local variable)**

Old:
```python
    decision = (
        SupportState.SUPPORTED
        if (
            sum(metric.context_coverage for metric in metrics) / len(metrics)
            >= materiality.order_three_estimator.minimum_mean_context_coverage
            and sum(metric.projection_nrmse for metric in metrics) / len(metrics)
            <= materiality.order_three_estimator.maximum_mean_projection_nrmse
            and sum(metric.standardized_null_bias for metric in metrics) / len(metrics)
            <= materiality.order_three_estimator.maximum_mean_standardized_null_bias
            and failure_rate <= materiality.maximum_pooled_numerical_failure_rate
        )
        else SupportState.NULL_RESULT
    )
```

New:
```python
    meets_threshold = (
        sum(metric.context_coverage for metric in metrics) / len(metrics)
        >= materiality.order_three_estimator.minimum_mean_context_coverage
        and sum(metric.projection_nrmse for metric in metrics) / len(metrics)
        <= materiality.order_three_estimator.maximum_mean_projection_nrmse
        and sum(metric.standardized_null_bias for metric in metrics) / len(metrics)
        <= materiality.order_three_estimator.maximum_mean_standardized_null_bias
        and failure_rate <= materiality.maximum_pooled_numerical_failure_rate
    )
```

- [ ] **Step 2: same function — payload dict key (was `"decision": decision.value,`)**

Old:
```python
        "decision": decision.value,
```

New:
```python
        "meets_threshold": meets_threshold,
```

- [ ] **Step 3: same function — `EstimatorFeasibilityAggregationRecord(...)` construction (was `decision=decision,`)**

Old:
```python
        decision=decision,
```

New:
```python
        meets_threshold=meets_threshold,
```

- [ ] **Step 4: `materialize_signed_theorem_statistics` — line 1546**

Old:
```python
        decision=(SupportState.SUPPORTED if lower >= threshold else SupportState.NULL_RESULT),
```

New:
```python
        meets_threshold=lower >= threshold,
```

- [ ] **Step 5: `materialize_finite_horizon_statistics` — lines 1588-1596 (the `decision` local variable)**

Old:
```python
    decision = (
        SupportState.NOT_SUPPORTED
        if unavailable_count > 0
        else (
            SupportState.SUPPORTED
            if maximum_upper is not None and maximum_upper <= target
            else SupportState.NULL_RESULT
        )
    )
```

New:
```python
    meets_threshold = (
        unavailable_count == 0 and maximum_upper is not None and maximum_upper <= target
    )
```

- [ ] **Step 6: same function — payload dict key (was `"decision": decision.value,`)**

Old:
```python
        "decision": decision.value,
```

New:
```python
        "meets_threshold": meets_threshold,
```

- [ ] **Step 7: same function — `FiniteHorizonAggregationRecord(...)` construction (was `decision=decision,`)**

Old:
```python
        decision=decision,
```

New:
```python
        meets_threshold=meets_threshold,
```

- [ ] **Step 8: Commit**

```bash
git add src/fedcampaign_emhi/experiments/campaigns.py
git commit -m "$(cat <<'EOF'
Replace SupportState verdicts with booleans in estimator feasibility/signed theorem/finite horizon statistics

EOF
)"
```

---

### Task 9: `experiments/campaigns.py` — producer sites (part 3: seed-level ODI Holm inputs, not-tested primary statistic, paired confirmatory contrast, common-mode)

**Files:**
- Modify: `src/fedcampaign_emhi/experiments/campaigns.py:2707-2737`, `:2799-2802`, `:2849`, `:3000-3001`, `:3067-3071`, `:3551-3555`

- [ ] **Step 1: seed-level strict-ODI-rate loop — lines 2707-2711 (the `decision` local variable)**

Old:
```python
        decision = (
            SupportState.SUPPORTED
            if adjusted[index] < loaded.values.statistics.nominal_significance_alpha
            else SupportState.NULL_RESULT
        )
```

New:
```python
        meets_threshold = adjusted[index] < loaded.values.statistics.nominal_significance_alpha
```

- [ ] **Step 2: same loop — payload dict key (was `"decision": decision.value,`) and `StatisticalRecord(...)` construction (was `decision=decision,`)**

Old:
```python
            "decision": decision.value,
```

New:
```python
            "meets_threshold": meets_threshold,
```

Old:
```python
            decision=decision,
```

New:
```python
            meets_threshold=meets_threshold,
```

- [ ] **Step 3: `_materialize_not_tested_primary_holm_statistic` — lines 2799-2802 (the guard condition)**

Old:
```python
    if (
        prepared.selection_support_state is not SupportState.NOT_TESTED
        or prepared.selected_client_ids
    ):
        return None
```

New:
```python
    if prepared.has_sufficient_clients or prepared.selected_client_ids:
        return None
```

- [ ] **Step 4: same function — `StatisticalRecord(...)` construction, line 2849**

Old:
```python
        decision=SupportState.NOT_TESTED,
```

New:
```python
        meets_threshold=False,
```

- [ ] **Step 5: `_materialize_paired_confirmatory_odi_contrast` — the "not complete" branch, line 3001**

Old:
```python
            decision=SupportState.NOT_TESTED,
```

New:
```python
            meets_threshold=False,
```

- [ ] **Step 6: same function — the main-path `decision=(...)` block, lines 3067-3071**

Old:
```python
        decision=(
            SupportState.SUPPORTED
            if raw_p_value < loaded.values.statistics.nominal_significance_alpha
            else SupportState.NULL_RESULT
        ),
```

New:
```python
        meets_threshold=raw_p_value < loaded.values.statistics.nominal_significance_alpha,
```

- [ ] **Step 7: `materialize_benign_common_mode_statistic` — lines 3551-3555 (same shape as Step 6, different function)**

Old:
```python
        decision=(
            SupportState.SUPPORTED
            if raw_p_value < loaded.values.statistics.nominal_significance_alpha
            else SupportState.NULL_RESULT
        ),
```

New:
```python
        meets_threshold=raw_p_value < loaded.values.statistics.nominal_significance_alpha,
```

- [ ] **Step 8: Verify no `SupportState` references remain in these functions**

```bash
grep -n "SupportState" src/fedcampaign_emhi/experiments/campaigns.py
```
Expected: no output (Task 10 removes the remaining full-method-support block, which also references it — if this grep still shows hits after this task, they belong to Task 10 and are expected until that task completes).

- [ ] **Step 9: Commit**

```bash
git add src/fedcampaign_emhi/experiments/campaigns.py
git commit -m "$(cat <<'EOF'
Replace SupportState verdicts with booleans in ODI/common-mode statistics

EOF
)"
```

---

### Task 10: `experiments/campaigns.py` — delete the full-method-support materialization

**Files:**
- Modify: `src/fedcampaign_emhi/experiments/campaigns.py:3137-3330` (approximate; verify exact line numbers before editing since Tasks 7-9 shift line numbers upward)

- [ ] **Step 1: Locate the current line range**

```bash
grep -n "_materialize_full_method_support\|_assert_full_method_criteria\|FullMethodSupportRecord\|FullMethodSupportInputs\|FullMethodSupportResult\|evaluate_full_method_support" src/fedcampaign_emhi/experiments/campaigns.py
```

- [ ] **Step 2: Delete `_materialize_full_method_support` and `_assert_full_method_criteria` in full**

Delete both function definitions entirely — from `def _materialize_full_method_support(` through the end of `_assert_full_method_criteria`'s body (the `raise ValueError(...)` loop and its closing), including the blank lines that separate the two functions from each other and from `_materialize_confirmatory_odi_inferences` below.

- [ ] **Step 3: Remove the call site inside `_materialize_confirmatory_odi_inferences`**

Old:
```python
    if experiment_name is ExperimentName.PRIMARY_STRICT_ODI_EVALUATION and not primary_not_tested:
        contrast = _materialize_paired_confirmatory_odi_contrast(
            loaded,
            repository,
            experiment_name,
            PrimaryHolmHypothesis.PRIMARY_ODI_ADVANTAGE_OVER_ORDER_AT_MOST_TWO_EMHI.value,
            MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI,
            "paired_strict_odi_rate_advantage",
        )
        _materialize_full_method_support(loaded, repository, contrast)
        return
```

New:
```python
    if experiment_name is ExperimentName.PRIMARY_STRICT_ODI_EVALUATION and not primary_not_tested:
        _materialize_paired_confirmatory_odi_contrast(
            loaded,
            repository,
            experiment_name,
            PrimaryHolmHypothesis.PRIMARY_ODI_ADVANTAGE_OVER_ORDER_AT_MOST_TWO_EMHI.value,
            MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI,
            "paired_strict_odi_rate_advantage",
        )
        return
```

(The `contrast` variable is no longer needed since its only consumer was the deleted call — dropping the assignment.)

- [ ] **Step 4: Remove now-unused imports**

Check whether `FullMethodSupportRecord`, `FullMethodSupportInputs`, `FullMethodSupportResult`, `evaluate_full_method_support`, `strict_odi_rate_criterion`, `paired_odi_advantage_criterion`, `median_operational_lead_criterion`, `matched_operating_point_requirement`, `median_of` are still imported at the top of `campaigns.py`:

```bash
grep -n "^from fedcampaign_emhi.experiments.registry import\|^from fedcampaign_emhi.artifacts.records import" src/fedcampaign_emhi/experiments/campaigns.py
```

Remove any of the deleted symbol names from those import blocks.

- [ ] **Step 5: Verify no leftover references anywhere in the file**

```bash
grep -n "SupportState\|FullMethodSupport\|evaluate_full_method_support\|strict_odi_rate_criterion\|paired_odi_advantage_criterion\|median_operational_lead_criterion\|matched_operating_point_requirement\|median_of(" src/fedcampaign_emhi/experiments/campaigns.py
```
Expected: no output.

- [ ] **Step 6: Confirm nothing else reads `full-method-support.json`**

```bash
grep -rn "full-method-support" src/ tests/
```
If any consumer is found outside this deleted function, stop and surface it — do not delete silently (per spec Section 4 verification note).

- [ ] **Step 7: Commit**

```bash
git add src/fedcampaign_emhi/experiments/campaigns.py
git commit -m "$(cat <<'EOF'
Delete full-method-support adjudication materialization from campaigns

EOF
)"
```

---

### Task 11: `evaluation/scalability.py`

**Files:**
- Modify: `src/fedcampaign_emhi/evaluation/scalability.py`

- [ ] **Step 1: Remove `SupportState` from the enum import, find and update the import line near the top of the file**

```bash
grep -n "SupportState" src/fedcampaign_emhi/evaluation/scalability.py
```
Delete `SupportState` from whichever `from fedcampaign_emhi.domain.enums import (...)` block it appears in.

- [ ] **Step 2: `ScalabilitySummary` dataclass fields**

Old:
```python
    numerical_failure_rate: Probability
    latency_criterion_state: SupportState
    numerical_criterion_state: SupportState
    local_timing_operating_point_available: Boolean
```

New:
```python
    numerical_failure_rate: Probability
    latency_within_target: Boolean
    numerical_failure_rate_within_bound: Boolean
    local_timing_operating_point_available: Boolean
```

- [ ] **Step 3: The `summarize_scalability` construction**

Old:
```python
        numerical_failure_rate=failure_rate,
        latency_criterion_state=SupportState.SUPPORTED
        if latency_passed
        else SupportState.NOT_SUPPORTED,
        numerical_criterion_state=SupportState.SUPPORTED
        if failure_passed
        else SupportState.NOT_SUPPORTED,
```

New:
```python
        numerical_failure_rate=failure_rate,
        latency_within_target=latency_passed,
        numerical_failure_rate_within_bound=failure_passed,
```

- [ ] **Step 4: The unrelated `DatasetSplitRecord(..., support_state=SupportState.SUPPORTED, ...)` construction elsewhere in this file**

```bash
grep -n "support_state=SupportState.SUPPORTED" src/fedcampaign_emhi/evaluation/scalability.py
```

Old:
```python
        support_state=SupportState.SUPPORTED,
```

New:
```python
        has_sufficient_clients=True,
```

- [ ] **Step 5: Commit**

```bash
git add src/fedcampaign_emhi/evaluation/scalability.py
git commit -m "$(cat <<'EOF'
Replace SupportState fields with booleans in scalability evaluation

EOF
)"
```

---

### Task 12: `experiments/synthetic.py`, `experiments/calibration.py`

**Files:**
- Modify: `src/fedcampaign_emhi/experiments/synthetic.py:36`, `:621`
- Modify: `src/fedcampaign_emhi/experiments/calibration.py:31`, `:210`, `:522`

- [ ] **Step 1: `synthetic.py` — remove `SupportState` from its enum import (line 36) and update the `DatasetSplitRecord`/similar construction at line 621**

```bash
grep -n "SupportState" src/fedcampaign_emhi/experiments/synthetic.py
```

Old:
```python
        support_state=SupportState.SUPPORTED,
```

New:
```python
        has_sufficient_clients=True,
```

- [ ] **Step 2: `calibration.py` — remove `SupportState` from its enum import (line 31) and update both constructions (lines 210, 522)**

```bash
grep -n "SupportState" src/fedcampaign_emhi/experiments/calibration.py
```

Old (both occurrences, identical text):
```python
        support_state=SupportState.SUPPORTED,
```

New (both occurrences):
```python
        has_sufficient_clients=True,
```

- [ ] **Step 3: Commit**

```bash
git add src/fedcampaign_emhi/experiments/synthetic.py src/fedcampaign_emhi/experiments/calibration.py
git commit -m "$(cat <<'EOF'
Replace SupportState with has_sufficient_clients in synthetic/calibration experiments

EOF
)"
```

---

### Task 13: `datasets/ton_iot_network/validation.py`, `datasets/edge_iiotset/validation.py`

**Files:**
- Modify: `src/fedcampaign_emhi/datasets/ton_iot_network/validation.py:5`, `:65`, `:71`
- Modify: `src/fedcampaign_emhi/datasets/edge_iiotset/validation.py:7`, `:140`, `:147`, `:153`

- [ ] **Step 1: `ton_iot_network/validation.py`**

Old (line 5):
```python
from fedcampaign_emhi.domain.enums import SupportState
```

Delete this line entirely (no other enum needed from this import in this file — confirm with `grep -n "SupportState" src/fedcampaign_emhi/datasets/ton_iot_network/validation.py` that nothing else from that import statement is used; if the line imports more than just `SupportState` adjust accordingly by re-reading the file before deleting).

Old (line 65):
```python
            support_state=SupportState.NOT_TESTED,
```
New:
```python
            has_sufficient_clients=False,
```

Old (line 71):
```python
        support_state=SupportState.SUPPORTED,
```
New:
```python
        has_sufficient_clients=True,
```

- [ ] **Step 2: `edge_iiotset/validation.py`**

Old (line 7):
```python
from fedcampaign_emhi.domain.enums import GroundTruthClass, SupportState
```
New:
```python
from fedcampaign_emhi.domain.enums import GroundTruthClass
```

Old (line 140):
```python
            support_state=SupportState.NOT_TESTED,
```
New:
```python
            has_sufficient_clients=False,
```

Old (line 147):
```python
            support_state=SupportState.SUPPORTED,
```
New:
```python
            has_sufficient_clients=True,
```

Old (line 153):
```python
        support_state=SupportState.SUPPORTED,
```
New:
```python
        has_sufficient_clients=True,
```

- [ ] **Step 3: Commit**

```bash
git add src/fedcampaign_emhi/datasets/ton_iot_network/validation.py src/fedcampaign_emhi/datasets/edge_iiotset/validation.py
git commit -m "$(cat <<'EOF'
Replace SupportState with has_sufficient_clients in dataset validation

EOF
)"
```

---

### Task 14: `execution/preprocessing.py`

**Files:**
- Modify: `src/fedcampaign_emhi/execution/preprocessing.py:89`, `:621`, `:778`, `:830`, `:975`, `:993`

- [ ] **Step 1: Remove `SupportState` from the enum import (line 89) — read the surrounding import block first to confirm exact removal**

```bash
sed -n '80,95p' src/fedcampaign_emhi/execution/preprocessing.py
```
Remove the `SupportState,` line from that block.

- [ ] **Step 2: Line 621 — the early-return call**

Old:
```python
        return _prepare_ton_epochs(loaded, (), (), (), SupportState.NOT_TESTED, 0, 0, 0)
```
New:
```python
        return _prepare_ton_epochs(loaded, (), (), (), False, 0, 0, 0)
```

- [ ] **Step 3: Lines 778 and 830 — function parameter type annotations**

Both occurrences:
Old:
```python
    support_state: SupportState,
```
New:
```python
    has_sufficient_clients: Boolean,
```

Read the surrounding function bodies (`sed -n '760,800p;815,850p' src/fedcampaign_emhi/execution/preprocessing.py`) to also rename every in-body reference to the old parameter name `support_state` to `has_sufficient_clients` within those two functions, and update the call sites that pass this parameter positionally or by keyword.

- [ ] **Step 4: Line 975 — local variable assignment**

Old:
```python
        support_state = SupportState.NOT_TESTED
```
New:
```python
        has_sufficient_clients = False
```

Check the lines immediately following (up to line 993) for further use of this local variable under its old name and rename those references too.

- [ ] **Step 5: Line 993 — record construction**

Old:
```python
        support_state=SupportState.NOT_TESTED,
```
New:
```python
        has_sufficient_clients=False,
```

(If this line is actually meant to forward the local variable computed in Step 4 rather than a hardcoded `False`, use `has_sufficient_clients=has_sufficient_clients,` instead — re-read lines 960-995 together before editing to confirm which is correct; do not silently change behavior from "forward computed value" to "always False" or vice versa.)

- [ ] **Step 6: Verify**

```bash
grep -n "SupportState\|support_state" src/fedcampaign_emhi/execution/preprocessing.py
```
Expected: no output.

- [ ] **Step 7: Commit**

```bash
git add src/fedcampaign_emhi/execution/preprocessing.py
git commit -m "$(cat <<'EOF'
Replace SupportState with has_sufficient_clients in preprocessing

EOF
)"
```

---

### Task 15: `emhi/calibration.py`, `evaluation/sequential.py` — `FitStatus`

**Files:**
- Modify: `src/fedcampaign_emhi/emhi/calibration.py:19`, `:375`, `:428`, `:434`, `:616`, `:763`, `:788`, `:804`, `:855`, `:861`, `:915-917`
- Modify: `src/fedcampaign_emhi/evaluation/sequential.py:29`, `:488`, `:573`, `:618`

- [ ] **Step 1: `emhi/calibration.py` — update the enum import**

Old (line 19, inside a larger import block):
```python
    SupportState,
```
New:
```python
    FitStatus,
```
(Keep it in the same alphabetically-sorted position the import-sort tool would place `FitStatus` — run `ruff check --fix src/fedcampaign_emhi/emhi/calibration.py` after this edit to let it re-sort if needed.)

- [ ] **Step 2: Replace every value/comparison in this file**

Run:
```bash
grep -n "SupportState" src/fedcampaign_emhi/emhi/calibration.py
```

For each of the 10 remaining occurrences (lines 375, 428, 434, 616, 763, 788, 804, 855, 861, 915-917), apply:
- `SupportState.SUPPORTED` → `FitStatus.FITTED`
- `SupportState.NOT_TESTED` → `FitStatus.INSUFFICIENT_DATA`

These are direct 1:1 token substitutions (`state=SupportState.SUPPORTED,` → `state=FitStatus.FITTED,`; `if order_context.state is not SupportState.SUPPORTED:` → `if order_context.state is not FitStatus.FITTED:`; the ternary at 915-917 substitutes both branches). No structural changes to any surrounding logic.

- [ ] **Step 3: `evaluation/sequential.py` — update the enum import (line 29) and the three comparison sites**

```bash
grep -n "SupportState" src/fedcampaign_emhi/evaluation/sequential.py
```

- Line 29 import: `SupportState,` → `FitStatus,`
- Line 488: `and context.state is SupportState.SUPPORTED` → `and context.state is FitStatus.FITTED`
- Line 573: `if cell.context_cell == context_cell and cell.state is SupportState.SUPPORTED` → `if cell.context_cell == context_cell and cell.state is FitStatus.FITTED`
- Line 618: `if coalition_fit.state is not SupportState.SUPPORTED:` → `if coalition_fit.state is not FitStatus.FITTED:`

- [ ] **Step 4: Verify**

```bash
grep -rn "SupportState" src/fedcampaign_emhi/emhi/calibration.py src/fedcampaign_emhi/evaluation/sequential.py
```
Expected: no output.

- [ ] **Step 5: Commit**

```bash
git add src/fedcampaign_emhi/emhi/calibration.py src/fedcampaign_emhi/evaluation/sequential.py
git commit -m "$(cat <<'EOF'
Replace SupportState with FitStatus in EMHI calibration fit-sufficiency gate

EOF
)"
```

---

### Task 16: `tests/architecture/test_forbidden_vocabulary.py` — close the gap

**Files:**
- Modify: `tests/architecture/test_forbidden_vocabulary.py`

- [ ] **Step 1: Read the current forbidden-fragment mechanism**

```bash
sed -n '1,80p' tests/architecture/test_forbidden_vocabulary.py
```

Identify how `FORBIDDEN_CLAIM_FRAGMENTS` (or equivalent tuple) is consumed by the test function(s) so the new entries plug into the same mechanism rather than requiring a new test function.

- [ ] **Step 2: Add the new forbidden fragments**

Add to the existing forbidden-fragment tuple (name may differ slightly from `FORBIDDEN_CLAIM_FRAGMENTS`; use whatever the Step 1 read reveals):
```python
    "SupportState",
    "FullMethodSupport",
    "evaluate_full_method_support",
    "criterion_satisfied",
    "all_criteria_pass",
```

Do not add a bare `support_state` fragment — `has_sufficient_clients` and other renamed fields must remain legal, and a substring match on `support_state` would not collide with them, but confirm this by checking the matching function's logic (exact identifier match vs. substring) before adding to avoid a false positive against legitimate names.

- [ ] **Step 3: Write a regression test proving the new patterns actually fire**

Add a test that constructs a small in-memory AST or temp file (matching whatever mechanism the existing test uses — check `tests/architecture/ast_scans.py` for helpers) containing an identifier `SupportState` and asserts the forbidden-vocabulary check flags it. Follow the existing test file's pattern for how prior forbidden-term tests are structured (look for an existing test like `test_forbidden_claim_fragments_are_rejected` or similar to model this on).

- [ ] **Step 4: Run the architecture test suite**

```bash
pytest tests/architecture/test_forbidden_vocabulary.py -v
```
Expected: all PASS, including the new regression test.

- [ ] **Step 5: Commit**

```bash
git add tests/architecture/test_forbidden_vocabulary.py
git commit -m "$(cat <<'EOF'
Forbid SupportState/FullMethodSupport vocabulary from returning to production

EOF
)"
```

---

### Task 17: Fix every remaining test file, then run full verification

**Files:**
- Modify (as needed, guided by the terminology mapping table at the top of this plan): every file under `tests/` that references `SupportState`, `support_state`, `selection_support_state`, `decision=`/`.decision`, `FullMethodSupport*`, `evaluate_full_method_support`, `strict_odi_rate_criterion`, `paired_odi_advantage_criterion`, `median_operational_lead_criterion`, `matched_operating_point_requirement`, `median_of`, `latency_criterion_state`, `numerical_criterion_state`, `criterion_satisfied`, `all_criteria_pass`.

- [ ] **Step 1: Find every remaining production+test reference**

```bash
grep -rln "SupportState\|selection_support_state\|support_state\|FullMethodSupport\|evaluate_full_method_support\|strict_odi_rate_criterion\|paired_odi_advantage_criterion\|median_operational_lead_criterion\|matched_operating_point_requirement\|latency_criterion_state\|numerical_criterion_state\|criterion_satisfied\|all_criteria_pass" src/ tests/ docs/Roadmap.md
```

Confirm zero hits under `src/` (Tasks 1-16 should have already achieved this — if any remain, fix them using the terminology mapping table before proceeding). For each hit under `tests/`, open the file and apply the terminology mapping table.

- [ ] **Step 2: Delete `tests/unit/experiments/test_registry.py` tests that exclusively covered the deleted construct**

This file currently has 3 tests: `test_registry_contains_roadmap_experiments` (keep — tests `experiment_registry`, which still exists), `test_evaluate_full_method_support_passes_when_every_criterion_holds` (delete), `test_evaluate_full_method_support_fails_when_heldout_pfa_exceeds_target` (delete), `test_matched_operating_point_requirement_requires_both_methods` (delete). Remove the `FullMethodSupportInputs`, `evaluate_full_method_support`, `matched_operating_point_requirement`, `median_of` names from the file's import block, leaving only `experiment_registry`.

- [ ] **Step 3: Work through the remaining 17 test files identified in the spec**

For each of: `tests/scientific/test_sequential_routes_contracts.py`, `tests/unit/execution/test_composition_calibration.py`, `tests/unit/execution/test_signed_theorem_statistics.py`, `tests/unit/execution/test_estimator_feasibility_statistics.py`, `tests/unit/emhi/test_basis_projection_crossfit.py`, `tests/unit/analysis/test_project.py`, `tests/unit/analysis/test_multiplicity.py`, `tests/unit/evaluation/test_scalability.py`, `tests/unit/config/test_scientific_configuration.py`, `tests/unit/synthetic/test_pure_order_separation.py`, `tests/unit/synthetic/test_context_boundaries.py`, `tests/unit/comparators/test_composition_challenge.py`, `tests/unit/comparators/test_contracts.py`, `tests/unit/comparators/test_composition_selection.py`, `tests/unit/datasets/edge_iiotset/test_edge_iiotset_contract.py`, `tests/unit/models/test_autoencoder_shape.py`, `tests/integration/preprocessing/test_edge_iiotset_pipeline.py`:

1. Run `grep -n "SupportState\|support_state\|decision\|criterion_satisfied\|all_criteria_pass\|latency_criterion_state\|numerical_criterion_state" <file>` to see exactly what needs changing in that file.
2. Apply the terminology mapping table from the top of this plan — field names rename 1:1, enum-value ternaries collapse into the equivalent boolean expression exactly as demonstrated in Tasks 7-15.
3. Run `pytest <file> -v` and confirm it passes (or fails only for reasons unrelated to this rename — investigate and fix any such failure too, per this project's "no known failure left behind" rule).
4. Commit that file's changes individually: `git add <file> && git commit -m "Update <short description> for SupportState removal"` (with the standard `Co-Authored-By` trailer).

- [ ] **Step 4: Update `docs/Roadmap.md`**

```bash
grep -n "SupportState\|support_state\|FullMethodSupport\|criterion_satisfied\|all_criteria_pass\|SUPPORTED\|NOT_SUPPORTED\|NULL_RESULT\|MECHANISM_ONLY\|PARTIALLY_SUPPORTED" docs/Roadmap.md
```

For every match describing this as *runtime/implementation output* (as opposed to prose already describing the *prohibition*, which stays), rewrite the sentence to describe the same measurement as a persisted metric plus a boolean threshold comparison, per spec Section 5. Do not touch the numeric thresholds, criteria definitions, or hypothesis statements themselves — only the description of what gets returned/persisted.

Commit:
```bash
git add docs/Roadmap.md
git commit -m "$(cat <<'EOF'
Align Roadmap.md wording with boolean threshold outputs, no claim verdicts

EOF
)"
```

- [ ] **Step 5: Full static analysis and test suite**

Run each of the following and fix any failure before proceeding to the next (per this project's mandatory-gate policy, fix pre-existing failures too if encountered):

```bash
ruff check .
```
```bash
pyright
```
```bash
semgrep --config auto src/ 2>&1 | tail -100
```
```bash
python -m tests.architecture.import_linter_check 2>/dev/null || lint-imports
```
(Use whichever import-linter invocation this repo's `pyproject.toml`/CI config actually specifies — check `grep -n "importlinter\|import-linter\|lint-imports" pyproject.toml Makefile 2>/dev/null` if unsure.)
```bash
vulture src/
```
```bash
deptry .
```
```bash
pytest
```

- [ ] **Step 6: Final grep sweep**

```bash
grep -rn "SupportState\|FullMethodSupport\|evaluate_full_method_support\|criterion_satisfied\|all_criteria_pass" src/
```
Expected: no output. This is the spec's completion criterion for Phase 1.

- [ ] **Step 7: Final commit if Step 5 required any additional fixes**

```bash
git add -A
git commit -m "$(cat <<'EOF'
Fix remaining quality-gate failures after claim-adjudication removal

EOF
)"
```

(Skip this step if Step 5 required no changes beyond what was already committed.)

---

## Post-plan note

This completes Phase 1 of the larger FedCampaign-EMHI cleanup (see the 18-point scope discussed at the start of this project). Phase 2 (splitting `experiments/campaigns.py` as a god module) should start from a fresh brainstorming/spec cycle once this phase is merged, since `campaigns.py` line numbers referenced anywhere will have shifted.
