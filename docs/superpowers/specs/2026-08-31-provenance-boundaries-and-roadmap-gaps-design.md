# Provenance boundary partitioning and adjacent roadmap gaps

Date: 2026-08-31

## Background

`docs/RoadmapAuditMatrix.md` row 17 (lineage audit, 2026-08-31) found that `configuration_digest()` (`config/loading.py:59`) hashes the entire 24-field `ScientificConfig` into one `material_digest`, which `material_fingerprint()` (`artifacts/provenance.py:15`) embeds into every artifact's `dependency_fingerprint`. This makes any config change anywhere invalidate every artifact, violating Roadmap Section 17.5 ("Invalidation follows dependency edges, not repository-wide provenance equality"). Current behavior is conservative-safe (over-invalidates, never silently reuses stale evidence) but not compliant.

Three investigation passes (config-field-to-boundary mapping, `experiments.*` sub-config trace, `runtime.*` field wiring check) surfaced the full scope, confirmed against Roadmap.md source text. All fields below were checked against roadmap prose before being classified — none are being deleted as "unused" without that check.

## Scope

### A. Provenance digest partitioning (the original ask)

Roadmap Section 17.5 defines 12 artifact boundaries. Add a 13th, **plan**, for sweep/grid-definition fields that gate which cells run rather than what a cell computes (`support_grids.*`, `robustness.*`) — approved by user rather than forcing them into B3.

Per-boundary scoped digest helpers replace the single `loaded.material_digest` argument at each `material_fingerprint(...)` call site. Two call-site classes:

- **Already correct** (5 sites, all in `execution/preprocess.py`): narrow `payload_digest({...})` per boundary. Pattern to replicate everywhere else.
- **Violating** (~20 sites across `execution/runner.py`, `analysis/project.py`, `reporting/evidence.py`, `comparators/composition.py`): pass `loaded.material_digest` (whole config) as the first argument. Each needs its boundary identified (done, see investigation results) and a scoped digest substituted. Several also need their existing `method_digest`/similar upstream payload *widened* to capture fields it's currently missing (e.g. `_evaluate_emhi_seed_cell` and `_evaluate_comparator_seed_cell` never capture `evidence.calibrated_finite_horizon`/`local_policy.*` even narrowly — they rely entirely on the whole-config digest today).

Fields confirmed excluded from every boundary: `artifacts.outputs_root`/`results_root` (path-only, roadmap 17.3 explicit exclusion), `reporting.*` (excluded everywhere except included in the B10 export boundary itself, per roadmap 17.5's export row).

Fields confirmed shared across boundaries needing per-boundary sub-hashing (not exclusion): `randomness.*` (per-seed, not whole block — pattern already used at `runner.py:1436`), `evidence.*` (B6-adjacent scoring, B7 calibration, B9 statistics all consume different sub-fields), `context.rank_clip_epsilon` (B5) vs rest of `context.*` (B6), `study.maximum_coalition_order` (cross-cutting, include per-boundary wherever consumed).

`experiments.*` sub-config trace (all 12, complete): 3 previously traced (composition→B10, primary_odi.methods→B11, sequential_evidence.signed_theorem→B9); remaining 9 now traced — mostly plan-gating `methods` fields feeding the same 4 real-data fingerprint sites (`runner.py:1562,1827,1977,2509`), plus `self_explanation_exclusion_validation.context_methods`→B6, `pure_order_separation_validation.primary_client_count`→B4/B5 (used far beyond its own experiment — 9 other files), `exclusion_matched_hofd_equivalence.{context_cell_count,primary_support_levels}`→B6, `estimator_support_and_context_feasibility.sensitivity.*`→B6.

B12 (timing/scalability) has no implementation yet — no artifact type, no fingerprint call site (confirmed against Roadmap 19.3, which defines a runtime-detected environment record, not a config sub-digest). Out of scope until the artifact exists; not a mapping gap.

### B. Fields verified as genuinely required by roadmap text, not dead — confirmed by grep against `docs/Roadmap.md`

All of these looked unwired during the trace but are **roadmap-mandated and must be wired, not removed**:

- `runtime.automatic_technical_retries_after_initial_failure`, `runtime.required_confirmatory_missing_cell_tolerance` — Roadmap.md:2087-2093. No retry loop exists anywhere in `execution/runner.py` or `execution/preprocess.py`; the `Failed` cell state (`domain/enums.py`) is never assigned — cells only ever become `COMPLETED` or `INVALID`. Missing-cell tolerance is hardcoded to strict all-or-nothing equality at 5 call sites (`runner.py:858,932,1094,1167,1233`) instead of reading the configured tolerance.
- `experiments.benign_common_mode_robustness.native_high_volume_window.{stride_epochs,top_event_count_fraction}` — Roadmap.md:3771-3777, the "Native high-volume stress windows" negative condition. Entirely unimplemented; only two of three negative conditions exist today (native non-overlapping horizons, synthetic-on-real count stress).
- `experiments.context_and_estimator_sensitivity.{forced_ridge,context_variants}` and the whole `context_and_estimator_sensitivity` experiment — Roadmap.md Section 13.11 (lines 3735-3753), full prose spec exists: development-only robustness experiment, one-factor sensitivity sweep (basis size, context cell count, forced ridge, shuffled outside context, local-history-only context, forced no-abstention) against the Primary Strict ODI Evaluation base. `ExperimentName.CONTEXT_AND_ESTIMATOR_SENSITIVITY` exists in the enum and is explicitly exempted from the "real experiment needs methods" validation (`runner.py:240-241`), but has zero execution branch anywhere in `runner.py`.

One field remains genuinely dead after the roadmap check: `self_explanation_exclusion_validation.primary_condition.comparison` — no roadmap prose reference found (checked Section 13.2 self-explanation text), no code consumer. To be removed, with a final grep re-check immediately before deletion.

Two dead helper functions confirmed unreachable from any call graph, only ever calling each other: `enumerate_hofd_equivalence_plan`, `hofd_equivalence_support_levels` (`comparators/hofd_equivalence.py:65,86`) — their live replacement (`producers.py:97`) already does the equivalent work inline. To be removed.

## Out of scope for this pass

- Running any experiment (forbidden this session).
- B12 timing/scalability artifact implementation (no roadmap-required trigger for this pass; flagged for a future pass).
- `numerics.smoke_repeatability_tolerance` consumer confirmation (deferred — low risk, smoke-only).

## Work breakdown (execution order)

1. Digest partitioning: add per-boundary scoped-digest helpers (new module, e.g. `artifacts/boundaries.py`), replace whole-config digest at each violating call site, widen narrow-but-incomplete `method_digest` payloads where identified. Tests: reuse/staleness behavior per boundary (change a B9-only field, assert B4/B5/B6 artifacts keep their fingerprint; change a B4 field, assert downstream B6/B7 propagate staleness).
2. Runtime retry loop: wire `automatic_technical_retries_after_initial_failure` into the per-cell execution try/except in `_execute_synthetic_experiment` (`runner.py:477-665`) and add the missing real-data equivalent around `_execute_real_emhi_methods` (`runner.py:2634-2710`), distinguishing technical failure (retry, eventual `Failed`) from scientific/provenance violation (`Invalid`, no retry) per Roadmap 17.6. Tests: retry exhaustion reaches `Failed`; scientific violation does not retry.
3. Missing-cell tolerance: replace the 5 strict-equality confirmatory checks (`runner.py:858,932,1094,1167,1233`) with a count-against-tolerance comparison; add the missing real-data-path equivalent gate. Tests: synthesis proceeds when missing count ≤ tolerance, still blocks above it.
4. Benign common-mode robustness: implement "Native high-volume stress windows" negative condition per Roadmap.md:3771-3777. Tests: rolling window construction, ranking, percentile-tie retention, exclusion from PFA inference.
5. Context and Estimator Sensitivity (13.11): new experiment producer implementing the one-factor sweep against the primary base. Largest single item — new execution path, new record type(s), CLI/report wiring, tests per sensitivity factor.
6. Remove the two confirmed-dead items (`primary_condition.comparison` field, two dead HOFD helper functions) with a final grep re-check first.
7. Update `docs/RoadmapAuditMatrix.md` repair log after each landed piece; full quality gate (`make quality`, `pytest`) after each commit.

Each numbered item lands as its own commit per CLAUDE.md Section 13.
