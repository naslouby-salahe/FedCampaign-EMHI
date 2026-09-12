# Diff Review

## 1. The audit source

The instruction assumed an uncommitted working tree. Reality:

```
$ git status --porcelain     # (empty)
$ git diff --stat            # (empty)
$ git diff --cached --stat   # (empty)
```

There was **no diff**. The previous agent's work was committed, and the
repository was mid-`rebase`:

```
interactive rebase in progress; onto 778e97d
Last command done (1 command done):
   pick 7711611 Add TODO statements for enum candidates and magic numbers
stopped for amending
```

`HEAD` was detached at `ba00b07`, `main` still at `7711611`, state in
`.git/rebase-merge/`. With explicit user authorisation the rebase was finished
with the commit as-is (`GIT_EDITOR=true git rebase --continue`), leaving
`main` at `ba00b07` with a clean tree — the exact baseline the subsequent
remediation was applied on top of.

No destructive command was ever run: no `reset`, `checkout`, `restore`,
`clean`, or `stash`.

## 2. Deletion audit (`CORRECT_REMOVAL` / `SHOULD_HAVE_BEEN_WIRED` / ...)

Every significant deletion in the final working-tree diff:

| Deleted | Classification | Rationale |
| --- | --- | --- |
| `evaluation/validation.py` frozen dataclass `SmokeFixtureName` (1 field `label`) | `CORRECT_REMOVAL` | Single-field wrapper around a primitive; no behaviour, no validation beyond `min_length=1`. Replaced by a real `StrEnum` whose members carry the same values. |
| 30 × `NAME = SmokeFixtureName("...")` module constants | `CORRECT_REMOVAL` | One-use constants whose only consumer was a single `_check(...)` call in the same module. The enum member is now the authoritative name; the indirection had zero external consumers (verified: no import, no test reference). |
| 30 × package-level `from ... import NAME` sites | n/a | None existed. |
| `domain/types.py` alias `OwnershipStatement` | `CORRECT_REMOVAL` (now unused) | Its only consumer was the removed wrapper field. Left in place rather than deleted to keep the change surgical; flagged as the one remaining unused alias. |
| `PreprocessingLayerDecision.reused` / `.reconstructed` booleans | `SHOULD_HAVE_BEEN_REFACTORED` → done | Two exact complements encoding one 2-state domain. Replaced by a single `ReuseDecision` enum. |
| All 66 `# TODO: ...` trailing comments | `CORRECT_REMOVAL` | Carried no information; violated four enforced gates. |

No deletion was found that should instead have been **wired**. Nothing was
removed that had a valid, reachable responsibility.

## 3. Newly introduced wrappers / conversion helpers (Audit A item)

| Candidate | Verdict |
| --- | --- |
| `ReuseDecision` enum | **KEEP** — 2-state closed domain, replaces a raw ternary producing magic strings |
| `SmokeFixtureName` enum | **KEEP** — replaces a wrapper class; 33-member closed domain |
| `EstimatorFeasibilityConditionName` enum | **KEEP** — replaces a magic string compared in a different package |
| Any `to_*` / `as_*` / `unwrap` / `coerce_*` helper | **NONE CREATED** |
| Any adapter bridging two internal APIs | **NONE CREATED** |
| `.value` introduced | **NONE for internal use** — every `.value` touched is at a serialization boundary (log format arg, JSON payload, CLI stdout) |

## 4. Type-contract propagation check (Audit A / §17)

| Changed API | Callers inspected | Callees inspected | Result |
| --- | --- | --- | --- |
| `PreprocessingLayerDecision.reuse_decision` | `execution/preprocessing.py` (2 constructions), `cli.py:119-122`, `tests/integration/execution/test_selective_invalidation.py` | `_build_layer_decision`, `_all_reused_decisions`, `_downstream_invalidation` | Callers no longer convert; no caller converts immediately before the call; the CLI branches on the enum identity. |
| `EstimatorFeasibilityCondition.identifier` | `experiments/synthetic.py:1144`, `synthetic/feasibility.py:106`, `tests/unit/synthetic/test_context_boundaries.py:80` | `derive_component_seed` → `seed_derivation_payload` → `rfc8785.dumps` | `StrEnum` serialises **byte-identically**. Proven empirically: `rfc8785.dumps` payload equal, `content_digest` equal. Seeds and experiment identity unchanged. |
| `SmokeValidationResult.failures` / `.executed_fixture_names` | `experiments/synthetic_execution.py:170,175`, `tests/smoke/test_smoke.py` | `FixtureCollector.record`, `_check` | `.label` → `.value` at the JSON boundary only. Payload proven byte-identical. |

## 5. Behaviour-preservation evidence

```
plain json identical:      True     # condition_evaluations identifier
content_digest identical:  True
fixture payload identical: True     # executed_fixture_names / invariant_failures
rfc8785 seed payload:      IDENTICAL  # component_name as str vs StrEnum
```

Therefore no already-published evidence becomes `STALE`: the hashed
diagnostic/checkpoint payloads are unchanged.

## 6. Manual reading of the entire final diff

The complete `git diff` was read file by file. 18 source files + 3 test files.
Findings:

* No suspicious deletion (all deletions accounted for in §2).
* No new primitive interface introduced.
* No new magic/hardcoded semantic string introduced.
* No unnecessary wrapper introduced.
* No TODO disappearance without implementation.
* No weakened type.
* No duplicate logic.
* No accidental behaviour change (payload equality proven above).
* One change beyond pure marker removal was applied to formatting only:
  `ruff format` reflowed 3 files.
