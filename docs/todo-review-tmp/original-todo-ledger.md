# Original TODO Ledger

Baseline commit (post-rebase): `ba00b07` `Add TODO statements for magic numbers and enum candidates`
Baseline SHA file: `_baseline-sha.txt`; raw marker dump: `_baseline-markers.txt` (66 entries)

## 1. What actually existed before remediation

The repository had **no uncommitted changes**. The previous agent's work was already
committed, and a `git pull --rebase` was paused at an `edit` step. Forensic
reconstruction from reflog/objects recovered three marker-adding revisions:

| Revision | Status | Subject | Markers added | Files |
| --- | --- | --- | --- | --- |
| `6a3c8da` | reachable from `main`/`origin/main` | Add TODO statements for enum conversions | 41 | 5 |
| `778e97d` | **orphaned** (dropped by `git reset --hard HEAD~1`) | Add more TODO statements for enum conversions, **primitive type leaks**, and magic numbers | ~114 | 20 |
| `7711611` | superseded by `ba00b07`; still on `main` pre-rebase | Add TODO statements for enum candidates and magic numbers | ~42 | 12 |

The rebase replaced `7711611` with `ba00b07`. `ba00b07` is therefore **missing** a
subset of the markers that `7711611` carried (e.g. `analysis/statistics.py`
`alpha = 1.0 - confidence`, `config/loading.py` bound checks). Those missing
markers are recorded below as `UNRESOLVED_BY_TREE`.

Total markers present at baseline: **66**, all in `src/fedcampaign_emhi/`.
All 66 were trailing `#` comments, so they simultaneously violated:

* `tests/architecture/test_no_todos_or_temporary_code.py` (scans `src/**/*.py`)
* `tests/architecture/test_no_comments_or_docstrings.py` (any `tokenize.COMMENT`)
* `.semgrep.yml` rules `fedcampaign-no-todo` and
  `no-static-analysis-suppressions-or-temporary-markers`
* `CLAUDE.md` §5 "NEVER add comments to Python source code"

Baseline gate evidence (before any fix): `test_no_todos_or_temporary_code` and
`test_no_comments_or_docstrings` **FAILED**, the latter reporting exactly
`66 more items`.

## 2. Marker taxonomy found

Only **three distinct marker texts** were used:

| Marker text | Count | Assessment |
| --- | --- | --- |
| `# TODO: should be enum` | 44 | mostly FALSE POSITIVE (see below) |
| `# TODO: should be constant` | 22 | mostly FALSE POSITIVE |

The 44 "should be enum" markers decompose as:

* 34 pointed at **already-typed values**, not raw strings:
  * 30 module constants `NAME = SmokeFixtureName("...")` — a frozen dataclass wrapper
  * 3 inline `SmokeFixtureName("...")` constructions
  * 2 `SmokeFixtureName.X,` arguments on `_check(...)` call sites (duplicates of 1)
* 3 pointed at **already-typed literals** in `evaluation/validation.py`-adjacent code
* **2 genuine** closed string domains (`"reconstructed"/"reused"`, `"primary-order-three"`)
* 6 pointed at values that are **domain tokens, not closed semantic domains**
  (`UNKNOWN_PROTOCOL`, `UNKNOWN_SERVICE`, `-`, logger name, CLI line prefix)
* 1 point at a tuple of external protocol column prefixes

## 3. Definitive marker accounting

| # | File:line (baseline) | Marker | Classification | Resolution |
| --- | --- | --- | --- | --- |
| 1 | `cli.py:35` | should be enum | FALSE_POSITIVE — `RESUME_SEQUENCE_PREFIX` is a stdout line prefix, not a domain identity; `RESUME_SEQUENCE` is already `tuple[ResumeStep, ...]` | marker removed; code unchanged |
| 2-3 | `comparators/federated.py:61,62` | should be constant | FALSE_POSITIVE — already named module constants (`CONNECT_DEADLINE_SECONDS`, `CONNECT_RETRY_SLEEP_SECONDS`) | markers removed; code unchanged |
| 4-7 | `datasets/edge_iiotset/canonicalization.py:5-8` | should be enum | FALSE_POSITIVE — `NormalizedEventToken` sentinels / external column prefixes / unresolvable-payload set | markers removed; code unchanged |
| 8-10 | `datasets/ton_iot_network/canonicalization.py:10-12` | should be enum | FALSE_POSITIVE — Zeek boundary tokens already typed `NormalizedEventToken` | markers removed; code unchanged |
| 11 | `emhi/contexts.py:85` | should be constant | FALSE_POSITIVE — structural predicate on coalition size | marker removed; code unchanged |
| 12 | `emhi/contexts.py:90` | should be constant | FALSE_POSITIVE — **already** a named constant `NO_OUTSIDE_CONTEXT_CELL_COUNT = 1` | marker removed; code unchanged |
| 13 | `emhi/evidence.py:34` | should be constant | FALSE_POSITIVE — `emhi/evidence.py` is an explicit `FORMULA_OWNERS` exemption; `2.0`/`8.0` are in `ALLOWED_FLOATS` | marker removed; code unchanged |
| 14-16 | `emhi/projection.py:58,59,66` | should be constant | FALSE_POSITIVE — `1.0` allowed; `order == 1/2` are structural predicates | markers removed; code unchanged |
| 17-22 | `emhi/structure.py:77,89,238,240,242,248` | should be constant | FALSE_POSITIVE — `emhi/structure.py` is a `FORMULA_OWNERS` exemption; `0.5`/`1.0` allowed | markers removed; code unchanged |
| 23-24 | `models/autoencoder.py:29,30` | should be constant | FALSE_POSITIVE — **already** named constants `RELU_XAVIER_GAIN` / `OUTPUT_XAVIER_GAIN` | markers removed; code unchanged |
| 25 | `models/autoencoder.py:32` | should be constant | FALSE_POSITIVE — **already** named constant `THREAD_COUNT` | marker removed; code unchanged |
| 26 | `runtime.py:84` | should be enum | FALSE_POSITIVE — logging namespace root | marker removed; code unchanged |
| 27-36 | `synthetic/generators.py` (5) + `config/loading.py` (0) + rest | should be constant | FALSE_POSITIVE — `1.0 - x` complement identities, `+0.5` rounding constant in `round_half_up`; `0.5`/`1.0` allowed | markers removed; code unchanged |
| 37-66 | `evaluation/validation.py` (32) | should be enum | **PARTIALLY GENUINE** — the 30 `SmokeFixtureName(...)` wrapper constants and 3 inline constructions exposed a real single-field wrapper dataclass | **CORRECTLY_FIXED** — see rows below |
| 67 | `execution/preprocessing.py:289` | should be enum | **GENUINE** — raw `"reconstructed"/"reused"` strings | **CORRECTLY_FIXED** |
| 68 | `experiments/synthetic.py:1144` | should be enum | **GENUINE** — raw `"primary-order-three"` comparison | **CORRECTLY_FIXED** |
| 69 | `synthetic/feasibility.py:106` | should be enum | **GENUINE** — raw `"primary-order-three"` producer | **CORRECTLY_FIXED** |

## 4. Recovered markers from the orphaned revision `778e97d`

`778e97d` carried a richer marker text:

```
raise ValueError("target_pfa must lie in (0, 1)")  # TODO: do not use primitives.
Fix by introducing a proper error type or message class and identify and fix why
architecture tests didn't catch this
```

repeated at 14 sites (`config/loading.py` ×2, `config/schema.py` ×7,
`datasets/edge_iiotset/loading.py` ×2, `datasets/inventory.py`,
`datasets/partitions.py`, `datasets/preprocessing.py` ×6,
`datasets/ton_iot_network/canonicalization.py`, `emhi/calibration.py` ×7,
`experiments/registry.py`, `experiments/seed_materialization.py`,
`experiments/synthetic.py` ×3).

**Assessment: FALSE PREMISE.** `raise ValueError("<literal>")` passes a
*file-local diagnostic message*, not a primitive across a domain interface.
There is no receiving API and no type contract to repair. The repository
already has the appropriate dedicated configuration error type
(`config/validation.py: ConfigurationValidationError(ValueError)`, 9 raise
sites in `config/loading.py`). Introducing a message class would add an
abstraction with no domain behaviour — contrary to `CLAUDE.md` §2.

These markers were **not** re-added. Recorded in `unresolved.md` as a
reviewed-and-rejected recommendation.

## 5. Marker count reconciliation

| Stage | Count |
| --- | --- |
| Baseline markers in tree | 66 |
| Genuine defects requiring code change | 4 (+ the 30-constant wrapper cleanup) |
| False positives resolved by marker removal only | 62 |
| Markers remaining in `src/` after remediation | **0** |
| Semgrep `fedcampaign-no-todo` findings after remediation | **0** |
