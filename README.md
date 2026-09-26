# FedCampaign-EMHI

FedCampaign-EMHI implements Exclusion-Matched Hierarchical Innovation for Operational Distributed Insufficiency. The scientific and execution contract is the repository copy of the roadmap at `docs/Roadmap.md`.

> **Scientific artifact status (2026-09-26):** Corrected TON and Edge preprocessing completed twice with idempotent reuse; engineering/static/architecture checks, fresh Graphify, and the production-path temporal-dependence diagnostic are recorded in the audit. The strong-comparator challenge completed 150/150 cells, and the corrected primary Strict ODI run completed with 200/200 valid cells (10 development and 10 confirmatory seeds). The previous unmatched-horizon primary outputs remain historical and stale. The corrected primary evaluation uses the current material digest and matched 60-epoch replay. It does **not** support the predeclared comparative ODI claim: Full FedCampaign-EMHI and its order-at-most-two comparator each had strict ODI rate 1.0 on all 10 confirmatory seeds; the paired advantage was 0 (raw p = 1; support criteria not met). This result is conditional on the fixed trace, selected source-IP cohort, split, campaign registry, seed variability, and zero-event representation; it is not population-level replication or an anytime-valid real-data e-process. Non-overlapping horizons are disjoint windows, not evidence of independent stop indicators. Empty epochs use the locked zero-event representation; the raw release has no independent capture-coverage signal to verify continuous monitoring. Edge remains `Not Tested` under its locked six-source minimum. See [current audit progress](docs/audit/Progress.md) and [the paired report](results/experiments/primary-strict-odi-evaluation/tables/main/seed-summary.csv).

## Environment

Python 3.13+ and `uv` are required.

```bash
uv sync --extra dev
uv run fedcampaign doctor
```

The production scientific configuration is `configs/fedcampaign-emhi.yaml`. `configs/tests.yml` and `configs/smoke.yml` are reduced non-production configurations and cannot replace the claim-bearing production configuration.

Raw datasets are immutable and must appear under the configured `data/raw` symlink.

## Public CLI

The only public executable is `fedcampaign`:

```bash
fedcampaign doctor
fedcampaign preprocess
fedcampaign preprocess <dataset-name>
fedcampaign preprocess --overwrite
fedcampaign preprocess <dataset-name> --overwrite
fedcampaign plan
fedcampaign analyze
fedcampaign smoke
fedcampaign smoke --overwrite
fedcampaign run <experiment-name>
fedcampaign run <experiment-name> --overwrite
fedcampaign status
fedcampaign status <experiment-name>
fedcampaign report
fedcampaign report <experiment-name>
fedcampaign report <experiment-name> --overwrite
```

The CLI exposes execution controls only. It does not accept seed, method, coalition-order, basis, context, threshold, PFA, statistical, sensitivity, run-id, or lifecycle-step overrides.

Normal `fedcampaign run <experiment-name>` invocations resume compatible completed work. Synthetic workers publish a durable checkpoint as soon as each cell finishes, so stopping the command and rerunning it without `--overwrite` preserves completed cells even when earlier-dispatched cells are still running. `--overwrite` intentionally bypasses reuse and starts the selected experiment again. Real-data execution also reuses its persisted score, rank, fit, and completed-cell artifacts.

## Campaign experiments

Each registered experiment is executed by name with a single command. Run `fedcampaign status` before starting one and verify `fedcampaign status <experiment-name>` afterwards; materialize results with `fedcampaign report <experiment-name>`. Names are identical for `run`, `status`, and `report`.

The list below is a historical run log, not a current validated campaign. For a future corrected run, start with `uv run fedcampaign preprocess --overwrite`, inspect `uv run fedcampaign status`, and follow the dependency-aware order below. Real-data runs require current preprocessing; `strong-comparator-composition-challenge` must complete before `primary-strict-odi-evaluation` and `secondary-controlled-trace-generalization`. The latter remains `Not Tested` under the present Edge-IIoTset minimum-source rule. `coalition-scalability` is an engineering reference-harness diagnostic and does not establish deployment readiness. The duration annotations are historical execution notes only.

```text
fedcampaign run synthetic-module-validation                   (Duration: ≈ 3–5 s — measured; current status: Completed, lifecycle valid, 1/1 cells)
fedcampaign run self-explanation-exclusion-validation         (Duration: 2 min 8 s — measured 2026-09-08; 60/60 cells completed, lifecycle validated, report exported)
fedcampaign run estimator-support-and-context-feasibility     (Duration: 15 min 22 s — measured 2026-09-08; 60/60 cells completed, checkpointed, and ready for lifecycle validation)
fedcampaign run sequential-evidence-validation                (Duration: deferred after 3 h 47 min plus a 1 min checkpoint/logging validation restart; 0/60 cells published before the controlled stops; completion-order checkpoints now preserve each finished cell)
fedcampaign run pure-order-separation-validation              (Duration: deferred after ≈ 10 min; 8/840 cells checkpointed; estimated ≈ 6–10 h total with 10 workers)
fedcampaign run exclusion-matched-hofd-equivalence            (Duration: 16 min 29 s — measured 2026-09-08; 120/120 cells completed, report export repaired)
fedcampaign run strong-comparator-composition-challenge       (Duration: ≈ 4 min 11 s)
fedcampaign run outside-campaign-contamination-boundary       (Duration: deferred after 5 h 36 min with 0/60 cells published; wave-based lower-bound estimate ≥ 44 h 48 min total — resume later; completion-order checkpoints now preserve each finished cell)
fedcampaign run client-dropout-and-context-sparsity-boundary  (Duration: ≈ 2 h 13–19 min)
fedcampaign run context-and-estimator-sensitivity             (Duration: ≈ 10 min 13 s)
fedcampaign run primary-strict-odi-evaluation                 (Duration: 5 min 57 s — measured 2026-09-08; 200/200 cells completed, report exported)
fedcampaign run exclusion-mechanism-ablation                  (Duration: 25 min 50 s — measured 2026-09-08; 80/80 cells completed, report exported)
fedcampaign run purification-and-order-ablation               (Duration: 9 min 55 s — measured 2026-09-08; 80/80 cells completed, lifecycle validation pending report export)
fedcampaign run strong-local-policy-challenge                 (Duration: ≈ 1 min 3 s)
fedcampaign run benign-common-mode-robustness                 (Duration: 39 min 17 s — measured 2026-09-08; 80/80 cells completed, report exported)
fedcampaign run secondary-controlled-trace-generalization     (Duration: ≈ 0.33 s compatible-artifact reuse — measured 2026-09-08; 120/120 cells already completed, report exported)
fedcampaign run coalition-scalability                         (Duration: not yet measured)
```

All listed experiments are registered names under the production configuration (`configs/fedcampaign-emhi.yaml`); `fedcampaign status` confirms which are registered.

### Measured run durations

Only experiments with a completed run have a measured duration. Values below were recorded from the campaign execution logs of 2026-09-07 and 2026-09-08 and must not be extrapolated to unmeasured experiments — their cell grids, worker profiles, and data scales differ.

| Experiment | Measured duration of completed run | Notes |
| --- | --- | --- |
| `synthetic-module-validation` | ≈ 3–5 s wall per canonical run (measured runs 2.6–5.3 s); single validation cell | Historical runs on 2026-09-07 were stale after a material-digest change. Current `fedcampaign status` (2026-09-25) reports the registered fixture `Completed`, lifecycle valid, 1/1 cells; `fedcampaign smoke` passes. |
| `client-dropout-and-context-sparsity-boundary` | ≈ 2 h 13–19 min; runner-recorded execute-stage `elapsed_seconds=8348.6` (≈ 2 h 19 min) with a logged start-to-completion span of ≈ 2 h 13 min | One of the currently valid completed runs (state `Completed`, 30/30 development cells). Ran 30 cells at 6 concurrent workers, ≈ 27 min per cell. Two earlier invocations were stopped memory-policy probes and produced no results. |
| `strong-comparator-composition-challenge` | ≈ 4 min 11 s (runner-recorded `elapsed_seconds=251.36`); 150 synthetic producer cells at 6 concurrent workers | Final fresh run 2026-09-08, state `Completed` (150/150 cells); selection: Conditional Log-Linear Reference. Earlier single-cell probe estimated ≈ 3 min; the recorded run is authoritative. |
| `strong-local-policy-challenge` | ≈ 1 min 3 s (runner-recorded `elapsed_seconds=63.09`); 20 real-data cells at 10 concurrent workers | Final fresh run 2026-09-08, state `Completed` (20/20 cells). Shared detector-score/rank/fit ancestors were reused, so this duration excludes those upstream fits. |
| `context-and-estimator-sensitivity` | ≈ 10 min 13 s (runner-recorded `elapsed_seconds=613.32`); 80 sensitivity condition cells at 10 concurrent workers | Final fresh run 2026-09-08, state `Completed` (80/80 cells). Runs seed-parallel; the earlier serial implementation was estimated at ≈ 55–60 min. |

No other experiment has completed a run, so no duration is measured for it yet. Each completed run records its canonical duration in the execution log as `stage_completed function=execute_experiment elapsed_seconds=...`; append that measured value to this table after the first completed run of any experiment rather than estimating it.

## Development

```bash
make format
make lint
make typecheck
make test
make quality
```
