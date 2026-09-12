# Progress

## Baseline

| Item | Value |
| --- | --- |
| Baseline commit | `ba00b07` (`_baseline-sha.txt`) |
| Baseline markers in `src/` | 66 (`_baseline-markers.txt`) |
| Baseline failing gates | `test_no_todos_or_temporary_code`, `test_no_comments_or_docstrings` (exactly 66 comment violations) |
| Baseline graphify | 3360 nodes / 23197 edges / 134 communities |

## Audit cycles executed

| Cycle | Scope | Outcome |
| --- | --- | --- |
| A — Git forensic | reflog, orphaned objects, `git show` of `6a3c8da`/`778e97d`/`7711611`, marker extraction, deletion audit, wrapper/conversion audit | 66 markers classified; 3 revisions reconstructed; 1 orphaned revision recovered from `.git` |
| B — type & enum | `types.py` full inventory, `enums.py` full inventory, repository-wide string-domain scan, `.value`/`float()`/`int()`/`str()`/`cast()` scan on changed files | 3 enums created, 3 workflows propagated, 0 conversions introduced |
| C — Graphify wiring/dead-code | fresh `graphify update . --force`, relation-filtered in-degree analysis, classification of all 20 candidates | 0 `TRULY_DEAD`, 0 `MISSING_WIRING` |
| D — second type/enum review after graphify | re-scan changed files for `.value`/casts/wrappers; `OwnershipStatement` usage check; enum-integrity registration | clean; gate extended to cover new enums |
| E — final full diff review | read every hunk of `git diff` for 18 source + 3 test files | no suspicious deletion, no weakened type, no behaviour change |
| F — final Graphify | `graphify update . --force` on the final tree | 3363 nodes / 23357 edges / 150 communities |

## Files changed

Source (18):

```
src/fedcampaign_emhi/cli.py
src/fedcampaign_emhi/comparators/federated.py
src/fedcampaign_emhi/datasets/edge_iiotset/canonicalization.py
src/fedcampaign_emhi/datasets/ton_iot_network/canonicalization.py
src/fedcampaign_emhi/domain/enums.py
src/fedcampaign_emhi/domain/types.py
src/fedcampaign_emhi/emhi/contexts.py
src/fedcampaign_emhi/emhi/evidence.py
src/fedcampaign_emhi/emhi/projection.py
src/fedcampaign_emhi/emhi/structure.py
src/fedcampaign_emhi/evaluation/validation.py
src/fedcampaign_emhi/execution/preprocessing.py
src/fedcampaign_emhi/experiments/synthetic.py
src/fedcampaign_emhi/experiments/synthetic_execution.py
src/fedcampaign_emhi/models/autoencoder.py
src/fedcampaign_emhi/runtime.py
src/fedcampaign_emhi/synthetic/feasibility.py
src/fedcampaign_emhi/synthetic/generators.py
```

Tests (3):

```
tests/architecture/test_enum_integrity.py
tests/integration/execution/test_selective_invalidation.py
tests/unit/synthetic/test_context_boundaries.py
```

## Gate results (final tree)

| Gate | Command | Result |
| --- | --- | --- |
| Ruff format | `ruff format --check src tests` | `207 files already formatted` |
| Ruff lint | `ruff check src tests` | `All checks passed!` |
| Strict typing | `pyright` | `0 errors, 0 warnings, 0 informations` |
| Semgrep | `semgrep --config .semgrep.yml src` | `0 findings` (4 rules, 89 files) |
| Import Linter | `lint-imports` | `2 kept, 0 broken` |
| deptry | `deptry src` | `Success! No dependency issues found.` |
| Vulture | `vulture src` | no output (pass) |
| pytest (full) | `pytest` | **1497 tests pass**, 0 failures |
| architecture subset | `pytest tests/architecture` | pass |
| Graphify | `graphify update . --force` | rebuilt from final tree |

## Owner decisions applied (second round)

| Item | Decision | Action |
| --- | --- | --- |
| U1 typed errors | "remove those todo statements, they are baseless" | markers stay deleted; no exception hierarchy introduced; premise recorded as rejected with the 254-site / 19-handler evidence |
| U2 vocabulary | distinct states; model as `ArtifactReuseDecision` | `ArtifactReuseDecision` (REUSED / REBUILT) added and gate-registered; all 4 materialisation sites now log `decision=%s` from the domain value; `reuse_decision_from_reusability` centralises the mapping |
| U3 `OwnershipStatement` | delete | deleted from `domain/types.py`; zero references remain |
| U4 exception identity | dedicated exception type | `AutoregressiveEpochCountError(ValueError)` added; harness catches the type, not `str(error)`; latent no-raise bug also closed |
| U6 branch divergence | investigate, report only | diagnosed as marker-cleanup difference in 2 files, **not** line endings; branch/remote untouched |

Second-round files changed: `domain/types.py`, `domain/enums.py`,
`synthetic/generators.py`, `experiments/seed_materialization.py`,
`experiments/seed_evaluation.py`, `tests/architecture/test_enum_integrity.py`.

## Final state

```
ruff format --check   207 files already formatted
ruff check            All checks passed!
pyright               0 errors, 0 warnings, 0 informations
semgrep               0 findings (4 rules, 89 files)
lint-imports          2 kept, 0 broken
deptry                Success! No dependency issues found.
vulture               no output (pass)
pytest (full)         1497 tests, exit code 0
markers in src/       0
comments in src/      0
graphify              3435 nodes / 23523 edges / 160 communities (final tree)
```

Diff at review time: 23 files changed, 252 insertions(+), 154 deletions(-).

Four enums now carry closed semantic domains end-to-end:
`ReuseDecision`, `ArtifactReuseDecision`, `SmokeFixtureName`,
`EstimatorFeasibilityConditionName` — all registered in the enum-integrity gate.

## Commits

| Commit | Subject |
| --- | --- |
| `cdf84a9` | Remove false-positive TODO markers from already-typed values |
| `e0643c5` | Convert remaining stringly-typed domains to enums and fix related defects |
| (this one) | Record the forensic TODO review |

## Preservation guarantees

* No `git reset`, `checkout`, `restore`, `clean`, or `stash` was run at any point.
* No commit was created. `main` is at `ba00b07`; all corrections are unstaged
  working-tree modifications.
* The rebase was completed only after explicit user authorisation, choosing the
  "finish the rebase with the commit as-is, then apply fixes on top" option.
* The orphaned pre-rebase revision `778e97d` and the superseded `7711611` remain
  in the object database and were read for the forensic ledger, not discarded.
* No scientific value, threshold, seed, metric, or experiment identity changed.
  Payload/hash equality was proven empirically for both affected artifacts.

## Discovery log (issues found *during* the work)

1. Working tree was clean despite the brief describing uncommitted changes —
   the work was committed inside a paused rebase. Recorded and confirmed with
   the user before any git operation.
2. `ba00b07` silently dropped a subset of `7711611`'s markers; recovered from
   the reflog and recorded as `UNRESOLVED_BY_TREE`.
3. `778e97d`, which carried the "primitive type leaks" markers, was orphaned by
   a `reset HEAD~1`. Recovered via `git show` (dangling objects are still
   readable). Its recommendation was assessed as a false premise.
4. The bulk of "should be constant" markers directly contradicted the
   repository's own enforced policy: `tests/architecture/test_no_hardcoded_values.py`
   defines `ALLOWED_FLOATS = {0.0, 0.5, 1.0, 2.0, 8.0}` and a `FORMULA_OWNERS`
   exemption set that includes exactly the files the markers targeted. Those four
   gates were verified green *before* any fix.
5. `SmokeFixtureName` was a **wrapper dataclass**, not a raw string — so the
   marker was superficially wrong but pointed at a real wrapper anti-pattern.
   The correct fix was to make it an enum, not to ignore it.
