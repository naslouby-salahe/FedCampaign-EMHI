# Unresolved

Status of every item raised during the forensic review. All items are either
**resolved** or **explicitly closed with owner input**, except U2 which awaits one
confirmation.

---

## U1. "Typed error / message class" — CLOSED, rejected by owner

```
Sites:       14 marker sites from dropped commit 778e97d
             (config/loading.py, config/schema.py, datasets/*, emhi/calibration.py,
              experiments/{registry,seed_materialization,synthetic}.py)
Owner decision: "No remove those todo statements. They are baseless."
Assessment:  FALSE PREMISE, confirmed.
             raise ValueError("<literal>") passes a file-local diagnostic message,
             not a primitive across a domain interface. There is no receiving API
             whose type contract needs repair. The layer already owns the correct
             dedicated error type (ConfigurationValidationError(ValueError),
             config/validation.py:9, 9 raise sites in config/loading.py).
Evidence gathered: 254 raise ValueError sites, 19 `except ValueError` handlers.
             A 254-site exception taxonomy would be a project-wide redesign whose
             effect on existing handlers is nil (subclasses are still caught by
             `except ValueError`), i.e. pure churn.
Action:      Markers deleted (none remain in the tree). No exception hierarchy
             introduced. No marker re-added.
Status:      RESOLVED — nothing outstanding.
```

---

## U2. `reconstructed` vs `rebuilt` — RESOLVED (modelled as distinct domains)

```
Owner decision: "Treat them as genuinely distinct states, not synonyms."
Follow-up choice: model it as `ArtifactReuseDecision` (REUSED / REBUILT).
```

INVESTIGATION — the two words label two different OBJECTS, which is why they are
genuinely distinct and should not share one enum:

  (a) "reconstructed"  ->  PreprocessingLayerDecision
      execution/preprocessing.py compares each layer's stored dependency
      fingerprint against its expected fingerprint and selects a reconstruction
      start layer. It decides WHICH PREPROCESSING LAYER must be re-materialised.
      Domain type: `ReuseDecision.RECONSTRUCTED` / `.REUSED`

  (b) "rebuilt"        ->  downstream ARTIFACTS: detector scores, marginal ranks,
      EMHI fit, evaluation cells.
      experiments/seed_materialization.py: if the artifact file exists AND its
      dependency_fingerprint matches -> REUSED (early return); otherwise the
      artifact is re-derived from prepared dataset + split -> REBUILT.
      Domain type: `ArtifactReuseDecision.REUSED` / `.REBUILT`

IMPLEMENTATION:
  * `ReuseDecision` (a) — already in place, used as a domain value, gate-enforced.
  * `ArtifactReuseDecision` (b) — added to domain/enums.py:172 and registered in
    tests/architecture/test_enum_integrity.py so its values can no longer be
    written as bare literals anywhere in src/.
  * One total decision function centralises the mapping:
        def reuse_decision_from_reusability(reusable: Boolean) -> ArtifactReuseDecision:
            if reusable:
                return ArtifactReuseDecision.REUSED
            return ArtifactReuseDecision.REBUILT
    It lives in experiments/seed_materialization.py (the module that owns artifact
    materialisation) and is imported by experiments/seed_evaluation.py for the
    evaluation-cell site.
  * All 4 sites now log `decision=%s` with `reuse_decision.value`; the literal
    "reused"/"rebuilt" strings are gone from every format string
    (grep for `decision=reused` / `decision=rebuilt` returns nothing).
  * Detector scores, marginal ranks, EMHI fit: the fingerprint comparison is
    computed once into `reusable`, then converted to the domain value and used for
    both the branch and the log.
  * Evaluation cell: `_reusable_completed_real_cell(...)` returns a boolean that is
    fed straight into `reuse_decision_from_reusability`.

ONE OBSERVABILITY CHANGE, called out explicitly:
  The evaluation-cell site previously logged ONLY the REUSED case; the rebuild path
  was silent. It now logs `decision=rebuilt` too, matching the other three sites.
  This adds one log line per rebuilt evaluation cell and changes no artifact, hash,
  stored value, or control flow.

Status:  RESOLVED.
```

## U3. `OwnershipStatement` — RESOLVED

```
File:    domain/types.py
Owner decision: delete.
Action:  DELETED. grep for `OwnershipStatement` across src/ and tests/ returns
         nothing. Its only consumer was the removed SmokeFixtureName dataclass field.
Status:  RESOLVED.
```

---

## U4. Exception identity by message string — RESOLVED

```
File:    synthetic/generators.py
Owner decision: add a dedicated exception type and catch that.

Action taken:
  1. New `AutoregressiveEpochCountError(ValueError)` at generators.py:36.
     It subclasses ValueError so all 19 existing `except ValueError` handlers
     continue to catch it unchanged.
  2. The raise site in `generate_unit_variance_autoregressive_latent` now raises
     `AutoregressiveEpochCountError`.
  3. The validation harness no longer branches on `str(error)`:
         caught_epoch_count_error = False
         try:
             generate_unit_variance_autoregressive_latent(0, 0.5, 11)
         except AutoregressiveEpochCountError:
             caught_epoch_count_error = True
         if caught_epoch_count_error:
             negative_rejections += 1
         else:
             failed.append("negative latent epoch count rejection")

  This also closed a latent bug: previously `negative_rejections` was incremented
  only inside the `except` block, so a call that failed to raise recorded no
  failure at all. The rewritten form now reports the missing rejection.

  Remaining `str(error)` at experiments/synthetic_execution.py:573,575 is message
  *rendering* into a diagnostic tuple, not identity branching.
Status:  RESOLVED.
```

---

## U5. `str(...)` in the registry digest payload — CLOSED, no change

```
File:    domain/types.py, deterministic_registry_payload
Reviewed: start_epoch / end_epoch are domain-typed and stringified into a
          newline-joined blob that is then SHA-256 hashed.
Assessment: LEGITIMATE_BOUNDARY. The blob is a serialisation format; the values are
          not passed onward as primitives; test_no_scalar_conversion_churn passes.
Status:  CLOSED, no action.
```

---

## U6. `main` vs `origin/main` divergence — RESOLVED (report only)

```
main        = ba00b07  "Add TODO statements for magic numbers and enum candidates"
origin/main = 7711611  "Add TODO statements for enum candidates and magic numbers"
merge-base  = 6a3c8da
```

**NOT line endings.** `git diff --ignore-all-space` and `--ignore-cr-at-eol` still
report 17 changed lines, and both commits' blobs are plain LF Python source.
`core.autocrlf=true` is set and there is no `.gitattributes`; the LF→CRLF warnings
are a working-tree normalisation notice, not the divergence.

The difference is exactly the marker cleanup, in 2 files:

| Direction | Content |
| --- | --- |
| `7711611` → `ba00b07` | removes 17 `# TODO: should be constant` comments from `analysis/statistics.py` (12) and `config/loading.py` (5) |
| `ba00b07` → `7711611` | re-adds them |

So `main` is **strictly cleaner than the remote**: the aborted-and-resumed rebase
produced a tip that had already dropped marker residue `origin/main` still carries.

Per owner decision: investigated and reported; nothing changed; branch and remote
state untouched.
Status:  CLOSED.
```
