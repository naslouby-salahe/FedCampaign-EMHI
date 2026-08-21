# Milestones

> **Coverage authority:** Roadmap Coverage Inventory — FedCampaign-EMHI
> **Milestone count:** 10
> **Traceability rule:** Every implementation-bearing inventory requirement has exactly one primary milestone owner. `NON_IMPLEMENTATION` claim/scope constraints remain traceable in M10 and remain binding wherever their roadmap scope applies without becoming implementation work.

# M01 — Scientific Configuration & Repository Contract

> **Outcome:** A validated production configuration and canonical repository/test structure encode every roadmap-fixed scientific value, ownership boundary, and implementation-readiness invariant.

## At a Glance

| Field | Value |
|---|---|
| Roadmap scope | `Roadmap authority and support lock; fixed Configuration YAML/scientific configuration blocks; §16 repository structure; §23 implementation readiness` |
| Requirement ownership | `REQ-0004, REQ-0007, REQ-0105–REQ-0106, REQ-0253–REQ-0486, REQ-0491–REQ-0514, REQ-0524–REQ-0529, REQ-0554–REQ-0573, REQ-0586–REQ-0589, REQ-0592–REQ-0599, REQ-0618–REQ-0622, REQ-0651–REQ-0687, REQ-1556–REQ-1906, REQ-2806–REQ-2810, REQ-2814–REQ-2815, REQ-2818–REQ-2822, REQ-2835–REQ-2837, REQ-2847–REQ-2849, REQ-2856–REQ-2868, REQ-2895, REQ-2923–REQ-2928, REQ-2953–REQ-2955, REQ-2962` |
| Upstream milestones | `None` |
| Implementation issues | `I01`, `I02`, `I03`, `I04`, `I05`, `I06` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | None — no dedicated per-milestone audit issue; verified via `Milestone Audit.md` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every owned implementation-bearing requirement must later map to real implementation issue(s) and objective verification evidence; `NON_IMPLEMENTATION` rows remain scope/claim constraints only.

| Roadmap Section | Scope / Work Package | Requirement IDs | Implementation Issue(s) | Verification / Evidence |
|---|---|---|---|---|
| Authority; §3 support lock | Scientific authority and no-post-hoc configuration lock | `REQ-0004, REQ-0007, REQ-0105–REQ-0106` | `I01` | Typed-config tests reject external overrides, undocumented defaults, and post-hoc scientific choices. |
| Configuration YAML and fixed scientific configuration blocks | Core scientific, data, detector, context, projection and evidence configuration | `REQ-0253–REQ-0341, REQ-0491–REQ-0514, REQ-0524–REQ-0527, REQ-0554–REQ-0571, REQ-0651–REQ-0654, REQ-2814–REQ-2815, REQ-2818–REQ-2822, REQ-2835–REQ-2837` | `I01` | Load the production configuration through the typed schema; assert every exact value/grid and canonical digest. |
| Configuration YAML; randomness/synthetic/numerics blocks | Randomness, synthetic generators and numerical configuration | `REQ-0342–REQ-0410, REQ-0586–REQ-0589, REQ-0592–REQ-0599, REQ-2847–REQ-2849, REQ-2856–REQ-2868` | `I02` | Seed/numerical/config validation asserts exact roots, sample sizes, generator values, tolerances, and deterministic material identity. |
| Configuration YAML; comparator/experiment/statistics/robustness/runtime blocks | Comparator, experiment, statistical, robustness and runtime configuration | `REQ-0411–REQ-0480, REQ-0618–REQ-0622, REQ-0655–REQ-0670, REQ-0673, REQ-0675–REQ-0682, REQ-2895, REQ-2923–REQ-2928` | `I03` | Typed validation asserts exact method sets, experiment grids, statistical families, robustness/scalability grids, and runtime/retry rules. |
| Reporting configuration | Reporting precision and export configuration | `REQ-0481–REQ-0486, REQ-0683–REQ-0687` | `I04` | Reporting-config tests assert exact precision/display/export values and reject unauthorized variation. |
| Claim/materiality and robustness-grid fixed configuration | Materiality, claim-gate and robustness-grid configuration lock | `REQ-0671–REQ-0672, REQ-0674` | `I03` | Configuration/claim-gate tests prove criteria are fixed before outcomes and robustness grids are exact. |
| Fixed scientific configuration clarifications | Additional fixed configuration contract | `REQ-0528–REQ-0529, REQ-0572–REQ-0573, REQ-2953–REQ-2955, REQ-2962` | `I04`, `I06` | Targeted typed-config tests cover each fixed semantic/configuration clarification and digest participation. |
| §16 repository structure | Canonical repository, output, results and documentation tree | `REQ-1556–REQ-1671` | `I05` | Structural inventory tests verify every required path and role. |
| §16 repository structure | Source-package and public CLI module tree | `REQ-1672–REQ-1803` | `I05` | Package/import/architecture tests verify all required modules and public ownership boundaries. |
| §16 repository structure | Architecture, unit, scientific, integration, end-to-end and smoke test tree | `REQ-1804–REQ-1877` | `I05` | Test-structure checks verify every required test path is present and discoverable. |
| §16 repository/public-CLI architecture rules | Repository architecture, type, naming and ownership invariants | `REQ-1878–REQ-1906` | `I06` | Architecture/static tests enforce dependency, typing, naming, constants, quality, and ownership rules. |
| §23 | Implementation-readiness gates | `REQ-2806–REQ-2810` | `I06` | Production-config/readiness validators prove all required checks are executable and no mandatory choice is unspecified. |

### Coverage Rules

- Every mandatory requirement owned by this milestone must be present in the Roadmap Coverage Inventory.
- Every mandatory implementation-bearing requirement must map to at least one real implementation issue before implementation begins; no hypothetical issue is created in this document.
- Every conditional requirement must remain traceable and must be implemented or resolved exactly when its roadmap-defined condition applies.
- Every mapped requirement must have objective verification or evidence.
- Every implementation issue must reference the exact requirement IDs it satisfies.
- A requirement is not considered covered merely because it falls inside a requirement range or roadmap section assigned to the milestone.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when the corresponding implementation work begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the authoritative roadmap requirement it implements.
- `NON_IMPLEMENTATION` requirements remain traceability/scope constraints only and must not be converted into fictitious implementation tasks.

## Dependencies

### Milestone Dependencies

| Milestone | Required Input / Contract | Entry Gate |
|---|---|---|
| `—` | No upstream milestone dependency. The authoritative roadmap and Roadmap Coverage Inventory are external governing inputs. | `—` |

### Artifact / Interface Dependencies

| Dependency | Produced By | Required Validation |
|---|---|---|
| `—` | `—` | No upstream milestone-produced artifact/interface dependency. |

Dependency completion alone is not sufficient. Every consumed dependency must be present, valid, provenance-compatible where applicable, and compatible with the active roadmap contract.

## Implementation Issues

Implementation issues for this milestone are listed below; each issue's detailed task checklist, acceptance criteria, and required tests are defined in `Issues.md`.

| Order | Issue | Work Package | Roadmap Scope | Requirement Coverage | Depends On |
|---:|---|---|---|---|---|
| 1 | `I01` — Lock Scientific Authority and Core Production Configuration | Lock Scientific Authority and Core Production Configuration | Authority; §3 support lock; Configuration YAML and fixed scientific configuration blocks | 153 atomic requirements | None (foundational within this milestone chain) |
| 2 | `I02` — Encode Randomness, Synthetic and Numerical Configuration | Encode Randomness, Synthetic and Numerical Configuration | Configuration YAML; randomness/synthetic/numerics blocks | 97 atomic requirements | `I01` |
| 3 | `I03` — Encode Comparator, Experiment, Statistical and Runtime Configuration | Encode Comparator, Experiment, Statistical and Runtime Configuration | Configuration YAML; comparator/experiment/statistics/robustness/runtime blocks; Claim/materiality and robustness-grid fixed configuration | 110 atomic requirements | `I01` |
| 4 | `I04` — Encode Reporting and Scientific Configuration Clarifications | Encode Reporting and Scientific Configuration Clarifications | Reporting configuration; Fixed scientific configuration clarifications | 16 atomic requirements | `I01`, `I03` |
| 5 | `I05` — Establish Canonical Repository, Source and Test Structure | Establish Canonical Repository, Source and Test Structure | §16 repository structure | 322 atomic requirements | `I01` |
| 6 | `I06` — Enforce Architecture Invariants and Implementation Readiness | Enforce Architecture Invariants and Implementation Readiness | §16 repository/public-CLI architecture rules; §16 repository/test architecture enforcement roles; §23 | 37 atomic requirements | `I01`, `I02`, `I03`, `I04`, `I05` |

### Issue Contract

Every future milestone issue must:

- reference its exact roadmap section(s);
- list every covered requirement ID;
- contain a detailed implementation checklist;
- define objective acceptance criteria;
- identify required tests;
- identify required artifacts, outputs, or interfaces;
- identify required provenance or manifest updates where applicable;
- identify explicit dependencies on upstream milestones, issues, artifacts, or interfaces;
- preserve roadmap terminology and semantics;
- close only when every mapped implementation-bearing requirement and acceptance criterion is satisfied.

## Deliverables

| Deliverable | Source Issue(s) | Required Validation | Downstream Consumer |
|---|---|---|---|
| Validated production configuration and typed configuration contract | `I01`, `I02`, `I03`, `I04`, `I05`, `I06` | Exact roadmap keys, values, grids, enums, unknown-field rejection, and canonical material digest all pass configuration tests | M02–M10 |
| Canonical repository, outputs/results, source-package, documentation, and public-CLI structure | `I01`, `I02`, `I03`, `I04`, `I05`, `I06` | Structural and architecture tests verify every required path and responsibility | M02–M10 |
| Architecture, unit, scientific, integration, end-to-end, and smoke test scaffold | `I01`, `I02`, `I03`, `I04`, `I05`, `I06` | Required test paths are discoverable and architecture invariants execute successfully | M02–M10 |
| Implementation-readiness validation contract | `I01`, `I02`, `I03`, `I04`, `I05`, `I06` | Production configuration validates and roadmap-defined readiness gates are mechanically evaluable with no unspecified mandatory choice | M02 |

All roadmap-required deliverables for this milestone must appear in this table or be explicitly traceable through the Roadmap Coverage Inventory.

## Entry Criteria

Implementation may begin only when all of the following are true:

- The Roadmap Coverage Inventory is present and all inventory rows are `READY`; there are no `AMBIGUOUS` or `BLOCKED` requirements.
- The scientific configuration is treated as locked roadmap content; implementation may encode it but may not invent, tune, or externalize scientific choices.
- all required upstream milestones are complete;
- every required upstream milestone audit is `PASS`;
- every required upstream artifact, interface, schema, or manifest exists;
- every consumed dependency passes its applicable validation;
- consumed evidence is provenance-compatible and not stale where provenance applies;
- all roadmap requirements owned by this milestone are present in the Roadmap Coverage Inventory;
- every implementation-bearing requirement has an explicit verification/evidence target;
- no blocking requirement is `AMBIGUOUS` or `BLOCKED`;
- no unresolved roadmap ambiguity would force the implementer to invent a scientific, mathematical, methodological, numerical, architectural, configuration, artifact, statistical, or execution decision.

## Exit Criteria

The milestone is complete only when all of the following are true:

- Every authoritative configuration key/value/grid, enum, numerical tolerance, seed namespace, experiment grid, statistical family, runtime rule, and reporting precision rule owned by M01 validates exactly.
- The complete fixed repository and test trees exist and architecture/static tests enforce roadmap ownership, typing, naming, constants, dependency and no-hardcoding invariants.
- Implementation-readiness gates are mechanically executable without inventing scientific, architectural, numerical, configuration, artifact, or execution choices.
- every mandatory implementation-bearing requirement owned by this milestone is satisfied;
- every applicable conditional requirement is satisfied or resolved to its exact roadmap-defined valid state;
- every mapped implementation issue, once issues exist, is closed;
- all required unit, scientific, integration, end-to-end, and validation tests applicable to this milestone pass;
- all required deliverables are generated and validate;
- all required artifacts, interfaces, schemas, manifests, and provenance records are complete, current, and compatible;
- no required evidence is stale or incompatible with its material dependencies;
- the milestone audit is `PASS`;
- no unresolved blocking finding remains.

## Acceptance Evidence

| Evidence Area | Required Evidence | Pass Condition |
|---|---|---|
| Requirement coverage | Roadmap Coverage Inventory plus milestone ownership audit | Every implementation-bearing requirement is owned exactly once, all relevant constraints remain traceable, and no blocking coverage gap exists |
| Configuration lock | Typed configuration validation, canonical material digest, unknown/missing-field rejection | Every owned configuration requirement is represented exactly and unauthorized variation is rejected |
| Repository structure | Structural inventory and architecture tests | Every required path exists in its canonical role and all ownership/dependency/static-quality invariants pass |
| Readiness | Production-configuration and readiness validation | No mandatory choice remains unspecified and readiness rules produce only roadmap-defined states |
| Provenance | Required manifests, dependency identity and compatibility evidence | Complete and sufficient to verify origin, compatibility and staleness where applicable |
| Audit | Milestone audit issue | Final result is `PASS` with no unresolved blocking findings |

## Milestone Audit

**Audit issue:** `—`

**Status:** `PENDING`

The milestone audit is the final completion gate. It must independently verify:

- complete roadmap coverage for all requirements owned by the milestone;
- exact requirement-to-issue traceability once implementation issues exist;
- closure of every mandatory implementation issue once issues exist;
- completion and passing status of all required tests and validations;
- existence and validity of all required deliverables;
- completeness and validity of required provenance and manifests;
- absence of stale or incompatible evidence;
- absence of unresolved blocking findings;
- readiness of milestone outputs for all declared downstream consumers.

The audit must end in exactly one result:

- `PASS` — every completion condition is satisfied.
- `FAIL` — one or more blocking conditions remain.

A milestone is not complete until the audit result is `PASS`.

## Scope Boundary

- Scientific methods, data processing, experiment execution, inference, and reporting logic are not implemented here beyond configuration, repository and readiness contracts consumed downstream.
- This milestone implements only the roadmap requirements explicitly assigned to it.
- The authoritative roadmap remains the source of scientific, mathematical, methodological, architectural, numerical, configuration, artifact, statistical, and execution requirements.
- This milestone may organize implementation work but may not redefine, weaken, extend, or silently reinterpret the roadmap.
- Detailed implementation checklists belong in implementation issues.
- Detailed verification checklists belong in the milestone audit issue.
- Work outside this milestone's mapped roadmap scope must not be added unless the roadmap or coverage inventory is explicitly updated first.

# M02 — Artifact Runtime, Provenance & Execution Orchestration

> **Outcome:** The project can deterministically identify, validate, reuse, invalidate, resume, recover, and orchestrate scientific artifacts and experiment cells under the roadmap's artifact-first provenance contract.

## At a Glance

| Field | Value |
|---|---|
| Roadmap scope | `§1; canonical serialization/hash/seed rules; §16 doctor/plan/run/status and orchestration boundaries; §17; §18.1–§18.6; §19.1–§19.2; §22 JCS grounding` |
| Requirement ownership | `REQ-0008–REQ-0051, REQ-0574–REQ-0585, REQ-1907–REQ-1910, REQ-1919–REQ-1927, REQ-1931–REQ-1952, REQ-1958, REQ-1960, REQ-1962–REQ-1963, REQ-1965–REQ-2312, REQ-2350–REQ-2381, REQ-2804–REQ-2805, REQ-2817, REQ-2838–REQ-2846, REQ-2959, REQ-2970–REQ-2973` |
| Upstream milestones | `M01` |
| Implementation issues | `I07`, `I08`, `I09`, `I10`, `I11`, `I12` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | None — no dedicated per-milestone audit issue; verified via `Milestone Audit.md` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every owned implementation-bearing requirement must later map to real implementation issue(s) and objective verification evidence; `NON_IMPLEMENTATION` rows remain scope/claim constraints only.

| Roadmap Section | Scope / Work Package | Requirement IDs | Implementation Issue(s) | Verification / Evidence |
|---|---|---|---|---|
| §1 | Artifact-first conceptual execution lifecycle | `REQ-0008–REQ-0051, REQ-2959` | `I07` | CLI/integration tests exercise validate→reuse→invalidate descendants→recompute missing→resume nearest-valid behavior and exact failure semantics. |
| Canonical serialization; §22 JCS grounding | Canonical serialization, deterministic hashing and seed derivation | `REQ-0574–REQ-0585, REQ-2804–REQ-2805, REQ-2817, REQ-2838–REQ-2846` | `I08` | Golden JCS/hash/seed fixtures prove input-order independence, stable identity, and exact normalization rules. |
| §16.1, §16.3, §16.5–§16.6, §16.8–§16.9 | Doctor/plan/run/status orchestration and command ownership | `REQ-1907–REQ-1910, REQ-1919–REQ-1927, REQ-1931–REQ-1952, REQ-1958, REQ-1960, REQ-1962–REQ-1963, REQ-1965–REQ-1989` | `I09` | CLI integration/e2e tests assert read/write ownership, deterministic enumeration, reuse, overwrite, recovery, and prohibited side effects. |
| §17.1–§17.3 | Semantic identity, dependency graph and material fingerprints | `REQ-1990–REQ-2056` | `I10` | Identity/fingerprint tests prove semantic filenames and material dependency hashes change only when material inputs change. |
| §17.4–§17.6 | Compatibility, selective invalidation and execution states | `REQ-2057–REQ-2102, REQ-2970–REQ-2973` | `I11` | Fault-injection tests verify provenance compatibility, atomic completion, selective invalidation, and exact state namespaces. |
| §17.7–§17.9 | Recovery, checkpoints, caches, logging and dependency index | `REQ-2103–REQ-2147` | `I11` | Recovery tests verify retries, repair, descendant cleanup, compatible checkpoints/caches, structured logs, and dependency-index integrity. |
| §18.1–§18.2 | Evidence boundary and artifact lifecycle | `REQ-2148–REQ-2203` | `I12` | Schema/lifecycle tests ensure only active current verified artifacts can become evidence and ownership transitions are explicit. |
| §18.3–§18.6 | Dataset, campaign, scientific-cell and result provenance schemas | `REQ-2204–REQ-2312` | `I12` | Schema/provenance tests validate required identities, lineage, fields, compatibility, and staleness detection. |
| §19.1–§19.2 | Execution roles and confirmatory-cell obligations | `REQ-2350–REQ-2381` | `I12` | Experiment-role tests enumerate the exact development/confirmatory obligations, seed roles, prerequisites, and zero missing-cell tolerance. |

### Coverage Rules

- Every mandatory requirement owned by this milestone must be present in the Roadmap Coverage Inventory.
- Every mandatory implementation-bearing requirement must map to at least one real implementation issue before implementation begins; no hypothetical issue is created in this document.
- Every conditional requirement must remain traceable and must be implemented or resolved exactly when its roadmap-defined condition applies.
- Every mapped requirement must have objective verification or evidence.
- Every implementation issue must reference the exact requirement IDs it satisfies.
- A requirement is not considered covered merely because it falls inside a requirement range or roadmap section assigned to the milestone.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when the corresponding implementation work begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the authoritative roadmap requirement it implements.
- `NON_IMPLEMENTATION` requirements remain traceability/scope constraints only and must not be converted into fictitious implementation tasks.

## Dependencies

### Milestone Dependencies

| Milestone | Required Input / Contract | Entry Gate |
|---|---|---|
| M01 — Scientific Configuration & Repository Contract | Validated production configuration, repository/module/test structure, and ownership boundaries | `Complete + audit PASS` |

### Artifact / Interface Dependencies

| Dependency | Produced By | Required Validation |
|---|---|---|
| Production configuration and canonical material digest | M01 | Schema-valid, exact roadmap values, stable canonical identity |
| Repository/package/test structure | M01 | Required paths, ownership boundaries, and architecture checks pass |

Dependency completion alone is not sufficient. Every consumed dependency must be present, valid, provenance-compatible where applicable, and compatible with the active roadmap contract.

## Implementation Issues

Implementation issues for this milestone are listed below; each issue's detailed task checklist, acceptance criteria, and required tests are defined in `Issues.md`.

| Order | Issue | Work Package | Roadmap Scope | Requirement Coverage | Depends On |
|---:|---|---|---|---|---|
| 1 | `I07` — Implement Artifact-First Execution Lifecycle | Implement Artifact-First Execution Lifecycle | §1 | 45 atomic requirements | `I06` |
| 2 | `I08` — Implement Canonical Serialization, Hashing and Seed Derivation | Implement Canonical Serialization, Hashing and Seed Derivation | Canonical serialization; §22 JCS grounding | 24 atomic requirements | `I06` |
| 3 | `I09` — Implement Doctor, Plan, Run and Status Orchestration | Implement Doctor, Plan, Run and Status Orchestration | §16.1, §16.3, §16.5–§16.6, §16.8–§16.9 | 64 atomic requirements | `I06`, `I07`, `I08` |
| 4 | `I10` — Implement Semantic Identity, Dependency Graph and Material Fingerprints | Implement Semantic Identity, Dependency Graph and Material Fingerprints | §17.1–§17.3 | 67 atomic requirements | `I07`, `I08` |
| 5 | `I11` — Implement Compatibility, Selective Invalidation, Recovery and Execution States | Implement Compatibility, Selective Invalidation, Recovery and Execution States | §17.4–§17.6; §17.7–§17.9 | 95 atomic requirements | `I09`, `I10` |
| 6 | `I12` — Implement Evidence Lifecycle, Provenance Schemas and Confirmatory Execution Roles | Implement Evidence Lifecycle, Provenance Schemas and Confirmatory Execution Roles | §18.1–§18.2; §18.3–§18.6; §19.1–§19.2 | 197 atomic requirements | `I11` |

### Issue Contract

Every future milestone issue must:

- reference its exact roadmap section(s);
- list every covered requirement ID;
- contain a detailed implementation checklist;
- define objective acceptance criteria;
- identify required tests;
- identify required artifacts, outputs, or interfaces;
- identify required provenance or manifest updates where applicable;
- identify explicit dependencies on upstream milestones, issues, artifacts, or interfaces;
- preserve roadmap terminology and semantics;
- close only when every mapped implementation-bearing requirement and acceptance criterion is satisfied.

## Deliverables

| Deliverable | Source Issue(s) | Required Validation | Downstream Consumer |
|---|---|---|---|
| Canonical scientific identity, dependency graph, and material-fingerprint engine | `I07`, `I08`, `I09`, `I10`, `I11`, `I12` | Deterministic identity and fingerprint fixtures are stable across equivalent inputs and change only for material dependencies | M03–M10 |
| Artifact lifecycle and selective invalidation runtime | `I07`, `I08`, `I09`, `I10`, `I11`, `I12` | Fault-injection tests prove compatibility, reuse, stale-descendant removal, nearest-valid-boundary resume, and atomic completion | M03–M10 |
| Provenance, scientific-cell, campaign, dataset, result, and analysis manifest schemas | `I07`, `I08`, `I09`, `I10`, `I11`, `I12` | Schema, integrity, dependency identity, and provenance-compatibility validation passes | M03–M10 |
| Doctor/plan/run/status orchestration layer | `I07`, `I08`, `I09`, `I10`, `I11`, `I12` | CLI integration and end-to-end reuse/recovery/overwrite tests pass without prohibited side effects | M03–M10 |

All roadmap-required deliverables for this milestone must appear in this table or be explicitly traceable through the Roadmap Coverage Inventory.

## Entry Criteria

Implementation may begin only when all of the following are true:

- M01 has produced the validated production configuration, canonical repository/module/test structure, and architecture ownership boundaries.
- Runtime identity/fingerprint logic consumes only M01-owned configuration and canonical serialization rules.
- all required upstream milestones are complete;
- every required upstream milestone audit is `PASS`;
- every required upstream artifact, interface, schema, or manifest exists;
- every consumed dependency passes its applicable validation;
- consumed evidence is provenance-compatible and not stale where provenance applies;
- all roadmap requirements owned by this milestone are present in the Roadmap Coverage Inventory;
- every implementation-bearing requirement has an explicit verification/evidence target;
- no blocking requirement is `AMBIGUOUS` or `BLOCKED`;
- no unresolved roadmap ambiguity would force the implementer to invent a scientific, mathematical, methodological, numerical, architectural, configuration, artifact, statistical, or execution decision.

## Exit Criteria

The milestone is complete only when all of the following are true:

- Artifact validation/reuse/invalidation/resume implements the complete roadmap lifecycle and selective-descendant semantics.
- Semantic cell identities, material fingerprints, execution states, checkpoints, caches, logs, dependency indexes, and provenance manifests are deterministic and validated.
- `doctor`, `plan`, `run`, and `status` obey exact ownership/side-effect/reuse/recovery contracts; development/confirmatory roles are represented without post-hoc state mutation.
- every mandatory implementation-bearing requirement owned by this milestone is satisfied;
- every applicable conditional requirement is satisfied or resolved to its exact roadmap-defined valid state;
- every mapped implementation issue, once issues exist, is closed;
- all required unit, scientific, integration, end-to-end, and validation tests applicable to this milestone pass;
- all required deliverables are generated and validate;
- all required artifacts, interfaces, schemas, manifests, and provenance records are complete, current, and compatible;
- no required evidence is stale or incompatible with its material dependencies;
- the milestone audit is `PASS`;
- no unresolved blocking finding remains.

## Acceptance Evidence

| Evidence Area | Required Evidence | Pass Condition |
|---|---|---|
| Requirement coverage | Roadmap Coverage Inventory plus milestone ownership audit | Every implementation-bearing requirement is owned exactly once, all relevant constraints remain traceable, and no blocking coverage gap exists |
| Artifact lifecycle | Integration/fault-injection tests over valid, stale, missing, failed, invalid and reusable artifacts | Only material descendants are invalidated; compatible ancestors/siblings remain reusable |
| Identity and provenance | Canonical identity/fingerprint/manifest/compatibility fixtures | Equivalent inputs serialize identically and all current artifacts expose complete dependency provenance |
| Recovery and CLI orchestration | Checkpoint/cache/retry/overwrite plus doctor/plan/run/status e2e tests | Interrupted/stale runs resume from the nearest valid boundary and commands obey exact side-effect ownership |
| Provenance | Required manifests, dependency identity and compatibility evidence | Complete and sufficient to verify origin, compatibility and staleness where applicable |
| Audit | Milestone audit issue | Final result is `PASS` with no unresolved blocking findings |

## Milestone Audit

**Audit issue:** `—`

**Status:** `PENDING`

The milestone audit is the final completion gate. It must independently verify:

- complete roadmap coverage for all requirements owned by the milestone;
- exact requirement-to-issue traceability once implementation issues exist;
- closure of every mandatory implementation issue once issues exist;
- completion and passing status of all required tests and validations;
- existence and validity of all required deliverables;
- completeness and validity of required provenance and manifests;
- absence of stale or incompatible evidence;
- absence of unresolved blocking findings;
- readiness of milestone outputs for all declared downstream consumers.

The audit must end in exactly one result:

- `PASS` — every completion condition is satisfied.
- `FAIL` — one or more blocking conditions remain.

A milestone is not complete until the audit result is `PASS`.

## Scope Boundary

- This milestone provides execution/provenance infrastructure; it does not implement scientific estimators, datasets, statistical methods, experiments, or claims.
- This milestone implements only the roadmap requirements explicitly assigned to it.
- The authoritative roadmap remains the source of scientific, mathematical, methodological, architectural, numerical, configuration, artifact, statistical, and execution requirements.
- This milestone may organize implementation work but may not redefine, weaken, extend, or silently reinterpret the roadmap.
- Detailed implementation checklists belong in implementation issues.
- Detailed verification checklists belong in the milestone audit issue.
- Work outside this milestone's mapped roadmap scope must not be added unless the roadmap or coverage inventory is explicitly updated first.

# M03 — Scientific Definitions, Generators & Reference Methods

> **Outcome:** The ODI/EMII theory, deterministic synthetic generators, controlled campaign families, and fixed comparator/reference methods are implemented as numerically verifiable scientific primitives.

## At a Glance

| Field | Value |
|---|---|
| Roadmap scope | `§2.1–§2.2 implementation definitions; fixed scientific derivations; synthetic generators; exclusion-matched dependence/HOFD references; strong comparator/sequential references; §22 comparator grounding` |
| Requirement ownership | `REQ-0052–REQ-0065, REQ-0487–REQ-0490, REQ-0590–REQ-0591, REQ-0600–REQ-0617, REQ-0623–REQ-0650, REQ-2803, REQ-2850–REQ-2855, REQ-2869–REQ-2894, REQ-2896–REQ-2898, REQ-2900–REQ-2911, REQ-2913–REQ-2922` |
| Upstream milestones | `M01, M02` |
| Implementation issues | `I13`, `I14`, `I15`, `I16` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | None — no dedicated per-milestone audit issue; verified via `Milestone Audit.md` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every owned implementation-bearing requirement must later map to real implementation issue(s) and objective verification evidence; `NON_IMPLEMENTATION` rows remain scope/claim constraints only.

| Roadmap Section | Scope / Work Package | Requirement IDs | Implementation Issue(s) | Verification / Evidence |
|---|---|---|---|---|
| §2.1–§2.2 | ODI and EMII formal definitions | `REQ-0052–REQ-0065` | `I13` | Hand-computed/property tests verify exact formulas, strict inequalities, admissible-information rules, and stopping semantics. |
| Scientific definitions/derivations | Fixed scientific method rules | `REQ-0487–REQ-0490` | `I13` | Deterministic unit/numerical tests exercise each fixed derivation and prohibited alternative choice. |
| Synthetic generator/campaign definitions | Deterministic synthetic generators and controlled campaign families | `REQ-0590–REQ-0591, REQ-0600–REQ-0617, REQ-2850–REQ-2855, REQ-2869–REQ-2894` | `I14` | Seeded fixtures verify exact distributions/effects, pure-order properties, context/dropout/contamination behavior, and input-order independence. |
| Comparator reference definitions | Exclusion-matched dependence and HOFD reference methods | `REQ-0623–REQ-0640, REQ-2896–REQ-2898, REQ-2900–REQ-2911` | `I15` | Analytic/numerical fixtures validate exact conditioning/exclusion, support, and reference quantities within locked tolerance. |
| Comparator/sequential reference definitions; §22 adaptation rule | Strong comparator and sequential reference implementations | `REQ-0641–REQ-0650, REQ-2803, REQ-2913–REQ-2922` | `I16` | Comparator/reference tests validate exact roadmap adaptations, calibration/stopping behavior, and serialized fitted artifacts. |

### Coverage Rules

- Every mandatory requirement owned by this milestone must be present in the Roadmap Coverage Inventory.
- Every mandatory implementation-bearing requirement must map to at least one real implementation issue before implementation begins; no hypothetical issue is created in this document.
- Every conditional requirement must remain traceable and must be implemented or resolved exactly when its roadmap-defined condition applies.
- Every mapped requirement must have objective verification or evidence.
- Every implementation issue must reference the exact requirement IDs it satisfies.
- A requirement is not considered covered merely because it falls inside a requirement range or roadmap section assigned to the milestone.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when the corresponding implementation work begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the authoritative roadmap requirement it implements.
- `NON_IMPLEMENTATION` requirements remain traceability/scope constraints only and must not be converted into fictitious implementation tasks.

## Dependencies

### Milestone Dependencies

| Milestone | Required Input / Contract | Entry Gate |
|---|---|---|
| M01 — Scientific Configuration & Repository Contract | Locked scientific values, generator/comparator grids, seed namespaces, and numerical tolerances | `Complete + audit PASS` |
| M02 — Artifact Runtime, Provenance & Execution Orchestration | Deterministic identity, seed derivation, artifact schemas, and execution/provenance APIs | `Complete + audit PASS` |

### Artifact / Interface Dependencies

| Dependency | Produced By | Required Validation |
|---|---|---|
| Scientific configuration, generator/reference grids and numerical tolerances | M01 | Exact values and canonical digest validate |
| Canonical seed/identity/provenance services | M02 | Golden fixtures and provenance compatibility pass |

Dependency completion alone is not sufficient. Every consumed dependency must be present, valid, provenance-compatible where applicable, and compatible with the active roadmap contract.

## Implementation Issues

Implementation issues for this milestone are listed below; each issue's detailed task checklist, acceptance criteria, and required tests are defined in `Issues.md`.

| Order | Issue | Work Package | Roadmap Scope | Requirement Coverage | Depends On |
|---:|---|---|---|---|---|
| 1 | `I13` — Implement ODI, EMII and Fixed Scientific Definitions | Implement ODI, EMII and Fixed Scientific Definitions | §2.1–§2.2; Scientific definitions/derivations | 18 atomic requirements | `I06`, `I12` |
| 2 | `I14` — Implement Deterministic Synthetic Generators and Campaign Families | Implement Deterministic Synthetic Generators and Campaign Families | Synthetic generator/campaign definitions | 52 atomic requirements | `I08`, `I13` |
| 3 | `I15` — Implement Exclusion-Matched Dependence and HOFD Reference Methods | Implement Exclusion-Matched Dependence and HOFD Reference Methods | Comparator reference definitions | 33 atomic requirements | `I08`, `I13` |
| 4 | `I16` — Implement Strong Comparator and Sequential Reference Methods | Implement Strong Comparator and Sequential Reference Methods | Comparator/sequential reference definitions; §22 adaptation rule | 21 atomic requirements | `I08`, `I13`, `I15` |

### Issue Contract

Every future milestone issue must:

- reference its exact roadmap section(s);
- list every covered requirement ID;
- contain a detailed implementation checklist;
- define objective acceptance criteria;
- identify required tests;
- identify required artifacts, outputs, or interfaces;
- identify required provenance or manifest updates where applicable;
- identify explicit dependencies on upstream milestones, issues, artifacts, or interfaces;
- preserve roadmap terminology and semantics;
- close only when every mapped implementation-bearing requirement and acceptance criterion is satisfied.

## Deliverables

| Deliverable | Source Issue(s) | Required Validation | Downstream Consumer |
|---|---|---|---|
| ODI and EMII mathematical primitives | `I13`, `I14`, `I15`, `I16` | Hand-computed and property-based formula/invariant tests pass | M06–M10 |
| Deterministic synthetic generator suite and controlled campaign families | `I13`, `I14`, `I15`, `I16` | Seed-repeatability, generator-purity, target-order, support, contamination and dropout invariants pass | M07, M09 |
| Exclusion-matched dependence and HOFD reference implementations | `I13`, `I14`, `I15`, `I16` | Numerical/reference fixtures match the roadmap-defined population quantities and exclusions | M06–M07 |
| Strong comparator and sequential reference implementations | `I13`, `I14`, `I15`, `I16` | Reference-specific unit/numerical tests and serialization/provenance checks pass | M06–M09 |

All roadmap-required deliverables for this milestone must appear in this table or be explicitly traceable through the Roadmap Coverage Inventory.

## Entry Criteria

Implementation may begin only when all of the following are true:

- M01 and M02 are complete and audited.
- All generator/reference identities, numerical tolerances, seed namespaces, and artifact/provenance interfaces needed by scientific primitives are fixed.
- all required upstream milestones are complete;
- every required upstream milestone audit is `PASS`;
- every required upstream artifact, interface, schema, or manifest exists;
- every consumed dependency passes its applicable validation;
- consumed evidence is provenance-compatible and not stale where provenance applies;
- all roadmap requirements owned by this milestone are present in the Roadmap Coverage Inventory;
- every implementation-bearing requirement has an explicit verification/evidence target;
- no blocking requirement is `AMBIGUOUS` or `BLOCKED`;
- no unresolved roadmap ambiguity would force the implementer to invent a scientific, mathematical, methodological, numerical, architectural, configuration, artifact, statistical, or execution decision.

## Exit Criteria

The milestone is complete only when all of the following are true:

- ODI/EMII definitions and all fixed derivations pass analytic/property checks.
- All controlled synthetic generators reproduce their declared effects/order/context/dropout/contamination properties under the locked seed contract.
- All exclusion-matched dependence, HOFD, strong-comparator and sequential reference methods match roadmap-defined reference quantities and prohibited alternatives are rejected.
- every mandatory implementation-bearing requirement owned by this milestone is satisfied;
- every applicable conditional requirement is satisfied or resolved to its exact roadmap-defined valid state;
- every mapped implementation issue, once issues exist, is closed;
- all required unit, scientific, integration, end-to-end, and validation tests applicable to this milestone pass;
- all required deliverables are generated and validate;
- all required artifacts, interfaces, schemas, manifests, and provenance records are complete, current, and compatible;
- no required evidence is stale or incompatible with its material dependencies;
- the milestone audit is `PASS`;
- no unresolved blocking finding remains.

## Acceptance Evidence

| Evidence Area | Required Evidence | Pass Condition |
|---|---|---|
| Requirement coverage | Roadmap Coverage Inventory plus milestone ownership audit | Every implementation-bearing requirement is owned exactly once, all relevant constraints remain traceable, and no blocking coverage gap exists |
| Theory and formulas | Hand-computed/property fixtures | ODI/EMII and fixed derivations match exact roadmap mathematics |
| Controlled generators | Seeded generator purity/support/order/context/dropout/contamination fixtures | Every generator realizes its declared structure deterministically |
| Reference methods | Analytic/numerical comparator/HOFD/sequential reference fixtures | Reference outputs and exclusions match roadmap-defined quantities/tolerances |
| Provenance | Required manifests, dependency identity and compatibility evidence | Complete and sufficient to verify origin, compatibility and staleness where applicable |
| Audit | Milestone audit issue | Final result is `PASS` with no unresolved blocking findings |

## Milestone Audit

**Audit issue:** `—`

**Status:** `PENDING`

The milestone audit is the final completion gate. It must independently verify:

- complete roadmap coverage for all requirements owned by the milestone;
- exact requirement-to-issue traceability once implementation issues exist;
- closure of every mandatory implementation issue once issues exist;
- completion and passing status of all required tests and validations;
- existence and validity of all required deliverables;
- completeness and validity of required provenance and manifests;
- absence of stale or incompatible evidence;
- absence of unresolved blocking findings;
- readiness of milestone outputs for all declared downstream consumers.

The audit must end in exactly one result:

- `PASS` — every completion condition is satisfied.
- `FAIL` — one or more blocking conditions remain.

A milestone is not complete until the audit result is `PASS`.

## Scope Boundary

- These are scientific primitives/reference methods; production data processing, EMHI orchestration, statistical inference, experiment execution and claim synthesis are owned downstream.
- Novelty and claim-boundary `NON_IMPLEMENTATION` constraints remain governed by M10 and may not be converted here into new novelty claims.
- This milestone implements only the roadmap requirements explicitly assigned to it.
- The authoritative roadmap remains the source of scientific, mathematical, methodological, architectural, numerical, configuration, artifact, statistical, and execution requirements.
- This milestone may organize implementation work but may not redefine, weaken, extend, or silently reinterpret the roadmap.
- Detailed implementation checklists belong in implementation issues.
- Detailed verification checklists belong in the milestone audit issue.
- Work outside this milestone's mapped roadmap scope must not be added unless the roadmap or coverage inventory is explicitly updated first.

# M04 — Statistical Inference & Decision Contract

> **Outcome:** The roadmap's inferential machinery is implemented and fixture-validated as a reusable contract for independent units, pairing, sign-flip tests, BCa/bootstrap intervals, effect estimation, multiplicity control, PFA inference, materiality aggregation, and invalid/missing-cell semantics before claim-bearing experiments consume it.

## At a Glance

| Field | Value |
|---|---|
| Roadmap scope | `§14.1–§14.15 statistical and inferential contract, including fixed statistical clarifications` |
| Requirement ownership | `REQ-1442–REQ-1541, REQ-2945–REQ-2948, REQ-2965` |
| Upstream milestones | `M01, M02` |
| Implementation issues | `I17`, `I18`, `I19`, `I20` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | None — no dedicated per-milestone audit issue; verified via `Milestone Audit.md` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every owned implementation-bearing requirement must later map to real implementation issue(s) and objective verification evidence; `NON_IMPLEMENTATION` rows remain scope/claim constraints only.

| Roadmap Section | Scope / Work Package | Requirement IDs | Implementation Issue(s) | Verification / Evidence |
|---|---|---|---|---|
| §14.1–§14.3 | Experimental units, aggregation units and pairing keys | `REQ-1442–REQ-1464, REQ-2945–REQ-2946` | `I17` | Deterministic unit/pairing fixtures validate exact real/synthetic independent units, within-seed aggregation rules, pairing coordinates, and unmatched-comparator handling. |
| §14.4–§14.5 | Exact and Monte Carlo sign-flip inference | `REQ-1465–REQ-1482` | `I17` | Known-result fixtures validate exact enumeration, fallback simulation count/seed, one-/two-sided extremeness, zero handling, and finite-simulation correction. |
| §14.6–§14.9 | BCa, hierarchical bootstrap, Hodges-Lehmann and equivalence procedures | `REQ-1483–REQ-1496, REQ-2947–REQ-2948, REQ-2965` | `I18` | Deterministic resampling fixtures validate paired resampling, confidence bounds, campaign hierarchy, Walsh averages, numerical-failure semantics, and equivalence decisions. |
| §14.10–§14.11 | Directional hypothesis contracts and Holm multiplicity control | `REQ-1497–REQ-1522` | `I19` | Fixed-family fixtures prove exact hypothesis membership/order, direction, `Not Tested` bookkeeping, Holm input handling, tie ordering, and adjusted p-values. |
| §14.12–§14.14 | PFA/descriptive intervals and primary materiality aggregation | `REQ-1523–REQ-1534` | `I20` | Known-count and synthetic seed-level fixtures validate Clopper-Pearson inference, primary ODI/advantage aggregation, operational-lead pooling, and inferential-unit preservation. |
| §14.15 | Missing, failed, unavailable and invalid cell semantics | `REQ-1535–REQ-1541` | `I20` | Fault fixtures verify no imputation, valid no-stop/unfavorable/operating-point outcomes, technical `Failed`, scientific/provenance `Invalid`, and zero-missing confirmatory completeness gating. |

### Coverage Rules

- Every mandatory requirement owned by this milestone must be present in the Roadmap Coverage Inventory.
- Every mandatory implementation-bearing requirement must map to at least one real implementation issue before implementation begins; no hypothetical issue is created in this document.
- Every conditional requirement must remain traceable and must be implemented or resolved exactly when its roadmap-defined condition applies.
- Every mapped requirement must have objective verification or evidence.
- Every implementation issue must reference the exact requirement IDs it satisfies.
- A requirement is not considered covered merely because it falls inside a requirement range or roadmap section assigned to the milestone.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when the corresponding implementation work begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the authoritative roadmap requirement it implements.
- `NON_IMPLEMENTATION` requirements remain traceability/scope constraints only and must not be converted into fictitious implementation tasks.

## Dependencies

### Milestone Dependencies

| Milestone | Required Input / Contract | Entry Gate |
|---|---|---|
| M01 — Scientific Configuration & Repository Contract | Locked statistical configuration, confidence levels, significance level, bootstrap/sign-flip counts, materiality/equivalence gates, and statistical seed namespace | `Complete + audit PASS` |
| M02 — Artifact Runtime, Provenance & Execution Orchestration | Canonical result/statistical artifact identity, provenance, execution-state semantics, and deterministic RNG/serialization contracts | `Complete + audit PASS` |

### Artifact / Interface Dependencies

| Dependency | Produced By | Required Validation |
|---|---|---|
| Statistical configuration and predeclared decision/materiality contracts | M01 | Exact values, fixed families/gates, and statistical seed identity validate |
| Canonical RNG, result/statistics artifact identity and execution-state semantics | M02 | Deterministic serialization/seed fixtures and provenance/state validators pass |

Dependency completion alone is not sufficient. Every consumed dependency must be present, valid, provenance-compatible where applicable, and compatible with the active roadmap contract.

## Implementation Issues

Implementation issues for this milestone are listed below; each issue's detailed task checklist, acceptance criteria, and required tests are defined in `Issues.md`.

| Order | Issue | Work Package | Roadmap Scope | Requirement Coverage | Depends On |
|---:|---|---|---|---|---|
| 1 | `I17` — Implement Experimental Units, Pairing and Sign-Flip Inference | Implement Experimental Units, Pairing and Sign-Flip Inference | §14.1–§14.3; §14.4–§14.5 | 43 atomic requirements | `I06`, `I12` |
| 2 | `I18` — Implement Bootstrap, Hodges-Lehmann and Equivalence Procedures | Implement Bootstrap, Hodges-Lehmann and Equivalence Procedures | §14.6–§14.9 | 17 atomic requirements | `I17` |
| 3 | `I19` — Implement Directional Hypotheses and Holm Multiplicity Control | Implement Directional Hypotheses and Holm Multiplicity Control | §14.10–§14.11 | 26 atomic requirements | `I17`, `I18` |
| 4 | `I20` — Implement PFA, Materiality Aggregation and Missing-Cell Semantics | Implement PFA, Materiality Aggregation and Missing-Cell Semantics | §14.12–§14.14; §14.15 | 19 atomic requirements | `I19` |

### Issue Contract

Every future milestone issue must:

- reference its exact roadmap section(s);
- list every covered requirement ID;
- contain a detailed implementation checklist;
- define objective acceptance criteria;
- identify required tests;
- identify required artifacts, outputs, or interfaces;
- identify required provenance or manifest updates where applicable;
- identify explicit dependencies on upstream milestones, issues, artifacts, or interfaces;
- preserve roadmap terminology and semantics;
- close only when every mapped implementation-bearing requirement and acceptance criterion is satisfied.

## Deliverables

| Deliverable | Source Issue(s) | Required Validation | Downstream Consumer |
|---|---|---|---|
| Experimental-unit, aggregation-unit and pairing-key contract | `I17`, `I18`, `I19`, `I20` | Fixture tests enforce seed-level independence, within-seed repetition handling, exact pairing coordinates and unmatched-comparator exclusion | M05–M10 |
| Exact/Monte-Carlo sign-flip inference engine | `I17`, `I18`, `I19`, `I20` | Enumeration/simulation, sidedness, zero handling, deterministic RNG and finite-simulation correction match known-result fixtures | M07–M10 |
| BCa, hierarchical bootstrap, Hodges-Lehmann and equivalence engine | `I17`, `I18`, `I19`, `I20` | Paired/hierarchical resampling, confidence bounds, effect estimates, equivalence and invalid-fallback semantics pass deterministic fixtures | M07–M10 |
| Directional hypothesis-family and Holm multiplicity engine | `I17`, `I18`, `I19`, `I20` | Fixed primary/secondary families, `Not Tested` bookkeeping, ordering and adjusted p-values reproduce exact fixtures | M07–M10 |
| Clopper-Pearson/PFA and primary materiality aggregation procedures | `I17`, `I18`, `I19`, `I20` | Known-count and seed-level fixtures reproduce exact PFA bounds, ODI/advantage aggregation and operational-lead pooling | M05–M10 |
| Statistical missing/failed/unavailable/invalid-cell contract | `I17`, `I18`, `I19`, `I20` | Fault fixtures enforce no imputation, valid scientific outcomes, technical/scientific failure distinction and zero-missing confirmatory gating | M07–M10 |

All roadmap-required deliverables for this milestone must appear in this table or be explicitly traceable through the Roadmap Coverage Inventory.

## Entry Criteria

Implementation may begin only when all of the following are true:

- M01 and M02 are complete and audited.
- Statistical configuration, materiality/equivalence thresholds, hypothesis-family definitions, confidence/significance levels, resampling counts, and statistical RNG roots are fixed before any claim-bearing result is inspected.
- No real or synthetic outcome may be used to choose or alter an inferential method in this milestone.
- all required upstream milestones are complete;
- every required upstream milestone audit is `PASS`;
- every required upstream artifact, interface, schema, or manifest exists;
- every consumed dependency passes its applicable validation;
- consumed evidence is provenance-compatible and not stale where provenance applies;
- all roadmap requirements owned by this milestone are present in the Roadmap Coverage Inventory;
- every implementation-bearing requirement has an explicit verification/evidence target;
- no blocking requirement is `AMBIGUOUS` or `BLOCKED`;
- no unresolved roadmap ambiguity would force the implementer to invent a scientific, mathematical, methodological, numerical, architectural, configuration, artifact, statistical, or execution decision.

## Exit Criteria

The milestone is complete only when all of the following are true:

- Every §14 statistical/inferential procedure is implemented before it is consumed by claim-bearing experiment milestones and passes deterministic known-result/property/fault fixtures.
- Primary and secondary hypothesis families, sidedness, pairing, multiplicity, materiality/equivalence, PFA and missing/invalid-cell rules are immutable and reproducible solely from locked configuration plus current input artifacts.
- No real/synthetic scientific conclusion is produced here; this milestone ends with a validated inferential capability and decision contract.
- every mandatory implementation-bearing requirement owned by this milestone is satisfied;
- every applicable conditional requirement is satisfied or resolved to its exact roadmap-defined valid state;
- every mapped implementation issue, once issues exist, is closed;
- all required unit, scientific, integration, end-to-end, and validation tests applicable to this milestone pass;
- all required deliverables are generated and validate;
- all required artifacts, interfaces, schemas, manifests, and provenance records are complete, current, and compatible;
- no required evidence is stale or incompatible with its material dependencies;
- the milestone audit is `PASS`;
- no unresolved blocking finding remains.

## Acceptance Evidence

| Evidence Area | Required Evidence | Pass Condition |
|---|---|---|
| Requirement coverage | Roadmap Coverage Inventory plus milestone ownership audit | Every implementation-bearing requirement is owned exactly once, all relevant constraints remain traceable, and no blocking coverage gap exists |
| Experimental units and pairing | Deterministic controlled/real fixture aggregates and pairing-key tests | Independent units, repeated measurements, pairing and unmatched comparisons follow §14 exactly |
| Inference engines | Known-result sign-flip, BCa/bootstrap, Hodges-Lehmann, equivalence and Clopper-Pearson fixtures | Statistics, intervals, sidedness and numerical failure semantics reproduce exact expected results |
| Multiplicity and gates | Primary/secondary family fixtures including `Not Tested` rows and tie cases | Family membership/order, Holm inputs/outputs and materiality/equivalence separation are exact |
| Cell-state semantics | Fault fixtures for no-stop, unfavorable, unavailable, failed, invalid and missing cases | No imputation or forbidden fallback occurs; zero-missing confirmatory gating is enforced |
| Provenance | Required manifests, dependency identity and compatibility evidence | Complete and sufficient to verify origin, compatibility and staleness where applicable |
| Audit | Milestone audit issue | Final result is `PASS` with no unresolved blocking findings |

## Milestone Audit

**Audit issue:** `—`

**Status:** `PENDING`

The milestone audit is the final completion gate. It must independently verify:

- complete roadmap coverage for all requirements owned by the milestone;
- exact requirement-to-issue traceability once implementation issues exist;
- closure of every mandatory implementation issue once issues exist;
- completion and passing status of all required tests and validations;
- existence and validity of all required deliverables;
- completeness and validity of required provenance and manifests;
- absence of stale or incompatible evidence;
- absence of unresolved blocking findings;
- readiness of milestone outputs for all declared downstream consumers.

The audit must end in exactly one result:

- `PASS` — every completion condition is satisfied.
- `FAIL` — one or more blocking conditions remain.

A milestone is not complete until the audit result is `PASS`.

## Scope Boundary

- This milestone implements statistical methods and decision contracts on fixtures; it does not execute the roadmap's claim-bearing synthetic or real experiments and does not materialize manuscript claims.
- Statistical procedures, family membership and gates may not be changed after inspecting scientific outcomes.
- This milestone implements only the roadmap requirements explicitly assigned to it.
- The authoritative roadmap remains the source of scientific, mathematical, methodological, architectural, numerical, configuration, artifact, statistical, and execution requirements.
- This milestone may organize implementation work but may not redefine, weaken, extend, or silently reinterpret the roadmap.
- Detailed implementation checklists belong in implementation issues.
- Detailed verification checklists belong in the milestone audit issue.
- Work outside this milestone's mapped roadmap scope must not be added unless the roadmap or coverage inventory is explicitly updated first.

# M05 — Dataset Preparation & Local Detection Pipeline

> **Outcome:** Corrected OpTC and the conditional secondary trace can be inventoried, deterministically adapted and preprocessed into valid client/epoch partitions with fitted immutable local detectors, calibrated local-policy behavior, and score streams.

## At a Glance

| Field | Value |
|---|---|
| Roadmap scope | `§6–§7; detector definitions and §9; §16.2 preprocess; dataset-grounding rules in §22` |
| Requirement ownership | `REQ-0515–REQ-0523, REQ-0530–REQ-0553, REQ-0688–REQ-0823, REQ-0849–REQ-0867, REQ-1911–REQ-1918, REQ-1959, REQ-2800–REQ-2802, REQ-2816, REQ-2823–REQ-2834, REQ-2929–REQ-2944, REQ-2966–REQ-2969` |
| Upstream milestones | `M01, M02, M04` |
| Implementation issues | `I21`, `I22`, `I23`, `I24`, `I25`, `I26` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | None — no dedicated per-milestone audit issue; verified via `Milestone Audit.md` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every owned implementation-bearing requirement must later map to real implementation issue(s) and objective verification evidence; `NON_IMPLEMENTATION` rows remain scope/claim constraints only.

| Roadmap Section | Scope / Work Package | Requirement IDs | Implementation Issue(s) | Verification / Evidence |
|---|---|---|---|---|
| §6.1 | Raw-dataset authority, inventory and deterministic adaptation | `REQ-0688–REQ-0709` | `I21` | Raw inventory/checksum/schema/discrepancy tests prove observed bytes are authoritative and adaptation follows only predeclared rules. |
| §6.2; OpTC definitions | Corrected OpTC identity, clients, separation and ground truth | `REQ-0515–REQ-0517, REQ-0710–REQ-0751, REQ-2929` | `I22` | Dataset integration tests validate release identity, client selection, ground truth, benign/evaluation separation, eligibility and manifests. |
| §6.3; TC Engagement 5 definitions | Transparent Computing Engagement 5 secondary-data contract | `REQ-0518–REQ-0520, REQ-0752–REQ-0779, REQ-2930–REQ-2931` | `I23` | Secondary adapter tests validate client definition/selection, benign interval, ground truth, eligibility and valid ineligibility handling. |
| §7; hash/canonicalization definitions | Canonical preprocessing, epoch features, scaling, splits and benign horizons | `REQ-0521–REQ-0523, REQ-0780–REQ-0823, REQ-2816, REQ-2932–REQ-2944, REQ-2966–REQ-2969` | `I24` | Deterministic preprocessing tests validate duplicate/invalid handling, epoch features, non-finite rules, scaling, chronology, leakage and horizon construction. |
| Detector definitions; §9 | Local detector fitting, scoring and immutable local-policy behavior | `REQ-0530–REQ-0553, REQ-0849–REQ-0867, REQ-2823–REQ-2834` | `I25` | Detector unit/integration tests validate exact fitting inputs, score direction, seed behavior, policy calibration separation and immutability. |
| §16.2; §16.8 preprocess row | Preprocess CLI ownership, reuse and invalidation | `REQ-1911–REQ-1918, REQ-1959` | `I26` | CLI tests verify dataset selection, layer validation/reuse, overwrite, nearest-valid reconstruction, and selective downstream invalidation. |
| §22 raw-release grounding | Research-grounding raw-release validation rules | `REQ-2800–REQ-2802` | `I21` | Provenance tests prove documented expectations never override observed raw bytes and discrepancies remain explicit. |

### Coverage Rules

- Every mandatory requirement owned by this milestone must be present in the Roadmap Coverage Inventory.
- Every mandatory implementation-bearing requirement must map to at least one real implementation issue before implementation begins; no hypothetical issue is created in this document.
- Every conditional requirement must remain traceable and must be implemented or resolved exactly when its roadmap-defined condition applies.
- Every mapped requirement must have objective verification or evidence.
- Every implementation issue must reference the exact requirement IDs it satisfies.
- A requirement is not considered covered merely because it falls inside a requirement range or roadmap section assigned to the milestone.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when the corresponding implementation work begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the authoritative roadmap requirement it implements.
- `NON_IMPLEMENTATION` requirements remain traceability/scope constraints only and must not be converted into fictitious implementation tasks.

## Dependencies

### Milestone Dependencies

| Milestone | Required Input / Contract | Entry Gate |
|---|---|---|
| M01 — Scientific Configuration & Repository Contract | Dataset/preprocessing/detector/local-policy configuration, eligibility thresholds, epoch semantics, and canonical paths | `Complete + audit PASS` |
| M02 — Artifact Runtime, Provenance & Execution Orchestration | Dataset/provenance manifests, dependency identity, reuse/invalidation, and preprocess artifact lifecycle | `Complete + audit PASS` |
| M04 — Statistical Inference & Decision Contract | Exact PFA-UCB/Clopper-Pearson procedures and valid unavailable/invalid statistical semantics required by local-policy calibration and held-out validation | `Complete + audit PASS` |

### Artifact / Interface Dependencies

| Dependency | Produced By | Required Validation |
|---|---|---|
| Dataset/detector/local-policy configuration and repository paths | M01 | Exact values, no unauthorized overrides |
| Dataset/preprocess artifact lifecycle and manifests | M02 | Schema/provenance/reuse/invalidation validation passes |
| PFA interval/UCB and statistical failure semantics | M04 | Known-count fixtures and unavailable/invalid-state tests pass |

Dependency completion alone is not sufficient. Every consumed dependency must be present, valid, provenance-compatible where applicable, and compatible with the active roadmap contract.

## Implementation Issues

Implementation issues for this milestone are listed below; each issue's detailed task checklist, acceptance criteria, and required tests are defined in `Issues.md`.

| Order | Issue | Work Package | Roadmap Scope | Requirement Coverage | Depends On |
|---:|---|---|---|---|---|
| 1 | `I21` — Implement Raw Dataset Authority, Inventory and Adaptation | Implement Raw Dataset Authority, Inventory and Adaptation | §6.1; §22 raw-release grounding | 25 atomic requirements | `I06`, `I12`, `I20` |
| 2 | `I22` — Implement Corrected OpTC Dataset Contract | Implement Corrected OpTC Dataset Contract | §6.2; OpTC definitions | 46 atomic requirements | `I21` |
| 3 | `I23` — Implement Transparent Computing Engagement 5 Dataset Contract | Implement Transparent Computing Engagement 5 Dataset Contract | §6.3; TC Engagement 5 definitions | 33 atomic requirements | `I21` |
| 4 | `I24` — Implement Canonical Preprocessing, Splits and Benign Horizons | Implement Canonical Preprocessing, Splits and Benign Horizons | §7; hash/canonicalization definitions | 65 atomic requirements | `I08`, `I12`, `I22`, `I23` |
| 5 | `I25` — Implement Local Detectors and Immutable Local Policies | Implement Local Detectors and Immutable Local Policies | Detector definitions; §9 | 55 atomic requirements | `I24` |
| 6 | `I26` — Implement Preprocess CLI Reuse and Invalidation Contract | Implement Preprocess CLI Reuse and Invalidation Contract | §16.2; §16.8 preprocess row | 9 atomic requirements | `I11`, `I24`, `I25` |

### Issue Contract

Every future milestone issue must:

- reference its exact roadmap section(s);
- list every covered requirement ID;
- contain a detailed implementation checklist;
- define objective acceptance criteria;
- identify required tests;
- identify required artifacts, outputs, or interfaces;
- identify required provenance or manifest updates where applicable;
- identify explicit dependencies on upstream milestones, issues, artifacts, or interfaces;
- preserve roadmap terminology and semantics;
- close only when every mapped implementation-bearing requirement and acceptance criterion is satisfied.

## Deliverables

| Deliverable | Source Issue(s) | Required Validation | Downstream Consumer |
|---|---|---|---|
| Raw inventory and deterministic adaptation artifacts for Corrected OpTC and Transparent Computing Engagement 5 | `I21`, `I22`, `I23`, `I24`, `I25`, `I26` | Checksums, observed-schema inventories, discrepancy manifests, client eligibility, and ground-truth validation pass | M06, M08–M10 |
| Canonical epoch features, deduplication/invalid-record handling, scaling, chronological benign splits, and benign horizons | `I21`, `I22`, `I23`, `I24`, `I25`, `I26` | Deterministic preprocessing integration tests and split/leakage invariants pass | M06, M08–M10 |
| Fitted local detector artifacts and immutable detector score streams | `I21`, `I22`, `I23`, `I24`, `I25`, `I26` | Detector unit/integration tests, score-orientation checks, seed/config provenance, and no-policy-leakage checks pass | M06, M08–M10 |
| Calibrated primary/strong local-policy artifacts and held-out local validation records | `I21`, `I22`, `I23`, `I24`, `I25`, `I26` | Candidate-source separation, exact PFA-UCB selection, `Operating Point Unavailable`, immutability and held-out non-retuning rules pass | M06, M08–M10 |
| `preprocess` command and layer-wise reuse/invalidation behavior | `I21`, `I22`, `I23`, `I24`, `I25`, `I26` | CLI integration and end-to-end tests prove nearest-valid-layer reconstruction and selective descendant invalidation | M06, M08–M10 |

All roadmap-required deliverables for this milestone must appear in this table or be explicitly traceable through the Roadmap Coverage Inventory.

## Entry Criteria

Implementation may begin only when all of the following are true:

- M01, M02 and M04 are complete and audited.
- Raw-data handling must use observed mounted bytes and deterministic roadmap adaptation rules; literature/documented expectations cannot override the observed release.
- Local-policy calibration must consume the fixed PFA inference contract from M04 and may not use held-out or attack-period outcomes for selection.
- all required upstream milestones are complete;
- every required upstream milestone audit is `PASS`;
- every required upstream artifact, interface, schema, or manifest exists;
- every consumed dependency passes its applicable validation;
- consumed evidence is provenance-compatible and not stale where provenance applies;
- all roadmap requirements owned by this milestone are present in the Roadmap Coverage Inventory;
- every implementation-bearing requirement has an explicit verification/evidence target;
- no blocking requirement is `AMBIGUOUS` or `BLOCKED`;
- no unresolved roadmap ambiguity would force the implementer to invent a scientific, mathematical, methodological, numerical, architectural, configuration, artifact, statistical, or execution decision.

## Exit Criteria

The milestone is complete only when all of the following are true:

- Primary and secondary raw-data inventories/adapters either validate under observed release rules or produce the exact roadmap-defined invalid/ineligible state.
- Canonical preprocessing, client selection, features, scaling, chronological splits and benign horizons are deterministic and leakage-safe.
- Local detectors, score streams and local-policy artifacts satisfy exact fitting/calibration/PFA/immutability rules and are provenance-valid.
- `preprocess` reconstructs only missing/invalid layers and preserves compatible upstream artifacts.
- every mandatory implementation-bearing requirement owned by this milestone is satisfied;
- every applicable conditional requirement is satisfied or resolved to its exact roadmap-defined valid state;
- every mapped implementation issue, once issues exist, is closed;
- all required unit, scientific, integration, end-to-end, and validation tests applicable to this milestone pass;
- all required deliverables are generated and validate;
- all required artifacts, interfaces, schemas, manifests, and provenance records are complete, current, and compatible;
- no required evidence is stale or incompatible with its material dependencies;
- the milestone audit is `PASS`;
- no unresolved blocking finding remains.

## Acceptance Evidence

| Evidence Area | Required Evidence | Pass Condition |
|---|---|---|
| Requirement coverage | Roadmap Coverage Inventory plus milestone ownership audit | Every implementation-bearing requirement is owned exactly once, all relevant constraints remain traceable, and no blocking coverage gap exists |
| Raw-data authority | Inventory/checksum/schema/discrepancy and eligibility manifests | Observed bytes are authoritative and all adaptations/ineligibility outcomes follow the fixed rules |
| Preprocessing | Determinism/leakage/split/horizon integration tests | Canonical features, scaling and chronological partitions are identical for equivalent inputs with no prohibited leakage |
| Detector/local policy | Fitting/scoring/PFA-UCB/held-out/immutability tests | Models, score streams and local policies use only allowed partitions and remain immutable after calibration |
| CLI reuse | `preprocess` e2e selective invalidation tests | Only invalid/missing descendants are rebuilt |
| Provenance | Required manifests, dependency identity and compatibility evidence | Complete and sufficient to verify origin, compatibility and staleness where applicable |
| Audit | Milestone audit issue | Final result is `PASS` with no unresolved blocking findings |

## Milestone Audit

**Audit issue:** `—`

**Status:** `PENDING`

The milestone audit is the final completion gate. It must independently verify:

- complete roadmap coverage for all requirements owned by the milestone;
- exact requirement-to-issue traceability once implementation issues exist;
- closure of every mandatory implementation issue once issues exist;
- completion and passing status of all required tests and validations;
- existence and validity of all required deliverables;
- completeness and validity of required provenance and manifests;
- absence of stale or incompatible evidence;
- absence of unresolved blocking findings;
- readiness of milestone outputs for all declared downstream consumers.

The audit must end in exactly one result:

- `PASS` — every completion condition is satisfied.
- `FAIL` — one or more blocking conditions remain.

A milestone is not complete until the audit result is `PASS`.

## Scope Boundary

- This milestone produces valid data/detector/local-policy artifacts; it does not implement EMHI, execute claim-bearing experiments, or synthesize claims.
- This milestone implements only the roadmap requirements explicitly assigned to it.
- The authoritative roadmap remains the source of scientific, mathematical, methodological, architectural, numerical, configuration, artifact, statistical, and execution requirements.
- This milestone may organize implementation work but may not redefine, weaken, extend, or silently reinterpret the roadmap.
- Detailed implementation checklists belong in implementation issues.
- Detailed verification checklists belong in the milestone audit issue.
- Work outside this milestone's mapped roadmap scope must not be added unless the roadmap or coverage inventory is explicitly updated first.

# M06 — EMHI Estimation, Context Conditioning & Sequential Evidence Engine

> **Outcome:** The complete FedCampaign-EMHI estimation/evaluation engine can transform detector score streams into exclusion-matched coalition innovations, sequential evidence, stopping decisions, campaign metrics, and comparator outputs using the locked inferential and provenance contracts.

## At a Glance

| Field | Value |
|---|---|
| Roadmap scope | `§4; §8; §10.1–§10.20; §11; §12` |
| Requirement ownership | `REQ-0107–REQ-0252, REQ-0824–REQ-0848, REQ-0868–REQ-0908, REQ-0931–REQ-1064, REQ-2811–REQ-2813, REQ-2949–REQ-2951, REQ-2956, REQ-2960–REQ-2961` |
| Upstream milestones | `M01, M02, M03, M04, M05` |
| Implementation issues | `I27`, `I28`, `I29`, `I30`, `I31`, `I32`, `I33` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | None — no dedicated per-milestone audit issue; verified via `Milestone Audit.md` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every owned implementation-bearing requirement must later map to real implementation issue(s) and objective verification evidence; `NON_IMPLEMENTATION` rows remain scope/claim constraints only.

| Roadmap Section | Scope / Work Package | Requirement IDs | Implementation Issue(s) | Verification / Evidence |
|---|---|---|---|---|
| §4.1–§4.5 | Information fields, ranks, outside context and coalition conditioning | `REQ-0107–REQ-0141, REQ-2811–REQ-2812, REQ-2960` | `I27` | Property tests validate fields, ranks, context clustering/capping, coalition-conditioned residual ranks and exclusion invariants. |
| §4.6–§4.10 | Bounded basis, proper-subset projection and cross-fitted calibration | `REQ-0142–REQ-0186` | `I28` | Numerical tests validate basis construction, blocked folds, ridge/SVD selection, proper-subset design, cross-fitting and abstention. |
| §4.11–§4.15 | Signed/norm evidence and hierarchical across-order aggregation | `REQ-0187–REQ-0220, REQ-2813, REQ-2961` | `I29` | Analytic fixtures validate centering/scaling, signed and norm evidence, within/across-order aggregation and deterministic comparisons. |
| §4.16–§4.20 | Support predicates, sequential routes, replay and operational lead | `REQ-0221–REQ-0252` | `I30` | Sequential tests validate support predicates, both routes, threshold calibration, recursion, no-stop/tie behavior, replay and lead formulas. |
| §8 | Context-method variants and diagnostic exclusion controls | `REQ-0824–REQ-0848, REQ-2949, REQ-2956` | `I31` | Variant tests verify inclusive/LOO/partial/oracle/no/shuffled context and forced-no-abstention semantics without hidden fallback. |
| §10.1–§10.20 | Baseline and comparator contracts | `REQ-0868–REQ-0908` | `I32` | Comparator fairness/contract tests validate information access, calibration, fitting, stopping and fixed method identities. |
| §11 | Metric, diagnostic, latency and communication definitions | `REQ-0931–REQ-1040, REQ-2950–REQ-2951` | `I33` | Hand-computed metric fixtures validate all predictive, stopping, support, numerical, latency, throughput and payload definitions. |
| §12 | Campaign registry semantics | `REQ-1041–REQ-1064` | `I33` | Registry schema/identity tests validate campaign intervals, durations, client/ground-truth linkage and deterministic serialization. |

### Coverage Rules

- Every mandatory requirement owned by this milestone must be present in the Roadmap Coverage Inventory.
- Every mandatory implementation-bearing requirement must map to at least one real implementation issue before implementation begins; no hypothetical issue is created in this document.
- Every conditional requirement must remain traceable and must be implemented or resolved exactly when its roadmap-defined condition applies.
- Every mapped requirement must have objective verification or evidence.
- Every implementation issue must reference the exact requirement IDs it satisfies.
- A requirement is not considered covered merely because it falls inside a requirement range or roadmap section assigned to the milestone.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when the corresponding implementation work begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the authoritative roadmap requirement it implements.
- `NON_IMPLEMENTATION` requirements remain traceability/scope constraints only and must not be converted into fictitious implementation tasks.

## Dependencies

### Milestone Dependencies

| Milestone | Required Input / Contract | Entry Gate |
|---|---|---|
| M01 — Scientific Configuration & Repository Contract | Context/projection/evidence/local-policy/comparator/metric configuration and numerical tolerances | `Complete + audit PASS` |
| M02 — Artifact Runtime, Provenance & Execution Orchestration | Fitted/evidence/evaluation artifact identities, manifests, reuse and failure semantics | `Complete + audit PASS` |
| M03 — Scientific Definitions, Generators & Reference Methods | ODI/EMII primitives and fixed reference/comparator implementations | `Complete + audit PASS` |
| M04 — Statistical Inference & Decision Contract | Exact PFA/interval procedures and decision semantics consumed by finite-horizon calibration and evaluation | `Complete + audit PASS` |
| M05 — Dataset Preparation & Local Detection Pipeline | Prepared client epochs, benign partitions/horizons, campaign-source identities, fitted detectors, local-policy artifacts, and score streams | `Complete + audit PASS` |

### Artifact / Interface Dependencies

| Dependency | Produced By | Required Validation |
|---|---|---|
| ODI/EMII and fixed scientific/reference primitives | M03 | Analytic/property/reference fixtures pass |
| Statistical PFA/interval decision interfaces | M04 | Exact known-result fixtures pass |
| Prepared datasets, benign partitions/horizons, fitted detectors, local policies and score streams | M05 | Current, leakage-safe, provenance-compatible artifacts validate |
| Artifact/provenance runtime | M02 | Material fingerprints, reuse and compatibility checks pass |

Dependency completion alone is not sufficient. Every consumed dependency must be present, valid, provenance-compatible where applicable, and compatible with the active roadmap contract.

## Implementation Issues

Implementation issues for this milestone are listed below; each issue's detailed task checklist, acceptance criteria, and required tests are defined in `Issues.md`.

| Order | Issue | Work Package | Roadmap Scope | Requirement Coverage | Depends On |
|---:|---|---|---|---|---|
| 1 | `I27` — Implement Exclusion-Matched Information Fields, Ranks and Context Conditioning | Implement Exclusion-Matched Information Fields, Ranks and Context Conditioning | §4.1–§4.5 | 38 atomic requirements | `I12`, `I13`, `I20`, `I24` |
| 2 | `I28` — Implement Bounded Basis, Projection and Cross-Fitted Innovation Calibration | Implement Bounded Basis, Projection and Cross-Fitted Innovation Calibration | §4.6–§4.10 | 45 atomic requirements | `I27` |
| 3 | `I29` — Implement Signed and Operational Evidence with Hierarchical Aggregation | Implement Signed and Operational Evidence with Hierarchical Aggregation | §4.11–§4.15 | 36 atomic requirements | `I28` |
| 4 | `I30` — Implement Distributed Support, Sequential Routes, Replay and Operational Lead | Implement Distributed Support, Sequential Routes, Replay and Operational Lead | §4.16–§4.20 | 32 atomic requirements | `I25`, `I29` |
| 5 | `I31` — Implement Context Variants and Exclusion Diagnostics | Implement Context Variants and Exclusion Diagnostics | §8 | 27 atomic requirements | `I27`, `I28` |
| 6 | `I32` — Implement Baseline and Comparator Contracts | Implement Baseline and Comparator Contracts | §10.1–§10.20 | 41 atomic requirements | `I16`, `I25`, `I30`, `I31` |
| 7 | `I33` — Implement Metric Registry and Campaign Registry Semantics | Implement Metric Registry and Campaign Registry Semantics | §11; §12 | 136 atomic requirements | `I30`, `I32` |

### Issue Contract

Every future milestone issue must:

- reference its exact roadmap section(s);
- list every covered requirement ID;
- contain a detailed implementation checklist;
- define objective acceptance criteria;
- identify required tests;
- identify required artifacts, outputs, or interfaces;
- identify required provenance or manifest updates where applicable;
- identify explicit dependencies on upstream milestones, issues, artifacts, or interfaces;
- preserve roadmap terminology and semantics;
- close only when every mapped implementation-bearing requirement and acceptance criterion is satisfied.

## Deliverables

| Deliverable | Source Issue(s) | Required Validation | Downstream Consumer |
|---|---|---|---|
| Context/rank/coalition-conditioning pipeline | `I27`, `I28`, `I29`, `I30`, `I31`, `I32`, `I33` | Deterministic context, support, rank, clustering, and exclusion tests pass | M07–M10 |
| Bounded basis, proper-subset ridge projection, cross-fitted innovation calibration, centering/scaling, and evidence artifacts | `I27`, `I28`, `I29`, `I30`, `I31`, `I32`, `I33` | Numerical/property tests validate projection, folds, abstention, calibration, and standardized evidence | M07–M10 |
| Signed-theorem and calibrated finite-horizon sequential routes with support predicates, replay, and operational lead | `I27`, `I28`, `I29`, `I30`, `I31`, `I32`, `I33` | Sequential-recursion, threshold, no-stop/tie, support, replay, and PFA-interface fixtures pass | M07–M10 |
| Baseline/comparator execution contracts and common evaluation/metric library | `I27`, `I28`, `I29`, `I30`, `I31`, `I32`, `I33` | Fairness/contract tests and hand-computed metric fixtures pass | M07–M10 |
| Campaign registry semantics and evaluation records | `I27`, `I28`, `I29`, `I30`, `I31`, `I32`, `I33` | Registry schema, interval/duration identity, and campaign/benign-horizon linkage tests pass | M07–M10 |

All roadmap-required deliverables for this milestone must appear in this table or be explicitly traceable through the Roadmap Coverage Inventory.

## Entry Criteria

Implementation may begin only when all of the following are true:

- M01–M05 are complete and audited where directly required by the dependency table.
- Prepared score streams/local policies and all scientific/statistical primitives consumed by EMHI are current, provenance-compatible, and leakage-safe.
- all required upstream milestones are complete;
- every required upstream milestone audit is `PASS`;
- every required upstream artifact, interface, schema, or manifest exists;
- every consumed dependency passes its applicable validation;
- consumed evidence is provenance-compatible and not stale where provenance applies;
- all roadmap requirements owned by this milestone are present in the Roadmap Coverage Inventory;
- every implementation-bearing requirement has an explicit verification/evidence target;
- no blocking requirement is `AMBIGUOUS` or `BLOCKED`;
- no unresolved roadmap ambiguity would force the implementer to invent a scientific, mathematical, methodological, numerical, architectural, configuration, artifact, statistical, or execution decision.

## Exit Criteria

The milestone is complete only when all of the following are true:

- All information-field/rank/context/coalition/projection/cross-fitting/evidence/support/sequential-route rules pass analytic, numerical and property tests.
- Comparator fairness/contracts, metric definitions and campaign-registry semantics are implemented exactly and produce schema-valid artifacts.
- Finite-horizon calibration and local/global evaluation consume the M04 inferential contract without duplicate or divergent statistical logic.
- every mandatory implementation-bearing requirement owned by this milestone is satisfied;
- every applicable conditional requirement is satisfied or resolved to its exact roadmap-defined valid state;
- every mapped implementation issue, once issues exist, is closed;
- all required unit, scientific, integration, end-to-end, and validation tests applicable to this milestone pass;
- all required deliverables are generated and validate;
- all required artifacts, interfaces, schemas, manifests, and provenance records are complete, current, and compatible;
- no required evidence is stale or incompatible with its material dependencies;
- the milestone audit is `PASS`;
- no unresolved blocking finding remains.

## Acceptance Evidence

| Evidence Area | Required Evidence | Pass Condition |
|---|---|---|
| Requirement coverage | Roadmap Coverage Inventory plus milestone ownership audit | Every implementation-bearing requirement is owned exactly once, all relevant constraints remain traceable, and no blocking coverage gap exists |
| Estimator mathematics | Analytic/property/numerical tests across ranks, context, projection, cross-fitting, evidence and support | All formulas, exclusions, abstention and numerical rules match the roadmap |
| Sequential routes | Threshold/recursion/no-stop/replay/lead fixtures | Both routes and PFA interfaces reproduce locked behavior |
| Comparators and metrics | Fairness/contract tests plus hand-computed metric fixtures | Information access, calibration/fitting and metric definitions are exact |
| Campaign registry | Schema/identity/interval linkage fixtures | Campaign and benign-horizon identities serialize deterministically and link to exact sources |
| Provenance | Required manifests, dependency identity and compatibility evidence | Complete and sufficient to verify origin, compatibility and staleness where applicable |
| Audit | Milestone audit issue | Final result is `PASS` with no unresolved blocking findings |

## Milestone Audit

**Audit issue:** `—`

**Status:** `PENDING`

The milestone audit is the final completion gate. It must independently verify:

- complete roadmap coverage for all requirements owned by the milestone;
- exact requirement-to-issue traceability once implementation issues exist;
- closure of every mandatory implementation issue once issues exist;
- completion and passing status of all required tests and validations;
- existence and validity of all required deliverables;
- completeness and validity of required provenance and manifests;
- absence of stale or incompatible evidence;
- absence of unresolved blocking findings;
- readiness of milestone outputs for all declared downstream consumers.

The audit must end in exactly one result:

- `PASS` — every completion condition is satisfied.
- `FAIL` — one or more blocking conditions remain.

A milestone is not complete until the audit result is `PASS`.

## Scope Boundary

- Experiment-specific validation, comparator composition selection, primary real-data runs, robustness studies, and manuscript claim synthesis are not completed here.
- This milestone implements only the roadmap requirements explicitly assigned to it.
- The authoritative roadmap remains the source of scientific, mathematical, methodological, architectural, numerical, configuration, artifact, statistical, and execution requirements.
- This milestone may organize implementation work but may not redefine, weaken, extend, or silently reinterpret the roadmap.
- Detailed implementation checklists belong in implementation issues.
- Detailed verification checklists belong in the milestone audit issue.
- Work outside this milestone's mapped roadmap scope must not be added unless the roadmap or coverage inventory is explicitly updated first.

# M07 — Synthetic Validation & Comparator Composition Lock

> **Outcome:** All mandatory synthetic/theory validation gates pass, estimator/sequential feasibility is established, and the strongest comparator composition is selected deterministically before primary real-data evaluation.

## At a Glance

| Field | Value |
|---|---|
| Roadmap scope | `§10.21; §13.1–§13.7; §16.4 smoke` |
| Requirement ownership | `REQ-0909–REQ-0930, REQ-1065–REQ-1280, REQ-1928–REQ-1930, REQ-1961` |
| Upstream milestones | `M02, M03, M04, M06` |
| Implementation issues | `I34`, `I35`, `I36`, `I37`, `I38`, `I39`, `I40` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | None — no dedicated per-milestone audit issue; verified via `Milestone Audit.md` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every owned implementation-bearing requirement must later map to real implementation issue(s) and objective verification evidence; `NON_IMPLEMENTATION` rows remain scope/claim constraints only.

| Roadmap Section | Scope / Work Package | Requirement IDs | Implementation Issue(s) | Verification / Evidence |
|---|---|---|---|---|
| §10.21 | Strong comparator composition selection rule | `REQ-0909–REQ-0930` | `I34` | Selection-unit tests verify candidate set, error/runtime tie tolerances, deterministic ordering, and selected-artifact identity. |
| §13 experiment contracts | Shared experiment contracts | `REQ-1065–REQ-1067` | `I34` | Registry/contract tests verify experiment identities, roles, prerequisite graph and immutable grids. |
| §13.1; §16.4 smoke | Synthetic module validation and smoke gate | `REQ-1068–REQ-1094, REQ-1928–REQ-1930, REQ-1961` | `I35` | Smoke artifacts and repeated executions satisfy every module invariant and locked repeatability tolerance. |
| §13.2 | Self-explanation exclusion validation | `REQ-1095–REQ-1106` | `I36` | Configured perturbation/derivative results satisfy exact exclusion, attenuation and primary-condition evidence rules. |
| §13.3 | Pure-order separation and generator-purity validation | `REQ-1107–REQ-1124` | `I37` | All required generator/effect/method rows satisfy purity, proper-subset preservation, separation and materiality checks. |
| §13.4 | Exclusion-matched HOFD equivalence validation | `REQ-1125–REQ-1147` | `I38` | Support/order equivalence artifacts satisfy exact equivalence metrics, support conditions and required confirmatory rows. |
| §13.5 | Strong comparator composition challenge | `REQ-1148–REQ-1190` | `I39` | Development challenge completes all candidates/conditions and produces the predeclared selected-comparator artifact. |
| §13.6 | Estimator support, feasibility and context sensitivity validation | `REQ-1191–REQ-1235` | `I40` | Feasibility/support rows, abstention/numerical states and declared sensitivity diagnostics complete exactly. |
| §13.7 | Sequential evidence validation | `REQ-1236–REQ-1280` | `I40` | Signed-theorem and calibrated finite-horizon route artifacts satisfy null/alternative, ARL/PFA, trajectory and threshold contracts. |

### Coverage Rules

- Every mandatory requirement owned by this milestone must be present in the Roadmap Coverage Inventory.
- Every mandatory implementation-bearing requirement must map to at least one real implementation issue before implementation begins; no hypothetical issue is created in this document.
- Every conditional requirement must remain traceable and must be implemented or resolved exactly when its roadmap-defined condition applies.
- Every mapped requirement must have objective verification or evidence.
- Every implementation issue must reference the exact requirement IDs it satisfies.
- A requirement is not considered covered merely because it falls inside a requirement range or roadmap section assigned to the milestone.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when the corresponding implementation work begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the authoritative roadmap requirement it implements.
- `NON_IMPLEMENTATION` requirements remain traceability/scope constraints only and must not be converted into fictitious implementation tasks.

## Dependencies

### Milestone Dependencies

| Milestone | Required Input / Contract | Entry Gate |
|---|---|---|
| M02 — Artifact Runtime, Provenance & Execution Orchestration | Experiment registry, execution roles, manifests, resumability, and confirmatory-cell handling | `Complete + audit PASS` |
| M03 — Scientific Definitions, Generators & Reference Methods | Deterministic controlled generators and fixed comparator/reference methods | `Complete + audit PASS` |
| M04 — Statistical Inference & Decision Contract | BCa/sign-flip/PFA/equivalence procedures and fixed hypothesis/materiality semantics required by synthetic validation gates | `Complete + audit PASS` |
| M06 — EMHI Estimation, Context Conditioning & Sequential Evidence Engine | Validated EMHI/context/projection/evidence/sequential/metric implementation | `Complete + audit PASS` |

### Artifact / Interface Dependencies

| Dependency | Produced By | Required Validation |
|---|---|---|
| Controlled generators/reference methods | M03 | Generator purity/repeatability and reference tests pass |
| Statistical inference/decision engine | M04 | BCa/sign-flip/PFA/equivalence and hypothesis-family fixtures pass |
| EMHI/sequential/comparator/metric engine | M06 | Scientific unit/integration validation passes |
| Experiment execution/provenance runtime | M02 | Role, seed, manifest and resumability validation passes |

Dependency completion alone is not sufficient. Every consumed dependency must be present, valid, provenance-compatible where applicable, and compatible with the active roadmap contract.

## Implementation Issues

Implementation issues for this milestone are listed below; each issue's detailed task checklist, acceptance criteria, and required tests are defined in `Issues.md`.

| Order | Issue | Work Package | Roadmap Scope | Requirement Coverage | Depends On |
|---:|---|---|---|---|---|
| 1 | `I34` — Implement Strong Comparator Composition Selection and Shared Experiment Contracts | Implement Strong Comparator Composition Selection and Shared Experiment Contracts | §10.21; §13 experiment contracts | 25 atomic requirements | `I12`, `I16`, `I20`, `I32`, `I33` |
| 2 | `I35` — Implement Synthetic Module Validation and Smoke Gate | Implement Synthetic Module Validation and Smoke Gate | §13.1; §16.4 smoke | 31 atomic requirements | `I14`, `I30`, `I34` |
| 3 | `I36` — Validate Self-Explanation Exclusion | Validate Self-Explanation Exclusion | §13.2 | 12 atomic requirements | `I31`, `I35` |
| 4 | `I37` — Validate Pure-Order Separation and Generator Purity | Validate Pure-Order Separation and Generator Purity | §13.3 | 18 atomic requirements | `I28`, `I35` |
| 5 | `I38` — Validate Exclusion-Matched HOFD Equivalence | Validate Exclusion-Matched HOFD Equivalence | §13.4 | 23 atomic requirements | `I15`, `I28`, `I35` |
| 6 | `I39` — Execute Strong Comparator Composition Challenge | Execute Strong Comparator Composition Challenge | §13.5 | 43 atomic requirements | `I32`, `I34`, `I38` |
| 7 | `I40` — Validate Estimator Feasibility and Sequential Evidence | Validate Estimator Feasibility and Sequential Evidence | §13.6; §13.7 | 90 atomic requirements | `I20`, `I33`, `I39` |

### Issue Contract

Every future milestone issue must:

- reference its exact roadmap section(s);
- list every covered requirement ID;
- contain a detailed implementation checklist;
- define objective acceptance criteria;
- identify required tests;
- identify required artifacts, outputs, or interfaces;
- identify required provenance or manifest updates where applicable;
- identify explicit dependencies on upstream milestones, issues, artifacts, or interfaces;
- preserve roadmap terminology and semantics;
- close only when every mapped implementation-bearing requirement and acceptance criterion is satisfied.

## Deliverables

| Deliverable | Source Issue(s) | Required Validation | Downstream Consumer |
|---|---|---|---|
| Synthetic Module Validation smoke artifact | `I34`, `I35`, `I36`, `I37`, `I38`, `I39`, `I40` | All smoke/theory/baseline invariants and repeatability checks pass | M08–M10 |
| Self-explanation exclusion and pure-order separation evidence | `I34`, `I35`, `I36`, `I37`, `I38`, `I39`, `I40` | Configured development/confirmatory conditions satisfy exact attenuation, purity, separation, materiality, and statistical checks | M10 |
| Exclusion-matched HOFD equivalence evidence | `I34`, `I35`, `I36`, `I37`, `I38`, `I39`, `I40` | All declared support/order equivalence rows, BCa-equivalence gates and diagnostics are complete and valid | M10 |
| Strong comparator composition challenge and selected-comparator artifact | `I34`, `I35`, `I36`, `I37`, `I38`, `I39`, `I40` | Selection rule, PFA eligibility, error/runtime tie tolerances, development-only selection, and artifact identity validate deterministically | M08–M10 |
| Estimator support/context feasibility and sequential evidence validation artifacts | `I34`, `I35`, `I36`, `I37`, `I38`, `I39`, `I40` | Primary feasibility/support rows and both sequential routes complete under declared confirmatory/statistical obligations | M08–M10 |

All roadmap-required deliverables for this milestone must appear in this table or be explicitly traceable through the Roadmap Coverage Inventory.

## Entry Criteria

Implementation may begin only when all of the following are true:

- M02, M03, M04 and M06 are complete and audited.
- All synthetic grids, seeds, materiality/equivalence gates, inferential procedures, experiment roles and comparator candidates are locked before validation results are inspected.
- all required upstream milestones are complete;
- every required upstream milestone audit is `PASS`;
- every required upstream artifact, interface, schema, or manifest exists;
- every consumed dependency passes its applicable validation;
- consumed evidence is provenance-compatible and not stale where provenance applies;
- all roadmap requirements owned by this milestone are present in the Roadmap Coverage Inventory;
- every implementation-bearing requirement has an explicit verification/evidence target;
- no blocking requirement is `AMBIGUOUS` or `BLOCKED`;
- no unresolved roadmap ambiguity would force the implementer to invent a scientific, mathematical, methodological, numerical, architectural, configuration, artifact, statistical, or execution decision.

## Exit Criteria

The milestone is complete only when all of the following are true:

- Every mandatory synthetic/theory validation experiment and smoke gate completes under exact development/confirmatory roles.
- Self-explanation, pure-order, HOFD-equivalence, feasibility/context-sensitivity and sequential-evidence gates are evaluated using the locked M04 statistical contract.
- The strongest comparator composition is selected only by the predeclared development rule, materialized with immutable identity, and no primary real outcome influences selection.
- every mandatory implementation-bearing requirement owned by this milestone is satisfied;
- every applicable conditional requirement is satisfied or resolved to its exact roadmap-defined valid state;
- every mapped implementation issue, once issues exist, is closed;
- all required unit, scientific, integration, end-to-end, and validation tests applicable to this milestone pass;
- all required deliverables are generated and validate;
- all required artifacts, interfaces, schemas, manifests, and provenance records are complete, current, and compatible;
- no required evidence is stale or incompatible with its material dependencies;
- the milestone audit is `PASS`;
- no unresolved blocking finding remains.

## Acceptance Evidence

| Evidence Area | Required Evidence | Pass Condition |
|---|---|---|
| Requirement coverage | Roadmap Coverage Inventory plus milestone ownership audit | Every implementation-bearing requirement is owned exactly once, all relevant constraints remain traceable, and no blocking coverage gap exists |
| Synthetic smoke | Repeated smoke artifacts | All module invariants and repeatability tolerances pass |
| Theory validation | Self-explanation, pure-order and HOFD-equivalence result artifacts | All roadmap-defined attenuation/purity/equivalence/statistical gates are satisfied or produce the exact permitted outcome |
| Comparator lock | Selection-candidate table and selected-comparator manifest | Only eligible candidates participate and selection/ties are deterministic and development-only |
| Sequential feasibility | Support/context and both route validation artifacts | All required confirmatory rows and statistical gates are complete |
| Provenance | Required manifests, dependency identity and compatibility evidence | Complete and sufficient to verify origin, compatibility and staleness where applicable |
| Audit | Milestone audit issue | Final result is `PASS` with no unresolved blocking findings |

## Milestone Audit

**Audit issue:** `—`

**Status:** `PENDING`

The milestone audit is the final completion gate. It must independently verify:

- complete roadmap coverage for all requirements owned by the milestone;
- exact requirement-to-issue traceability once implementation issues exist;
- closure of every mandatory implementation issue once issues exist;
- completion and passing status of all required tests and validations;
- existence and validity of all required deliverables;
- completeness and validity of required provenance and manifests;
- absence of stale or incompatible evidence;
- absence of unresolved blocking findings;
- readiness of milestone outputs for all declared downstream consumers.

The audit must end in exactly one result:

- `PASS` — every completion condition is satisfied.
- `FAIL` — one or more blocking conditions remain.

A milestone is not complete until the audit result is `PASS`.

## Scope Boundary

- This milestone validates and locks scientific machinery on the roadmap's synthetic/theory studies; it does not execute the primary Corrected OpTC study or later robustness/generalization studies.
- This milestone implements only the roadmap requirements explicitly assigned to it.
- The authoritative roadmap remains the source of scientific, mathematical, methodological, architectural, numerical, configuration, artifact, statistical, and execution requirements.
- This milestone may organize implementation work but may not redefine, weaken, extend, or silently reinterpret the roadmap.
- Detailed implementation checklists belong in implementation issues.
- Detailed verification checklists belong in the milestone audit issue.
- Work outside this milestone's mapped roadmap scope must not be added unless the roadmap or coverage inventory is explicitly updated first.

# M08 — Primary Real-Data Strict ODI Evaluation

> **Outcome:** The complete primary Corrected OpTC evaluation is executed for every declared method and confirmatory seed, producing current strict-ODI, PFA, lead, comparator-advantage, and support evidence under the predeclared statistical contract.

## At a Glance

| Field | Value |
|---|---|
| Roadmap scope | `§13.8 Primary Strict ODI Evaluation` |
| Requirement ownership | `REQ-1281–REQ-1296` |
| Upstream milestones | `M04, M05, M06, M07` |
| Implementation issues | `I41`, `I42` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | None — no dedicated per-milestone audit issue; verified via `Milestone Audit.md` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every owned implementation-bearing requirement must later map to real implementation issue(s) and objective verification evidence; `NON_IMPLEMENTATION` rows remain scope/claim constraints only.

| Roadmap Section | Scope / Work Package | Requirement IDs | Implementation Issue(s) | Verification / Evidence |
|---|---|---|---|---|
| §13.8 | Primary Strict ODI evaluation matrix | `REQ-1281–REQ-1290` | `I41` | Current method×real-confirmatory-seed cells cover the complete eligible campaign registry and benign horizons with exact evaluation artifacts. |
| §13.8 support criteria | Full FedCampaign-EMHI primary support criteria | `REQ-1291–REQ-1296` | `I42` | Primary support/PFA/ODI/lead/comparator-advantage criteria are mechanically evaluable from current primary evidence. |

### Coverage Rules

- Every mandatory requirement owned by this milestone must be present in the Roadmap Coverage Inventory.
- Every mandatory implementation-bearing requirement must map to at least one real implementation issue before implementation begins; no hypothetical issue is created in this document.
- Every conditional requirement must remain traceable and must be implemented or resolved exactly when its roadmap-defined condition applies.
- Every mapped requirement must have objective verification or evidence.
- Every implementation issue must reference the exact requirement IDs it satisfies.
- A requirement is not considered covered merely because it falls inside a requirement range or roadmap section assigned to the milestone.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when the corresponding implementation work begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the authoritative roadmap requirement it implements.
- `NON_IMPLEMENTATION` requirements remain traceability/scope constraints only and must not be converted into fictitious implementation tasks.

## Dependencies

### Milestone Dependencies

| Milestone | Required Input / Contract | Entry Gate |
|---|---|---|
| M04 — Statistical Inference & Decision Contract | Fixed real-seed pairing, PFA inference, primary materiality aggregation, directional-test and multiplicity contracts | `Complete + audit PASS` |
| M05 — Dataset Preparation & Local Detection Pipeline | Current eligible Corrected OpTC clients, benign horizons, campaign-registry inputs, local policies, detector models, and score streams | `Complete + audit PASS` |
| M06 — EMHI Estimation, Context Conditioning & Sequential Evidence Engine | Validated EMHI, comparator, sequential-evidence, metric, and campaign-evaluation engine | `Complete + audit PASS` |
| M07 — Synthetic Validation & Comparator Composition Lock | Passing validation gates and immutable selected strong-comparator identity | `Complete + audit PASS` |

### Artifact / Interface Dependencies

| Dependency | Produced By | Required Validation |
|---|---|---|
| Real prepared data, selected clients, campaigns, local policies and score streams | M05 | Primary eligibility, preprocessing, leakage and provenance checks pass |
| EMHI/comparator/sequential/metric engine | M06 | Scientific validation passes |
| Statistical inference/decision contract | M04 | Real pairing/PFA/materiality/multiplicity rules validate |
| Synthetic validation and selected-comparator artifact | M07 | All prerequisite gates pass and selected identity is immutable |

Dependency completion alone is not sufficient. Every consumed dependency must be present, valid, provenance-compatible where applicable, and compatible with the active roadmap contract.

## Implementation Issues

Implementation issues for this milestone are listed below; each issue's detailed task checklist, acceptance criteria, and required tests are defined in `Issues.md`.

| Order | Issue | Work Package | Roadmap Scope | Requirement Coverage | Depends On |
|---:|---|---|---|---|---|
| 1 | `I41` — Execute Primary Strict ODI Evaluation Matrix | Execute Primary Strict ODI Evaluation Matrix | §13.8 | 10 atomic requirements | `I20`, `I26`, `I33`, `I40` |
| 2 | `I42` — Evaluate Full FedCampaign-EMHI Primary Support Criteria | Evaluate Full FedCampaign-EMHI Primary Support Criteria | §13.8 support criteria | 6 atomic requirements | `I20`, `I41` |

### Issue Contract

Every future milestone issue must:

- reference its exact roadmap section(s);
- list every covered requirement ID;
- contain a detailed implementation checklist;
- define objective acceptance criteria;
- identify required tests;
- identify required artifacts, outputs, or interfaces;
- identify required provenance or manifest updates where applicable;
- identify explicit dependencies on upstream milestones, issues, artifacts, or interfaces;
- preserve roadmap terminology and semantics;
- close only when every mapped implementation-bearing requirement and acceptance criterion is satisfied.

## Deliverables

| Deliverable | Source Issue(s) | Required Validation | Downstream Consumer |
|---|---|---|---|
| Primary Strict ODI method-by-seed scientific-cell outputs | `I41`, `I42` | Every declared method and required real confirmatory root completes or follows an explicit roadmap-defined valid state | M09–M10 |
| Primary campaign and held-out benign-horizon evaluations | `I41`, `I42` | Campaign detection, PFA, stopping, ODI, lead, comparator and support outputs validate against schemas, metric and statistical contracts | M09–M10 |
| Full FedCampaign-EMHI support-criteria evidence | `I41`, `I42` | All PFA, strict-ODI, comparator-advantage, operational-lead and directional-inference gates are mechanically evaluable from current primary evidence | M09–M10 |

All roadmap-required deliverables for this milestone must appear in this table or be explicitly traceable through the Roadmap Coverage Inventory.

## Entry Criteria

Implementation may begin only when all of the following are true:

- M04–M07 are complete and audited as listed in the dependency table.
- The primary raw/preprocessed data, selected-client list, campaign registry, local policies, detectors, score streams, selected comparator, and real confirmatory roots are current and immutable for the primary study.
- all required upstream milestones are complete;
- every required upstream milestone audit is `PASS`;
- every required upstream artifact, interface, schema, or manifest exists;
- every consumed dependency passes its applicable validation;
- consumed evidence is provenance-compatible and not stale where provenance applies;
- all roadmap requirements owned by this milestone are present in the Roadmap Coverage Inventory;
- every implementation-bearing requirement has an explicit verification/evidence target;
- no blocking requirement is `AMBIGUOUS` or `BLOCKED`;
- no unresolved roadmap ambiguity would force the implementer to invent a scientific, mathematical, methodological, numerical, architectural, configuration, artifact, statistical, or execution decision.

## Exit Criteria

The milestone is complete only when all of the following are true:

- Every required primary method × real-confirmatory-seed cell is completed or has an explicit roadmap-valid state with complete provenance.
- All eligible campaigns and held-out benign horizons are evaluated and primary PFA, strict-ODI, comparator-advantage, operational-lead and support criteria are mechanically evaluable under M04.
- No primary result changes data selection, comparator identity, thresholds, methods, inferential procedure, or materiality gates.
- every mandatory implementation-bearing requirement owned by this milestone is satisfied;
- every applicable conditional requirement is satisfied or resolved to its exact roadmap-defined valid state;
- every mapped implementation issue, once issues exist, is closed;
- all required unit, scientific, integration, end-to-end, and validation tests applicable to this milestone pass;
- all required deliverables are generated and validate;
- all required artifacts, interfaces, schemas, manifests, and provenance records are complete, current, and compatible;
- no required evidence is stale or incompatible with its material dependencies;
- the milestone audit is `PASS`;
- no unresolved blocking finding remains.

## Acceptance Evidence

| Evidence Area | Required Evidence | Pass Condition |
|---|---|---|
| Requirement coverage | Roadmap Coverage Inventory plus milestone ownership audit | Every implementation-bearing requirement is owned exactly once, all relevant constraints remain traceable, and no blocking coverage gap exists |
| Primary cell completeness | Primary method × confirmatory-seed scientific-cell index | Every mandatory cell is current and completed or in an explicitly valid roadmap state |
| Primary evaluation | Campaign/benign-horizon metric artifacts | Complete eligible registry coverage with exact PFA/stopping/ODI/lead/comparator/support outputs |
| Primary support gates | Materiality/PFA/directional-inference evidence using M04 | All six §13.8 support criteria are mechanically evaluable without post-hoc changes |
| Provenance | Required manifests, dependency identity and compatibility evidence | Complete and sufficient to verify origin, compatibility and staleness where applicable |
| Audit | Milestone audit issue | Final result is `PASS` with no unresolved blocking findings |

## Milestone Audit

**Audit issue:** `—`

**Status:** `PENDING`

The milestone audit is the final completion gate. It must independently verify:

- complete roadmap coverage for all requirements owned by the milestone;
- exact requirement-to-issue traceability once implementation issues exist;
- closure of every mandatory implementation issue once issues exist;
- completion and passing status of all required tests and validations;
- existence and validity of all required deliverables;
- completeness and validity of required provenance and manifests;
- absence of stale or incompatible evidence;
- absence of unresolved blocking findings;
- readiness of milestone outputs for all declared downstream consumers.

The audit must end in exactly one result:

- `PASS` — every completion condition is satisfied.
- `FAIL` — one or more blocking conditions remain.

A milestone is not complete until the audit result is `PASS`.

## Scope Boundary

- This milestone is limited to the primary §13.8 evaluation and its predeclared support criteria; later mechanism/boundary studies and final claim/report materialization remain downstream.
- This milestone implements only the roadmap requirements explicitly assigned to it.
- The authoritative roadmap remains the source of scientific, mathematical, methodological, architectural, numerical, configuration, artifact, statistical, and execution requirements.
- This milestone may organize implementation work but may not redefine, weaken, extend, or silently reinterpret the roadmap.
- Detailed implementation checklists belong in implementation issues.
- Detailed verification checklists belong in the milestone audit issue.
- Work outside this milestone's mapped roadmap scope must not be added unless the roadmap or coverage inventory is explicitly updated first.

# M09 — Ablations, Robustness, Generalization & Scalability Boundaries

> **Outcome:** The roadmap's mechanism ablations, robustness challenges, secondary generalization, failure boundaries, dropout/context sparsity, and coalition-scalability studies are completed under their predeclared conditions, inferential rules, and timing constraints.

## At a Glance

| Field | Value |
|---|---|
| Roadmap scope | `§13.9–§13.17; §15; §19.3` |
| Requirement ownership | `REQ-1297–REQ-1441, REQ-1542–REQ-1555, REQ-2382–REQ-2410, REQ-2952, REQ-2963–REQ-2964` |
| Upstream milestones | `M03, M04, M05, M06, M07, M08` |
| Implementation issues | `I43`, `I44`, `I45`, `I46`, `I47`, `I48`, `I49` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | None — no dedicated per-milestone audit issue; verified via `Milestone Audit.md` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every owned implementation-bearing requirement must later map to real implementation issue(s) and objective verification evidence; `NON_IMPLEMENTATION` rows remain scope/claim constraints only.

| Roadmap Section | Scope / Work Package | Requirement IDs | Implementation Issue(s) | Verification / Evidence |
|---|---|---|---|---|
| §13.9–§13.10 | Exclusion, purification and order ablations | `REQ-1297–REQ-1314` | `I43` | Ablation artifacts vary only the declared mechanism and report all required metrics for every configured method/seed. |
| §13.11 | Context and estimator sensitivity | `REQ-1315–REQ-1331, REQ-2952` | `I44` | Sensitivity rows cover the fixed context variants/forced-ridge conditions and preserve declared development-only semantics where applicable. |
| §13.12 | Benign common-mode robustness | `REQ-1332–REQ-1358` | `I45` | Native-high-volume negative and positive-power branches plus declared stresses produce the required suppression/power evidence. |
| §13.13 | Strong local policy challenge | `REQ-1359–REQ-1366` | `I46` | All required real confirmatory seeds compare the declared stronger local policy under exact fixed rules. |
| §13.14 | Secondary controlled-trace generalization | `REQ-1367–REQ-1372` | `I46` | Eligibility manifest plus all-method results when eligible, or exact valid `Not Tested` outcome when ineligible. |
| §13.15 | Outside-campaign contamination boundary | `REQ-1373–REQ-1383` | `I47` | Configured fractions/seeds produce complete boundary metrics and expected conditioning/power diagnostics. |
| §13.16 | Client dropout and context sparsity boundary | `REQ-1384–REQ-1394` | `I47` | Configured unavailable fractions exercise support, abstention and numerical-state rules without forbidden rescue. |
| §13.17; §19.3 | Coalition scalability and common reference timing environment | `REQ-1395–REQ-1441, REQ-2382–REQ-2410, REQ-2963–REQ-2964` | `I48` | K×seed×repetition outputs share one exact environment record and follow warmup/measurement/concurrency/p95 rules. |
| §15 | Predeclared scientific failure and ineligibility boundaries | `REQ-1542–REQ-1555` | `I49` | Fault/ineligibility fixtures assert exact outcome states for estimator failure, unavailable threshold and secondary ineligibility. |

### Coverage Rules

- Every mandatory requirement owned by this milestone must be present in the Roadmap Coverage Inventory.
- Every mandatory implementation-bearing requirement must map to at least one real implementation issue before implementation begins; no hypothetical issue is created in this document.
- Every conditional requirement must remain traceable and must be implemented or resolved exactly when its roadmap-defined condition applies.
- Every mapped requirement must have objective verification or evidence.
- Every implementation issue must reference the exact requirement IDs it satisfies.
- A requirement is not considered covered merely because it falls inside a requirement range or roadmap section assigned to the milestone.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when the corresponding implementation work begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the authoritative roadmap requirement it implements.
- `NON_IMPLEMENTATION` requirements remain traceability/scope constraints only and must not be converted into fictitious implementation tasks.

## Dependencies

### Milestone Dependencies

| Milestone | Required Input / Contract | Entry Gate |
|---|---|---|
| M03 — Scientific Definitions, Generators & Reference Methods | Common-mode, contamination, dropout and other controlled generators/reference methods | `Complete + audit PASS` |
| M04 — Statistical Inference & Decision Contract | Locked statistical procedures, hypothesis families, materiality/equivalence gates, and missing/failed-cell semantics | `Complete + audit PASS` |
| M05 — Dataset Preparation & Local Detection Pipeline | Current primary and conditionally eligible secondary prepared data, local policies, detectors, and score streams | `Complete + audit PASS` |
| M06 — EMHI Estimation, Context Conditioning & Sequential Evidence Engine | Validated estimator, context variants, comparators, metrics and sequential-evidence engine | `Complete + audit PASS` |
| M07 — Synthetic Validation & Comparator Composition Lock | Passing validation gates and fixed selected comparator identity | `Complete + audit PASS` |
| M08 — Primary Real-Data Strict ODI Evaluation | Current primary reference evidence used as the roadmap-ordered baseline for later mechanism/boundary studies | `Complete + audit PASS` |

### Artifact / Interface Dependencies

| Dependency | Produced By | Required Validation |
|---|---|---|
| Controlled generators/reference methods | M03 | Relevant generator/reference fixtures pass |
| Statistical inference/decision contract | M04 | Applicable tests, intervals, families and cell-state semantics validate |
| Primary/secondary prepared data and score artifacts | M05 | Current eligibility/provenance validation passes |
| EMHI/comparator/metric engine | M06 | Scientific validation passes |
| Comparator-lock and validation artifacts | M07 | Current and prerequisite-valid |
| Primary real-data evidence | M08 | Complete, current and provenance-compatible |

Dependency completion alone is not sufficient. Every consumed dependency must be present, valid, provenance-compatible where applicable, and compatible with the active roadmap contract.

## Implementation Issues

Implementation issues for this milestone are listed below; each issue's detailed task checklist, acceptance criteria, and required tests are defined in `Issues.md`.

| Order | Issue | Work Package | Roadmap Scope | Requirement Coverage | Depends On |
|---:|---|---|---|---|---|
| 1 | `I43` — Execute Exclusion, Purification and Order Ablations | Execute Exclusion, Purification and Order Ablations | §13.9–§13.10 | 18 atomic requirements | `I31`, `I32`, `I42` |
| 2 | `I44` — Execute Context and Estimator Sensitivity Analysis | Execute Context and Estimator Sensitivity Analysis | §13.11 | 18 atomic requirements | `I31`, `I40`, `I42` |
| 3 | `I45` — Evaluate Benign Common-Mode Robustness | Evaluate Benign Common-Mode Robustness | §13.12 | 27 atomic requirements | `I33`, `I42` |
| 4 | `I46` — Execute Strong-Local Challenge and Secondary Controlled-Trace Generalization | Execute Strong-Local Challenge and Secondary Controlled-Trace Generalization | §13.13; §13.14 | 14 atomic requirements | `I25`, `I40`, `I42` |
| 5 | `I47` — Evaluate Outside-Contamination and Client-Dropout Boundaries | Evaluate Outside-Contamination and Client-Dropout Boundaries | §13.15; §13.16 | 22 atomic requirements | `I31`, `I40`, `I42` |
| 6 | `I48` — Evaluate Coalition Scalability in the Common Reference Timing Environment | Evaluate Coalition Scalability in the Common Reference Timing Environment | §13.17; §19.3 | 78 atomic requirements | `I12`, `I33`, `I42` |
| 7 | `I49` — Enforce Scientific Failure, Ineligibility and Downscope Boundaries | Enforce Scientific Failure, Ineligibility and Downscope Boundaries | §15 | 14 atomic requirements | `I20`, `I43`, `I44`, `I45`, `I46`, `I47`, `I48` |

### Issue Contract

Every future milestone issue must:

- reference its exact roadmap section(s);
- list every covered requirement ID;
- contain a detailed implementation checklist;
- define objective acceptance criteria;
- identify required tests;
- identify required artifacts, outputs, or interfaces;
- identify required provenance or manifest updates where applicable;
- identify explicit dependencies on upstream milestones, issues, artifacts, or interfaces;
- preserve roadmap terminology and semantics;
- close only when every mapped implementation-bearing requirement and acceptance criterion is satisfied.

## Deliverables

| Deliverable | Source Issue(s) | Required Validation | Downstream Consumer |
|---|---|---|---|
| Exclusion/purification/order ablation and context/estimator sensitivity results | `I43`, `I44`, `I45`, `I46`, `I47`, `I48`, `I49` | All configured methods/conditions execute under exact ablation semantics and produce current metric/statistical artifacts | M10 |
| Benign common-mode robustness and strong-local challenge results | `I43`, `I44`, `I45`, `I46`, `I47`, `I48`, `I49` | Required negative/positive branches and strong-local comparator conditions complete under confirmatory statistical obligations | M10 |
| Secondary controlled-trace generalization result or valid `Not Tested` outcome | `I43`, `I44`, `I45`, `I46`, `I47`, `I48`, `I49` | Secondary eligibility is resolved strictly from raw-data rules and all eligible methods complete when applicable | M10 |
| Outside-contamination and client-dropout/context-sparsity boundary evidence | `I43`, `I44`, `I45`, `I46`, `I47`, `I48`, `I49` | Configured boundary grids and expected support/abstention semantics are recorded without post-hoc rescue | M10 |
| Coalition-scalability and reference-harness timing evidence | `I43`, `I44`, `I45`, `I46`, `I47`, `I48`, `I49` | All required K/timing repetitions share one validated environment identity and produce latency/throughput/payload evidence | M10 |
| Failure/ineligibility boundary records | `I43`, `I44`, `I45`, `I46`, `I47`, `I48`, `I49` | Order-3 failure, unavailable real calibrated threshold, and secondary-data ineligibility follow the exact predeclared outcome semantics | M10 |

All roadmap-required deliverables for this milestone must appear in this table or be explicitly traceable through the Roadmap Coverage Inventory.

## Entry Criteria

Implementation may begin only when all of the following are true:

- M03–M08 are complete and audited as listed in the dependency table.
- Primary evidence is complete before roadmap-ordered ablation/robustness/generalization/scalability work is used for downstream synthesis.
- All conditional secondary-data and boundary-study eligibility decisions are made from predeclared input conditions, never from favorable outcomes.
- all required upstream milestones are complete;
- every required upstream milestone audit is `PASS`;
- every required upstream artifact, interface, schema, or manifest exists;
- every consumed dependency passes its applicable validation;
- consumed evidence is provenance-compatible and not stale where provenance applies;
- all roadmap requirements owned by this milestone are present in the Roadmap Coverage Inventory;
- every implementation-bearing requirement has an explicit verification/evidence target;
- no blocking requirement is `AMBIGUOUS` or `BLOCKED`;
- no unresolved roadmap ambiguity would force the implementer to invent a scientific, mathematical, methodological, numerical, architectural, configuration, artifact, statistical, or execution decision.

## Exit Criteria

The milestone is complete only when all of the following are true:

- Every required ablation, robustness, strong-local, conditional secondary, contamination, dropout/context-sparsity and scalability/timing study completes or records the exact valid ineligibility/`Not Tested` state.
- All statistical decisions required inside these studies use M04 unchanged, including fixed Holm-family participation where applicable.
- Timing/scalability measurements share the roadmap-defined environment identity, warmup/repetition/concurrency and reporting semantics.
- every mandatory implementation-bearing requirement owned by this milestone is satisfied;
- every applicable conditional requirement is satisfied or resolved to its exact roadmap-defined valid state;
- every mapped implementation issue, once issues exist, is closed;
- all required unit, scientific, integration, end-to-end, and validation tests applicable to this milestone pass;
- all required deliverables are generated and validate;
- all required artifacts, interfaces, schemas, manifests, and provenance records are complete, current, and compatible;
- no required evidence is stale or incompatible with its material dependencies;
- the milestone audit is `PASS`;
- no unresolved blocking finding remains.

## Acceptance Evidence

| Evidence Area | Required Evidence | Pass Condition |
|---|---|---|
| Requirement coverage | Roadmap Coverage Inventory plus milestone ownership audit | Every implementation-bearing requirement is owned exactly once, all relevant constraints remain traceable, and no blocking coverage gap exists |
| Mechanism and sensitivity studies | Ablation/context/estimator result matrices | Every configured contrast varies only the declared mechanism and uses fixed statistical semantics |
| Robustness/generalization | Common-mode, strong-local, secondary, contamination and dropout/context artifacts | All applicable cells complete or use exact valid `Not Tested`/ineligible outcomes |
| Scalability/timing | K × seed × repetition artifacts plus environment record | Warmup, measurement, concurrency, p95, throughput/payload and environment identity rules pass |
| Failure boundaries | Fault/ineligibility artifacts | Estimator failure, unavailable thresholds and secondary ineligibility follow exact scientific/technical states |
| Provenance | Required manifests, dependency identity and compatibility evidence | Complete and sufficient to verify origin, compatibility and staleness where applicable |
| Audit | Milestone audit issue | Final result is `PASS` with no unresolved blocking findings |

## Milestone Audit

**Audit issue:** `—`

**Status:** `PENDING`

The milestone audit is the final completion gate. It must independently verify:

- complete roadmap coverage for all requirements owned by the milestone;
- exact requirement-to-issue traceability once implementation issues exist;
- closure of every mandatory implementation issue once issues exist;
- completion and passing status of all required tests and validations;
- existence and validity of all required deliverables;
- completeness and validity of required provenance and manifests;
- absence of stale or incompatible evidence;
- absence of unresolved blocking findings;
- readiness of milestone outputs for all declared downstream consumers.

The audit must end in exactly one result:

- `PASS` — every completion condition is satisfied.
- `FAIL` — one or more blocking conditions remain.

A milestone is not complete until the audit result is `PASS`.

## Scope Boundary

- This milestone does not reopen the primary comparator lock, primary data/client selection, inferential procedures, or scientific configuration; it only executes the predeclared later study families and boundaries.
- This milestone implements only the roadmap requirements explicitly assigned to it.
- The authoritative roadmap remains the source of scientific, mathematical, methodological, architectural, numerical, configuration, artifact, statistical, and execution requirements.
- This milestone may organize implementation work but may not redefine, weaken, extend, or silently reinterpret the roadmap.
- Detailed implementation checklists belong in implementation issues.
- Detailed verification checklists belong in the milestone audit issue.
- Work outside this milestone's mapped roadmap scope must not be added unless the roadmap or coverage inventory is explicitly updated first.

# M10 — Confirmatory Evidence Synthesis, Claim Registry & Reporting

> **Outcome:** All current confirmatory evidence is synthesized through the locked statistical contract and materialized into source-backed tables, figures, project summaries, reproducibility exports, and mechanically bounded claim states without new scientific computation.

## At a Glance

| Field | Value |
|---|---|
| Roadmap scope | `Claim/novelty constraints from §§2–3; §16.7 report; §18.7–§18.8; §19.4; §§20–21; claim-boundary clarifications` |
| Requirement ownership | `REQ-0001–REQ-0003, REQ-0005–REQ-0006, REQ-0066–REQ-0104, REQ-1953–REQ-1957, REQ-1964, REQ-2313–REQ-2349, REQ-2411–REQ-2799, REQ-2899, REQ-2912, REQ-2957–REQ-2958` |
| Upstream milestones | `M01, M02, M04, M07, M08, M09` |
| Implementation issues | `I50`, `I51`, `I52`, `I53`, `I54`, `I55` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | None — no dedicated per-milestone audit issue; verified via `Milestone Audit.md` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every owned implementation-bearing requirement must later map to real implementation issue(s) and objective verification evidence; `NON_IMPLEMENTATION` rows remain scope/claim constraints only.

| Roadmap Section | Scope / Work Package | Requirement IDs | Implementation Issue(s) | Verification / Evidence |
|---|---|---|---|---|
| Authority; §§2–3; claim-boundary clarifications | Claim identity, novelty limits, research questions and forbidden extrapolations | `REQ-0001–REQ-0003, REQ-0005–REQ-0006, REQ-0066–REQ-0104, REQ-2786, REQ-2795, REQ-2798–REQ-2799, REQ-2899, REQ-2912, REQ-2957–REQ-2958` | `I50` | Roadmap-to-claim/manuscript traceability audit verifies exact terminology, novelty boundaries and every prohibited extrapolation. |
| §16.7; §16.8 report row | Report CLI verified-evidence materialization | `REQ-1953–REQ-1957, REQ-1964` | `I51` | CLI integration tests prove `report` performs no new scientific/statistical computation and reads only current verified artifacts. |
| §18.7–§18.8 | Figure/table source, claim-registry and reproducibility export artifacts | `REQ-2313–REQ-2349` | `I51` | Schema/provenance tests validate source-data lineage, claim/report manifests, exports and staleness behavior. |
| §19.4 | Confirmatory statistical synthesis completeness | `REQ-2411–REQ-2420` | `I52` | Completeness validation proves all mandatory current cells, pairing families, intervals, decision gates, and confirmatory-analysis inputs are present before claim/report materialization. |
| §20.1–§20.5 | Source-data, dataset-role, protocol, detector and baseline tables | `REQ-2421–REQ-2488` | `I53` | Table-contract tests assert exact source paths/columns/roles/precision and trace every value to current machine-readable artifacts. |
| §20.6–§20.10 | Experiment result tables and machine-readable source data | `REQ-2489–REQ-2654` | `I53` | Per-experiment table/source-data validators cover every required result family and reject stale/incomplete inputs. |
| §20.11–§20.18 | Manuscript figure contracts and source data | `REQ-2655–REQ-2709` | `I54` | Figure validators assert exact x/y/series/source-data contracts, labels and reproducibility from machine-readable sources. |
| §20.19 | Project-summary evidence | `REQ-2710–REQ-2718` | `I54` | Cross-experiment summary validator confirms all project-level metrics/statistics/source-data/reproducibility inputs are verified and current. |
| §21 | Mechanical claim and evidence registry | `REQ-2719–REQ-2785, REQ-2787–REQ-2794, REQ-2796–REQ-2797` | `I55` | Claim-engine tests evaluate every claim state mechanically from exact prerequisites, gates, eligibility and downscoping rules. |

### Coverage Rules

- Every mandatory requirement owned by this milestone must be present in the Roadmap Coverage Inventory.
- Every mandatory implementation-bearing requirement must map to at least one real implementation issue before implementation begins; no hypothetical issue is created in this document.
- Every conditional requirement must remain traceable and must be implemented or resolved exactly when its roadmap-defined condition applies.
- Every mapped requirement must have objective verification or evidence.
- Every implementation issue must reference the exact requirement IDs it satisfies.
- A requirement is not considered covered merely because it falls inside a requirement range or roadmap section assigned to the milestone.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when the corresponding implementation work begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the authoritative roadmap requirement it implements.
- `NON_IMPLEMENTATION` requirements remain traceability/scope constraints only and must not be converted into fictitious implementation tasks.

## Dependencies

### Milestone Dependencies

| Milestone | Required Input / Contract | Entry Gate |
|---|---|---|
| M01 — Scientific Configuration & Repository Contract | Locked reporting precision, claim/materiality configuration, canonical output/result paths | `Complete + audit PASS` |
| M02 — Artifact Runtime, Provenance & Execution Orchestration | Current verified-evidence boundary, claim/report artifact schemas, dependency identity and staleness checks | `Complete + audit PASS` |
| M04 — Statistical Inference & Decision Contract | Validated inferential procedures, hypothesis families, materiality/equivalence rules, and completeness semantics | `Complete + audit PASS` |
| M07 — Synthetic Validation & Comparator Composition Lock | Validated synthetic/equivalence/feasibility/sequential source evidence | `Complete + audit PASS` |
| M08 — Primary Real-Data Strict ODI Evaluation | Complete current primary real confirmatory evidence | `Complete + audit PASS` |
| M09 — Ablations, Robustness, Generalization & Scalability Boundaries | Complete applicable secondary confirmatory and boundary evidence | `Complete + audit PASS` |

### Artifact / Interface Dependencies

| Dependency | Produced By | Required Validation |
|---|---|---|
| Verified scientific/statistical evidence graph | M02 | Only current verified artifacts are admitted; stale/incompatible evidence rejected |
| Statistical inference/decision contract | M04 | All synthesis procedures/families/gates mechanically validate |
| Synthetic validation and comparator-lock evidence | M07 | Current and provenance-compatible |
| Primary real-data evidence | M08 | Complete current confirmatory source artifacts |
| Ablation/robustness/generalization/scalability evidence | M09 | Complete applicable source artifacts or valid roadmap-defined `Not Tested` states |

Dependency completion alone is not sufficient. Every consumed dependency must be present, valid, provenance-compatible where applicable, and compatible with the active roadmap contract.

## Implementation Issues

Implementation issues for this milestone are listed below; each issue's detailed task checklist, acceptance criteria, and required tests are defined in `Issues.md`.

| Order | Issue | Work Package | Roadmap Scope | Requirement Coverage | Depends On |
|---:|---|---|---|---|---|
| 1 | `I50` — Materialize Claim Identity, Novelty Boundaries and Research-Question Constraints | Materialize Claim Identity, Novelty Boundaries and Research-Question Constraints | Authority; §§2–3; claim-boundary clarifications | 52 atomic requirements | `I49` |
| 2 | `I51` — Implement Verified-Evidence Reporting and Reproducibility Exports | Implement Verified-Evidence Reporting and Reproducibility Exports | §16.7; §16.8 report row; §18.7–§18.8 | 43 atomic requirements | `I06`, `I12`, `I49` |
| 3 | `I52` — Perform Confirmatory Statistical Synthesis | Perform Confirmatory Statistical Synthesis | §19.4 | 10 atomic requirements | `I12`, `I20`, `I49` |
| 4 | `I53` — Materialize Dataset, Protocol, Detector, Baseline and Experiment Result Tables | Materialize Dataset, Protocol, Detector, Baseline and Experiment Result Tables | §20.1–§20.5; §20.6–§20.10 | 234 atomic requirements | `I49`, `I51`, `I52` |
| 5 | `I54` — Materialize Manuscript Figures and Project-Summary Evidence | Materialize Manuscript Figures and Project-Summary Evidence | §20.11–§20.18; §20.19 | 64 atomic requirements | `I51`, `I53` |
| 6 | `I55` — Materialize the Mechanical Claim and Evidence Registry | Materialize the Mechanical Claim and Evidence Registry | §21 | 77 atomic requirements | `I50`, `I52`, `I53`, `I54` |

### Issue Contract

Every future milestone issue must:

- reference its exact roadmap section(s);
- list every covered requirement ID;
- contain a detailed implementation checklist;
- define objective acceptance criteria;
- identify required tests;
- identify required artifacts, outputs, or interfaces;
- identify required provenance or manifest updates where applicable;
- identify explicit dependencies on upstream milestones, issues, artifacts, or interfaces;
- preserve roadmap terminology and semantics;
- close only when every mapped implementation-bearing requirement and acceptance criterion is satisfied.

## Deliverables

| Deliverable | Source Issue(s) | Required Validation | Downstream Consumer |
|---|---|---|---|
| Confirmatory statistical synthesis completeness manifest | `I50`, `I51`, `I52`, `I53`, `I54`, `I55` | All mandatory current cells, pairings, intervals, hypothesis families, materiality/equivalence gates and valid `Not Tested` states are complete before claim materialization | Claim registry and manuscript evidence |
| Verified-evidence report command outputs | `I50`, `I51`, `I52`, `I53`, `I54`, `I55` | `report` materializes only current machine-readable evidence and performs no new scientific/statistical computation | Manuscript evidence |
| Required source-data, dataset/evidence-role, protocol, detector, baseline, experiment-result and boundary tables | `I50`, `I51`, `I52`, `I53`, `I54`, `I55` | Table schemas, required columns, source paths, precision and provenance checks pass | Manuscript evidence |
| Required manuscript figures and figure source data | `I50`, `I51`, `I52`, `I53`, `I54`, `I55` | Figure-contract, source-data, axis/metric and provenance checks pass | Manuscript evidence |
| Project-summary metrics/statistics/source-data/reproducibility package | `I50`, `I51`, `I52`, `I53`, `I54`, `I55` | Cross-experiment synthesis reads only verified current artifacts and exposes configuration/data/software/seed/execution provenance | Manuscript evidence / reproducibility |
| Mechanical claim and evidence registry | `I50`, `I51`, `I52`, `I53`, `I54`, `I55` | Every claim state is computed from the exact prerequisite evidence and forbidden/downscoped boundaries are enforced | Manuscript |
| Claim-boundary compliance evidence | `I50`, `I51`, `I52`, `I53`, `I54`, `I55` | Novelty limits, forbidden extrapolations, research-question scope and literature-adaptation boundaries are traceable without creating fictitious implementation work | Manuscript |

All roadmap-required deliverables for this milestone must appear in this table or be explicitly traceable through the Roadmap Coverage Inventory.

## Entry Criteria

Implementation may begin only when all of the following are true:

- M01, M02, M04, M07, M08 and M09 are complete and audited.
- All source scientific/statistical artifacts admitted to synthesis are current, verified, provenance-compatible and complete under §19.4.
- Claim-boundary and `NON_IMPLEMENTATION` requirements are treated as reporting/scope constraints and never converted into fictitious scientific implementation tasks.
- all required upstream milestones are complete;
- every required upstream milestone audit is `PASS`;
- every required upstream artifact, interface, schema, or manifest exists;
- every consumed dependency passes its applicable validation;
- consumed evidence is provenance-compatible and not stale where provenance applies;
- all roadmap requirements owned by this milestone are present in the Roadmap Coverage Inventory;
- every implementation-bearing requirement has an explicit verification/evidence target;
- no blocking requirement is `AMBIGUOUS` or `BLOCKED`;
- no unresolved roadmap ambiguity would force the implementer to invent a scientific, mathematical, methodological, numerical, architectural, configuration, artifact, statistical, or execution decision.

## Exit Criteria

The milestone is complete only when all of the following are true:

- §19.4 completeness validation proves zero missing mandatory confirmatory evidence, valid current provenance, complete pairing/families/intervals/gates, and only roadmap-valid `Not Tested` states.
- `report` reads only verified current artifacts and performs no new scientific/statistical computation.
- Every required table, figure, machine-readable source artifact, project summary, reproducibility export and claim-registry state is reproducible from exact current sources.
- Every claim obeys the roadmap's novelty/scope/forbidden-extrapolation constraints and automatically downscopes or becomes unsupported/not-tested when prerequisite evidence fails.
- every mandatory implementation-bearing requirement owned by this milestone is satisfied;
- every applicable conditional requirement is satisfied or resolved to its exact roadmap-defined valid state;
- every mapped implementation issue, once issues exist, is closed;
- all required unit, scientific, integration, end-to-end, and validation tests applicable to this milestone pass;
- all required deliverables are generated and validate;
- all required artifacts, interfaces, schemas, manifests, and provenance records are complete, current, and compatible;
- no required evidence is stale or incompatible with its material dependencies;
- the milestone audit is `PASS`;
- no unresolved blocking finding remains.

## Acceptance Evidence

| Evidence Area | Required Evidence | Pass Condition |
|---|---|---|
| Requirement coverage | Roadmap Coverage Inventory plus milestone ownership audit | Every implementation-bearing requirement is owned exactly once, all relevant constraints remain traceable, and no blocking coverage gap exists |
| Synthesis completeness | §19.4 completeness manifest over all current source artifacts | All mandatory cells, pairings, families, intervals, gates and provenance inputs are present before claim materialization |
| Reporting source integrity | Table/figure source artifacts and report CLI tests | Every rendered value is reproducible from exactly one current machine-readable source and no diagnostic/console/manual values enter evidence |
| Claim registry | Mechanical claim-state fixtures and current project claim artifact | Every claim state follows exact prerequisites, statistical/materiality gates and scope/downscoping rules |
| Reproducibility | Project-summary reproducibility export | Configuration, dataset, seed, software, execution, dependency and source-artifact identities are complete and current |
| Claim boundaries | Roadmap-to-claim/manuscript traceability audit | All `NON_IMPLEMENTATION` novelty/exclusion/scope constraints are preserved and no forbidden extrapolation is emitted |
| Provenance | Required manifests, dependency identity and compatibility evidence | Complete and sufficient to verify origin, compatibility and staleness where applicable |
| Audit | Milestone audit issue | Final result is `PASS` with no unresolved blocking findings |

## Milestone Audit

**Audit issue:** `—`

**Status:** `PENDING`

The milestone audit is the final completion gate. It must independently verify:

- complete roadmap coverage for all requirements owned by the milestone;
- exact requirement-to-issue traceability once implementation issues exist;
- closure of every mandatory implementation issue once issues exist;
- completion and passing status of all required tests and validations;
- existence and validity of all required deliverables;
- completeness and validity of required provenance and manifests;
- absence of stale or incompatible evidence;
- absence of unresolved blocking findings;
- readiness of milestone outputs for all declared downstream consumers.

The audit must end in exactly one result:

- `PASS` — every completion condition is satisfied.
- `FAIL` — one or more blocking conditions remain.

A milestone is not complete until the audit result is `PASS`.

## Scope Boundary

- This milestone synthesizes/reports existing verified evidence only; it must not create new scientific cells, alter thresholds/comparators/statistical procedures, rerun or invent missing scientific evidence, or broaden permitted claims.
- `NON_IMPLEMENTATION` requirements are traceability/scope constraints here, not fictitious implementation work.
- This milestone implements only the roadmap requirements explicitly assigned to it.
- The authoritative roadmap remains the source of scientific, mathematical, methodological, architectural, numerical, configuration, artifact, statistical, and execution requirements.
- This milestone may organize implementation work but may not redefine, weaken, extend, or silently reinterpret the roadmap.
- Detailed implementation checklists belong in implementation issues.
- Detailed verification checklists belong in the milestone audit issue.
- Work outside this milestone's mapped roadmap scope must not be added unless the roadmap or coverage inventory is explicitly updated first.
