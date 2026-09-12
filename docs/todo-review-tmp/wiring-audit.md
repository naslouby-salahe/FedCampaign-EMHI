# Wiring Audit

## 1. Method

A fresh Graphify extraction was run against the final source tree:

```
$ graphify update . --force
[graphify watch] Rebuilt: 3363 nodes, 23357 edges, 150 communities
```

baseline for comparison (run before remediation): 3360 nodes / 23197 edges / 134 communities.

The Graphify CLI exposes only `update`, `path`, `explain`, `cluster-only`,
`diagnose multigraph`, `merge-*` — there is **no dead-code query command**.
`graphify-out/graph.json` was therefore analysed directly with the relation
graph (`calls`, `references`, `uses`, `inherits`, `imports`, `imports_from`,
`method`), excluding the structural `contains` relation.

## 2. Reachability result

808 production callables were identified in `src/fedcampaign_emhi/**`.
Filtering out `__dunder__` members, **20** had no semantic incoming reference.

## 3. Classification of every reported item

| Symbol | File | Classification | Evidence |
| --- | --- | --- | --- |
| `main` | `cli.py:47` | `REFLECTION_OR_FRAMEWORK_ENTRYPOINT` | Typer/console-script entry; `pyproject` `[project.scripts] fedcampaign = ...cli:application` |
| `doctor_command`, `preprocess_command`, `plan_command`, `smoke_command`, `run_command`, `status_command`, `report_command` | `cli.py` | `BOUNDARY_ENTRYPOINT` | Invoked by Typer via decorator registration, never by direct call |
| `log_stage` | `runtime.py:109` | `FALSE_POSITIVE` | `functools.wraps` decorator; used as `@log_stage(...)` in `evaluation/validation.py:134` |
| `normalize_event_type` (×2) | both `canonicalization.py` | `FALSE_POSITIVE` | Imported under alias and called: `execution/preprocessing.py:39,70,658,743,807`; also exercised by tests |
| `schema_is_executable` (×2) | `datasets/*/validation.py` | `FALSE_POSITIVE` | Imported and called in `datasets/ton_iot_network/loading.py:12` and `datasets/edge_iiotset/loading.py:62` |
| `_run_client` | `comparators/federated.py:378` | `FALSE_POSITIVE` | `threading.Thread(target=_run_client, args=(port, client), daemon=True)` at `:363` — passed as a value, not called |
| `execute_synthetic_worker_task` | `experiments/synthetic_execution.py:595` | `FALSE_POSITIVE` | `pool.submit(execute_synthetic_worker_task, task)` at `:718` |
| `_execute_real_seed_worker` | `experiments/seed_evaluation.py:1131` | `FALSE_POSITIVE` | Passed as a callable at `:1121` |
| `_context_sensitivity_seed_worker` | `experiments/seed_evaluation.py:1615` | `FALSE_POSITIVE` | Passed as a callable at `:1642` |
| `_benign_common_mode_seed_difference_worker` | `experiments/seed_statistics.py:1180` | `FALSE_POSITIVE` | `pool.map(..., tasks)` at `:1270` |
| `_count_stress_false_declaration_rates_worker` | `experiments/seed_statistics.py:1195` | `FALSE_POSITIVE` | `pool.map(..., tasks)` at `:1532` |
| `_benign_common_mode_positive_power_seed_worker` | `experiments/seed_statistics.py:1634` | `FALSE_POSITIVE` | multiprocessing worker passed as a value |

**`TRULY_DEAD`: 0. `MISSING_WIRING`: 0.**

No missing wiring was introduced or discovered. No item was deleted.

## 4. Independent corroboration

The repository enforces dead-code detection itself:

* `tests/architecture/test_dead_code.py` runs `vulture src --min-confidence 80`
  and asserts exit code 0. **PASSES.**
* `make quality` also runs `vulture src` directly. **PASSES (no output).**

Because `vulture` (which performs real reference analysis rather than graph edge
counting) reports nothing, and since every Graphify candidate above is
explicitly traceable to a call site, the graph's 20 findings are confirmed
FALSE POSITIVES rather than genuine dead code.

## 5. Workflow traces (CLI → leaf)

| Workflow | Entry point | Reachable layer chain | Leaf operations |
| --- | --- | --- | --- |
| `doctor` | `cli.doctor_command` | `runtime.assess_implementation_readiness` → `config.loading.load_production_configuration` | `material_digest`, `RESUME_SEQUENCE` echo |
| `preprocess` | `cli.preprocess_command` | `execution.preprocessing.execute_preprocess` → `_execute_dataset` → `_build_layer_decision` / `_all_reused_decisions` → `_materialize_layer` | inventory, prepared, splits, partitions, campaign registry |
| `plan` | `cli.plan_command` | `execution.planning.plan_experiments` → `experiments.registry.experiment_registry` | plan snapshot |
| `smoke` | `cli.smoke_command` | `experiments.synthetic_execution.execute_synthetic_module_validation` → `evaluation.validation.run_synthetic_module_validation` | 33 invariant fixtures |
| `run` | `cli.run_command` | `execution.runner.execute_experiment` → `experiments.synthetic.run_synthetic_cell` / `seed_evaluation` / `seed_statistics` → `synthetic.feasibility`, `emhi.calibration` | cells, checkpoints, statistics |
| `status` | `cli.status_command` | `execution.status.project_status` → `artifacts` hash verification | lifecycle state |
| `report` | `cli.report_command` | `reporting.evidence.materialize_report_scope` | report tables/figures |

Each traced chain terminates in real leaf science code with no forwarding-only
layer discovered. The `is ReuseDecision.*` and `is EstimatorFeasibilityConditionName.*`
changes sit inside existing chains and introduce no new layer.

## 6. Wrapper / forwarding-layer scan on the final graph

Candidate conversion-or-wrapping helpers introduced by the audited diff: none
(see `diff-review.md` §3). The only removed indirection is the 30-constant
`SmokeFixtureName(...)` soup in `evaluation/validation.py`, which was a
value-forwarding layer with no behaviour.
