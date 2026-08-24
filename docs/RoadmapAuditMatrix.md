# Roadmap audit matrix

This matrix is the implementation audit record for `docs/Roadmap.md`. A row is
Supported only when its configured inputs, execution path, persisted evidence,
and tests have been inspected. `In progress` and `Unverified` are not evidence
of scientific completion.

| Roadmap area | Required implementation evidence | Audit status | Evidence or finding |
| --- | --- | --- | --- |
| 4.1–4.8 EMHI core | Detector scores, ranks, context, residual ranks, bounded basis, atoms, calibration, aggregation | In progress | Implementations exist under `src/fedcampaign_emhi/emhi`; real-data execution must be traced end-to-end. |
| 5 detector protocol | Dataset-specific detector fit and score artifacts | In progress | Implementations exist under `detectors`; audit must verify partitions and held-out wiring. |
| 6 raw datasets | Only paths under `data/raw`, released files, provenance inventory | Supported | Canonical TON-IoT and Edge-IIoTSet paths are configured and preprocessing inventories are produced. |
| 7.1 duplicates | Complete retained-record representation and counts | In progress | DuckDB aggregation is executable; duplicate identity must be checked against complete-payload requirement. |
| 7.2 invalid records | Deterministic exclusion reasons and discrepancy manifest | In progress | Counts are persisted; reason-level records need audit. |
| 7.3–7.5 epoch features, scaling, selection | Configured features, training-only scaling, deterministic client selection | In progress | Primary preprocessing executes; selection eligibility remains insufficient for the current release. |
| 8 contexts | Exact, inclusive, leave-one-out, partial, oracle, and diagnostic definitions | In progress | Shared context-member functions are wired; each consumer needs contract coverage. |
| 9 local detectors | IF, robust PCA, autoencoder, calibration and rank conversion | In progress | Source present; not yet execution-audited. |
| 10 methods/comparators | All declared EMHI and comparator methods with lawful contexts | In progress | Method contracts exist; generic synthetic producer previously bypassed method-specific evaluation. |
| 11 metrics | PFA, ODI, stopping, derivatives, attenuation, drift, coverage, runtime | In progress | Derivative/attenuation now persisted for self-explanation; comparator ODI path still contains placeholders. |
| 12 fixtures | Exact deterministic fixture outcomes and tolerances | In progress | Fixture modules/tests exist; full fixture evidence audit pending. |
| 13.1 synthetic module validation | Every exact fixture and invariant | In progress | Current validation run record is only a diagnostic; required fixture-output audit pending. |
| 13.2 self-explanation | Complete grid per seed, paired trajectories, OLS derivatives, material gates, and primary Holm decision | In progress | `evaluate_self_explanation_seed` materializes 1,260 conditions per seed and runner persists them. Confirmatory multiplicity synthesis remains open. |
| 13.3 pure-order separation | Every generator/effect/order/method cell, subset and target drift | Unverified | Generic producer only samples one setting; requires replacement. |
| 13.4 HOFD equivalence | Configured support grid, paired CIs, cosine and stopping differences | Unverified | Generic producer does not execute the contract. |
| 13.5 comparator composition | Candidate error, PFA, runtime and tie-break artifact | Unverified | Runner currently selects from a one-seed proxy score and zero runtimes. |
| 13.6 estimator feasibility | Support/context grid and feasibility criteria | Unverified | Generic producer does not execute the contract. |
| 13.7 sequential evidence | Finite horizon calibration and held-out validity | Unverified | Generic producer does not execute the contract. |
| 13.8–13.17 real and robustness experiments | Each declared method/seed/dataset/condition and all outcomes | In progress | Real EMHI path exists; comparator evaluator has placeholder ODI and local-stop values. |
| 14 statistics | Exact sign-flip, BCa, fixed Holm families, Not Tested handling | In progress | Statistics path exists but must be checked against all fixed families and metrics. |
| 15 claims | Registry maps only evidence-backed conditions to supported claims | In progress | Claim materialization requires re-audit after producer repairs. |
| 16 CLI | Plan, doctor, preprocess, run, status, report and resume semantics | In progress | Commands execute; status/report must reject incomplete scientific evidence. |
| 17 lifecycle | Fingerprints, stale descendants, immutable published artifacts | In progress | Source fingerprinting and stale checks exist; lineage audit pending. |
| 18 evidence | Raw, derived, statistical, claims, manuscript inputs linked to cell records | In progress | Self-explanation cell now includes measurement evidence; broad evidence graph audit pending. |
| 19 completion gates | All requirements, no placeholders, full quality suite, real reruns | Unverified | No completion claim is permitted while any matrix row is open. |
| 20 reports | Evidence tables, explicit states, reproducible sources | In progress | Reports generate; content must be checked after all execution repairs. |
| 21 claims wording | No claim beyond tested scope or Not Tested state | In progress | Requires final claim-registry audit. |

## Repair log

| Date | Area | Change | Verification |
| --- | --- | --- | --- |
| 2026-08-24 | 13.2 | Replaced the self-explanation smoke check with paired common-mode trajectories, the complete configured grid, post-settling OLS derivatives, attenuation, material gates, and persisted measurement evidence. | Focused unit suite and one confirmatory-seed execution. |
