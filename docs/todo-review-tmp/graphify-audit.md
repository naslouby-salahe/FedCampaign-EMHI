# Graphify Audit

## 1. Runs performed

| Run | When | Scope | Result |
| --- | --- | --- | --- |
| A (baseline) | before remediation | commit `ba00b07` tree | 3360 nodes, 23197 edges, 134 communities |
| B (final) | after all source fixes | corrected tree | **3363 nodes, 23357 edges, 150 communities** |

`graphify update . --force` was used for both, so the final graph corresponds to
the final source tree (`--force` is required after refactors that delete code,
otherwise Graphify refuses to overwrite a graph with fewer nodes).

No previous Graphify output was trusted; `graphify-out/` was regenerated from
scratch in both runs. `graphify-out/` is gitignored
(`.gitignore:235`), so these runs do not pollute the working tree.

## 2. What was inspected

* CLI-to-leaf call chains — see `wiring-audit.md` §5.
* Unreachable callables — relation-filtered in-degree analysis over
  `graph.json`. 20 candidates, **all** classified (0 `TRULY_DEAD`,
  0 `MISSING_WIRING`). Full table in `wiring-audit.md` §3.
* Isolated / duplicated workflow branches — none newly introduced: the diff
  does not add or remove any function, module, or branch. It changes field
  types, comparison forms, and constant definitions inside existing control flow.
* Methods whose only purpose is conversion/wrapping — none added; the removed
  `SmokeFixtureName` dataclass was the only value-forwarding layer, and it is
  gone.
* Unnecessary forwarding layers — the 30 one-use module constants in
  `evaluation/validation.py` were exactly that; removed.
* Saturated modules — `execution/preprocessing.py` and
  `experiments/synthetic_execution.py` remain the largest hubs; the diff does
  not increase their fan-out (it reduces `preprocessing.py` by removing two
  dataclass fields).
* Circular / suspicious dependency paths — `lint-imports` reports
  `Layered architecture KEPT` and
  `CLI contains no scientific implementation layers as reverse dependencies KEPT`
  (2 kept, 0 broken) against the final tree.

## 3. Delta interpretation

Node/edge growth (3360→3363, 23197→23357) is consistent with the three new
`StrEnum` classes and their members being extracted as new symbols, plus the
re-clustering (134→150 communities) that follows. There is **no** node-count
decrease, which confirms no production callable, class, or module was lost.

## 4. Graphify limitations encountered (recorded, not worked around)

Graphify's static edge extraction does **not** resolve:

* decorator applications (`@log_stage`)
* `functools.wraps`-preserving wrappers
* `threading.Thread(target=f)`
* `multiprocessing.Pool.submit(f, ...)` / `pool.map(f, ...)`
* aliased imports (`from x import y as z`)

All 20 reported un-referenced callables fall into exactly these five patterns.
They were therefore classified as `FALSE_POSITIVE` **with the call site quoted**,
not silently dismissed.

## 5. Final graph state

The final `graphify-out/graph.json`, `graph.html` and `GRAPH_REPORT.md` were
generated from the final source tree. No stale Graphify result is reported here.
