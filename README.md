# FedCampaign-EMHI

FedCampaign-EMHI implements Exclusion-Matched Hierarchical Innovation for Operational Distributed Insufficiency. The scientific and execution contract is the repository copy of the roadmap at `docs/Roadmap.md`.

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

Run the experiments in the dependency-aware campaign order below. The real-data experiments require valid production preprocessing (`fedcampaign preprocess`, `fedcampaign status`), and `strong-comparator-composition-challenge` must complete before `primary-strict-odi-evaluation` and `secondary-controlled-trace-generalization`, whose configurations use the Selected Strong Comparator Composition record. `coalition-scalability` is a timing harness and runs last so its evidence is not distorted by campaign load. The `(Duration: ...)` annotation shows the measured wall time where a completed run exists; experiments without one read `not yet measured`.

```text
fedcampaign run synthetic-module-validation                   (Duration: ≈ 3–5 s — measured; currently stale, re-run pending)
fedcampaign run self-explanation-exclusion-validation         (Duration: 2 min 8 s — measured 2026-09-08; 60/60 cells completed, lifecycle validated, report exported)
fedcampaign run estimator-support-and-context-feasibility     (Duration: 15 min 22 s — measured 2026-09-08; 60/60 cells completed, checkpointed, and ready for lifecycle validation)
fedcampaign run sequential-evidence-validation                (Duration: deferred after 3 h 47 min plus a 1 min checkpoint/logging validation restart; 0/60 cells published before the controlled stops; completion-order checkpoints now preserve each finished cell)
fedcampaign run pure-order-separation-validation              (Duration: not yet measured)
fedcampaign run exclusion-matched-hofd-equivalence            (Duration: not yet measured)
fedcampaign run strong-comparator-composition-challenge       (Duration: ≈ 4 min 11 s)
fedcampaign run outside-campaign-contamination-boundary       (Duration: deferred after 5 h 36 min with 0/60 cells published; wave-based lower-bound estimate ≥ 44 h 48 min total — resume later; completion-order checkpoints now preserve each finished cell)
fedcampaign run client-dropout-and-context-sparsity-boundary  (Duration: ≈ 2 h 13–19 min)
fedcampaign run context-and-estimator-sensitivity             (Duration: ≈ 10 min 13 s)
fedcampaign run primary-strict-odi-evaluation                 (Duration: not yet measured)
fedcampaign run exclusion-mechanism-ablation                  (Duration: 25 min 50 s — measured 2026-09-08; 80/80 cells completed, report exported)
fedcampaign run purification-and-order-ablation               (Duration: 9 min 55 s — measured 2026-09-08; 80/80 cells completed, lifecycle validation pending report export)
fedcampaign run strong-local-policy-challenge                 (Duration: ≈ 1 min 3 s)
fedcampaign run benign-common-mode-robustness                 (Duration: 39 min 17 s — measured 2026-09-08; 80/80 cells completed, report exported)
fedcampaign run secondary-controlled-trace-generalization     (Duration: not yet measured)
fedcampaign run coalition-scalability                         (Duration: not yet measured)
```

All listed experiments are registered names under the production configuration (`configs/fedcampaign-emhi.yaml`); `fedcampaign status` confirms which are registered.

### Measured run durations

Only experiments with a completed run have a measured duration. Values below were recorded from the campaign execution logs of 2026-09-07 and 2026-09-08 and must not be extrapolated to unmeasured experiments — their cell grids, worker profiles, and data scales differ.

| Experiment | Measured duration of completed run | Notes |
| --- | --- | --- |
| `synthetic-module-validation` | ≈ 3–5 s wall per canonical run (measured runs 2.6–5.3 s); single validation cell | Ran to completion twice on 2026-09-07, but `fedcampaign status` now reports it `BLOCKED` (stale) because the material digest changed — a re-run is required before its evidence may be reused. |
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
