# FedCampaign-EMHI — Pre-Experiment Audit Matrix
**Scope:** verification gate before any claim-bearing experiment execution.
**Scientific basis:** `Roadmap(3).md` plus established repository engineering rules for strong typing, enums, primitive-leak prevention, duplication control, Graphify wiring, and code hygiene.
**Target:** exactly **250** requirements.
## Execution boundary
- **Permitted:** repository/static inspection, fresh Graphify analysis, architecture/static/type tests, normal test suite, `fedcampaign doctor`, real `fedcampaign preprocess`, `fedcampaign smoke`, `fedcampaign plan`, `fedcampaign status`, `fedcampaign report` behavior checks, and roadmap-defined `fedcampaign run <experiment-name> --dry-run`.
- **Forbidden:** every non-dry `fedcampaign run <experiment-name>` invocation and any other path that executes claim-bearing development or confirmatory experiment cells.
- `smoke` is permitted because the roadmap explicitly defines it as the short Synthetic Module Validation workflow and makes it part of pre-run readiness.
- Do not invent CLI options. Use only options actually present in the repository/roadmap.
- File-tree/module-name differences are not defects by themselves. Science, dependency boundaries, typed interfaces, wiring, artifact semantics, and execution behavior are the audit targets.

## Status vocabulary
Use one of: `TODO`, `PASS`, `FAIL`, `PARTIAL`, `UNWIRED`, `MISSING`, `JUSTIFIED_EMPIRICAL_DEVIATION`, `JUSTIFIED_ARCHITECTURE_DEVIATION`, `BLOCKED_PRE_EXPERIMENT`, `NOT_APPLICABLE`.

## Summary
| Domain | Count |
|---|---:|
| A. Scientific authority and configuration | 12 |
| B. Dataset authority, inventory, and empirical amendments | 16 |
| C. Preprocessing, chronology, partitions, and leakage | 24 |
| D. Core mathematical implementation | 36 |
| E. Detector, local-policy, stopping, and replay contracts | 10 |
| F. Baseline and comparator contracts | 21 |
| G. Metric registry and scoring semantics | 37 |
| H. Experiment contracts — static/dry-run verification only | 18 |
| I. Statistical analysis protocol | 16 |
| J. CLI, Graphify, workflow reachability, and callable accounting | 20 |
| K. Artifact identity, caching, provenance, outputs, and reporting | 12 |
| L. Types, enums, primitive-leak prevention, and domain modeling | 12 |
| M. Duplication, defaults, paths, dead code, libraries, and code hygiene | 8 |
| N. Tests, short commands, and final pre-experiment readiness gate | 8 |
| **Total** | **250** |

## Matrix

### A. Scientific authority and configuration

| ID | Requirement | Verification / expected evidence | Severity | Status | Evidence / notes |
|---|---|---|---|---|---|
| SCI-001 | The roadmap is treated as the scientific contract for formulas, data semantics, experiment definitions, metrics, statistics, failure/downscope rules, and evidence lineage; implementation layout is not required to mirror roadmap prose or module names. | R §§1–5, 16; verify deviations are classified by scientific effect, not filename/tree similarity. | BLOCKER | TODO |  |
| SCI-002 | Observed raw-data facts may supersede untested roadmap expectations only through an explicit evidence-backed empirical amendment; no scientific rule may be silently relaxed to fit observed data. | R protocol amendments + §6.1; inspect adaptation logic and provenance records. | BLOCKER | TODO |  |
| SCI-003 | The authoritative production scientific configuration is singular and resolved consistently; test/smoke configuration cannot alter production scientific semantics. | R Configuration YAML; inspect config loading and environment/CLI override paths. | BLOCKER | TODO |  |
| SCI-004 | Public CLI exposes execution controls only; no CLI/environment argument can override locked scientific settings. | R §16 public interface; inspect Typer/Click/argparse options and environment reads. | BLOCKER | TODO |  |
| SCI-005 | Every configured primary-study value is consumed exactly once through the intended configuration/domain layer and is not shadowed by a Python default or duplicate constant. | R Configuration YAML; static search + call-site audit. | BLOCKER | TODO |  |
| SCI-006 | Derived values are computed from their declared primitive inputs rather than independently configured or hardcoded. | R Configuration YAML derivation rules; inspect derived-value constructors/functions. | BLOCKER | TODO |  |
| SCI-007 | Fixed algorithmic rules remain code-level scientific rules and are not exposed as post-hoc tunable configuration. | R §4 + Configuration YAML preamble; compare config schema with roadmap. | BLOCKER | TODO |  |
| SCI-008 | Development and confirmatory seed namespaces are disjoint and their ownership is enforced by experiment contracts. | R randomness config + §§13–14, 19; inspect seed resolution. | BLOCKER | TODO |  |
| SCI-009 | Scientific random substreams are deterministically derived from canonical identities and do not depend on iteration order, Python hash randomization, wall time, or process scheduling. | R canonical serialization/seed derivation; inspect RNG helpers and tests. | BLOCKER | TODO |  |
| SCI-010 | Maximum implemented coalition order is taken from the authoritative study setting and all order-dependent logic derives its enabled order set from it. | R study.maximum_coalition_order + §§4,13; trace order enumeration. | BLOCKER | TODO |  |
| SCI-011 | Numerical tolerances, floors, cutoffs, and comparison tolerances are centralized according to roadmap ownership and are not inconsistently redefined at call sites. | R projection/evidence/numerics config; search numeric constants and aliases. | MAJOR | TODO |  |
| SCI-012 | Repository/file-tree differences from the roadmap do not fail the audit by themselves; only broken responsibility boundaries, missing science, missing wiring, or incompatible artifact semantics are defects. | R §16 package-topology flexibility; audit architecture semantics separately from filenames. | MAJOR | TODO |  |

### B. Dataset authority, inventory, and empirical amendments

| ID | Requirement | Verification / expected evidence | Severity | Status | Evidence / notes |
|---|---|---|---|---|---|
| DATA-001 | Raw dataset discovery uses the configured immutable raw-data source and does not silently fall back to copies, generated samples, or alternate releases. | R §6 + §18.3; run inventory through preprocess/doctor and inspect resolved paths. | BLOCKER | TODO |  |
| DATA-002 | Raw files are inventoried with stable source identity, SHA-256, byte size, and applicable record/time metadata before downstream preprocessing. | R §18.3 dataset inventory fields; inspect produced inventory. | BLOCKER | TODO |  |
| DATA-003 | Documented expected structure and observed raw structure are recorded separately; discrepancies are surfaced rather than normalized away silently. | R §6.1; inspect validation/discrepancy artifacts. | BLOCKER | TODO |  |
| DATA-004 | Raw-dataset adaptation changes only parsing/structural accommodation and cannot weaken eligibility, split, campaign, label, or scientific protocol rules. | R §6.1 adaptation rule; inspect adapters and config. | BLOCKER | TODO |  |
| DATA-005 | TON_IoT Network raw identity resolves to the intended configured release and files, with no accidental use of a different TON_IoT modality/release. | R §6.2 Raw identity; inventory evidence. | BLOCKER | TODO |  |
| DATA-006 | TON_IoT client identity is constructed exactly from the roadmap-defined client field and normalization semantics. | R §6.2 Client definition; inspect canonical client mapping. | BLOCKER | TODO |  |
| DATA-007 | TON_IoT eligibility ranking is benign-only and deterministic, and preserves the declared ordering/tie rules. | R §6.2 Primary client selection; inspect ranking implementation and output. | BLOCKER | TODO |  |
| DATA-008 | The primary TON_IoT cohort target is four clients under Protocol amendment 1, not the superseded twelve-client target. | R Protocol amendment 1; config + selected-client manifest. | BLOCKER | TODO |  |
| DATA-009 | The selected four-client cohort is the largest leading ranked cohort with adequate common benign support for every required benign partition. | R Protocol amendment 1; recompute support from prepared metadata. | BLOCKER | TODO |  |
| DATA-010 | Artifacts produced under the superseded twelve-client material identity cannot be reused as evidence for the amended four-client protocol. | R Protocol amendment 1 + §§17–18; dependency fingerprint audit. | BLOCKER | TODO |  |
| DATA-011 | TON_IoT benign/evaluation separation follows the roadmap and attack/campaign labels never contaminate benign fitting/calibration partitions. | R §6.2 Benign/evaluation separation; split audit. | BLOCKER | TODO |  |
| DATA-012 | TON_IoT ground-truth semantics and campaign/event labels are preserved exactly and discrepancies are counted explicitly. | R §6.2 Ground-truth semantics + §18.3. | BLOCKER | TODO |  |
| DATA-013 | Edge-IIoTset raw identity resolves to the configured controlled-trace release rather than an alternate prepared CSV or synthetic substitute. | R §6.3 Raw identity; inventory evidence. | BLOCKER | TODO |  |
| DATA-014 | Edge-IIoTset clients are formed from the roadmap-defined source-host identity without fabricating pseudo-clients. | R §6.3 Secondary client definition; inspect client map. | BLOCKER | TODO |  |
| DATA-015 | The observed eligible Edge-IIoTset source hosts are validated from raw/preprocessed data; the known release finding of two eligible hosts is reproduced or explicitly evidenced if the raw release has materially changed. | R Protocol amendment 2; preprocessing eligibility output. | BLOCKER | TODO |  |
| DATA-016 | If the secondary release remains below the six-client minimum, the secondary experiment is Not Tested; eligibility is not relaxed, clients are not fabricated, and no substitute dataset is selected. | R Protocol amendment 2 + §15.3 + §16.9. | BLOCKER | TODO |  |

### C. Preprocessing, chronology, partitions, and leakage

| ID | Requirement | Verification / expected evidence | Severity | Status | Evidence / notes |
|---|---|---|---|---|---|
| PRE-001 | Duplicate handling follows the roadmap-defined duplicate key/scope and records duplicate counts without accidentally removing scientifically distinct events. | R §7.1; inspect deduplication implementation + preprocessing validation. | BLOCKER | TODO |  |
| PRE-002 | Invalid-record handling follows the declared exclusion rules and records excluded counts/reasons; malformed records are not silently coerced into valid observations. | R §7.2; inspect validators and manifest counts. | BLOCKER | TODO |  |
| PRE-003 | Timestamp parsing and UTC normalization use the declared dataset-specific semantics and do not rely on locale/system timezone defaults. | R timestamp/epoch configuration + §7. | BLOCKER | TODO |  |
| PRE-004 | Epoch assignment uses the authoritative epoch duration and deterministic boundary convention. | R time.real_data_epoch_seconds + timestamp/epoch config; fixture/boundary tests. | BLOCKER | TODO |  |
| PRE-005 | Event canonicalization follows the dataset-specific canonical event mapping before hashing/feature construction. | R Event canonicalization; inspect TON/Edge adapters. | BLOCKER | TODO |  |
| PRE-006 | Event-type hash mapping uses the declared deterministic hash/canonical serialization rule and bucket count. | R Hash mapping + preprocessing config; deterministic fixture. | BLOCKER | TODO |  |
| PRE-007 | Epoch feature vectors contain exactly the roadmap-defined event-bucket/count/entropy features in the correct order and dimension. | R §7.3 + preprocessing config; inspect feature schema artifact. | BLOCKER | TODO |  |
| PRE-008 | Feature dimension is derived from configuration/formula, not duplicated as an unrelated literal. | R §7.3 + §13.17 d derivation; static search + schema assertion. | MAJOR | TODO |  |
| PRE-009 | Non-finite raw/derived feature values are handled exactly as specified and counted; no NaN/Inf reaches detector fitting silently. | R §7.4; validation artifacts + tests. | BLOCKER | TODO |  |
| PRE-010 | Robust local scaling is fit only on the permitted client-local benign detector-fit data and never on future/calibration/held-out/campaign rows. | R §7.5–7.6; fit-source tracing. | BLOCKER | TODO |  |
| PRE-011 | Scaling parameters remain client-local where required and are reused consistently across that client’s later partitions. | R §7.5; artifact identity + transform call sites. | BLOCKER | TODO |  |
| PRE-012 | Chronological order is preserved before constructing detector-fit, nuisance-fit, threshold-calibration, and held-out partitions. | R §7.6; split manifest + monotonicity checks. | BLOCKER | TODO |  |
| PRE-013 | Detector-fit benign partition boundaries are exact, deterministic, and non-overlapping with every later benign partition. | R §7.6; split interval audit. | BLOCKER | TODO |  |
| PRE-014 | Nuisance-fit benign partition boundaries are exact and do not overlap detector-fit, threshold-calibration, or held-out intervals. | R §7.6; split interval audit. | BLOCKER | TODO |  |
| PRE-015 | Threshold-calibration benign partition is independent of nuisance fitting and held-out evaluation. | R §§4.9, 7.6; interval/source audit. | BLOCKER | TODO |  |
| PRE-016 | Held-out benign partition is never used to fit detectors, contexts, projections, atom scaling, local policies, or global thresholds. | R §§4.9, 4.18, 7.6; dependency trace. | BLOCKER | TODO |  |
| PRE-017 | Client eligibility checks use the roadmap-defined minimum support for every required partition and do not downscale requirements automatically. | R §7.6 Eligibility checks; recompute from manifests. | BLOCKER | TODO |  |
| PRE-018 | Common benign support across selected primary clients is validated before final cohort acceptance. | R Protocol amendment 1 + §7.6; preprocessing validation. | BLOCKER | TODO |  |
| PRE-019 | Benign finite-horizon calibration windows are constructed as non-overlapping windows of the configured evaluation horizon. | R §7.7 + §4.18; horizon manifest audit. | BLOCKER | TODO |  |
| PRE-020 | Held-out benign horizons used for PFA evaluation are non-overlapping and disjoint from calibration horizons. | R §7.7 + §14.12; horizon index audit. | BLOCKER | TODO |  |
| PRE-021 | Campaign construction uses the roadmap-defined event/campaign merge rule, minimum duration, and intervening-benign tolerance. | R campaign config + §12; campaign registry recomputation. | BLOCKER | TODO |  |
| PRE-022 | Campaign prestart warm-up availability is checked and ineligible campaigns are explicitly marked rather than padded with future information. | R §4.19 + campaign config + §12. | BLOCKER | TODO |  |
| PRE-023 | Campaign evaluation horizons are anchored/reset exactly at campaign start and do not leak preceding sequential/local-policy state. | R §4.19; campaign replay implementation. | BLOCKER | TODO |  |
| PRE-024 | A full real `fedcampaign preprocess` run completes for every roadmap dataset, writes the expected inventory/prepared/split/campaign/provenance layers, and a second identical run demonstrates deterministic reuse/idempotence. | R §§16.2, 17–18; execute preprocess twice without experiment runs. | BLOCKER | TODO |  |

### D. Core mathematical implementation

| ID | Requirement | Verification / expected evidence | Severity | Status | Evidence / notes |
|---|---|---|---|---|---|
| MATH-001 | Coalition outside information is defined from complement-client predictable history only; current or historical information from coalition members cannot enter exact-exclusion nuisance context except where explicitly permitted by another named ablation. | R §4.1 + §8.1. | BLOCKER | TODO |  |
| MATH-002 | Exact-exclusion context is lagged by the configured outside lag; no current-epoch coalition or complement observation enters a predictable context. | R §§4.1, 4.3 + smoke lag fixture. | BLOCKER | TODO |  |
| MATH-003 | Marginal suspicion rank implements the exact deterministic midrank formula, including +1/2 finite-sample offset and denominator n+1. | R §4.2 + §13.1 fixture. | BLOCKER | TODO |  |
| MATH-004 | Rank orientation is consistent: larger detector score maps to larger suspicion rank throughout all methods and metrics. | R §§4.2, 9.2. | BLOCKER | TODO |  |
| MATH-005 | Ranks are clipped exactly at configured epsilon and 1-epsilon after rank computation. | R §4.2 + §13.1. | BLOCKER | TODO |  |
| MATH-006 | Outside-client availability set is determined before current evidence and uses only complement clients declared available for that epoch. | R §4.3. | BLOCKER | TODO |  |
| MATH-007 | Coalition abstention is triggered when outside availability fails either configured minimum-client or minimum-fraction support. | R §4.3 + context config. | BLOCKER | TODO |  |
| MATH-008 | Outside-context histogram uses equal-width [0,1] bins and the exact B(u)=min(floor(u*bins), bins-1) convention. | R §4.3 + §13.1 histogram fixture. | BLOCKER | TODO |  |
| MATH-009 | Context centroids are fitted separately by dataset, coalition order, context method, and seed when score streams are seed-dependent. | R §4.4. | BLOCKER | TODO |  |
| MATH-010 | Context fit-row capping uses deterministic SHA-256 ranking over the declared identity tuple and is independent of input iteration order. | R §4.4. | BLOCKER | TODO |  |
| MATH-011 | K-means uses Euclidean assignment and resolves near-tied centroid distances to the smaller centroid index. | R §4.4 + §13.1 tie fixture. | BLOCKER | TODO |  |
| MATH-012 | Coalition-conditioned residual ranks use the empirical CDF fitted for member/coalition/context cell with the same midrank convention. | R §4.5. | BLOCKER | TODO |  |
| MATH-013 | Order-specific minimum context support is enforced exactly; unsupported coalition/context fits abstain instead of borrowing data or lowering the minimum. | R §4.5 + context.minimum_support_epochs. | BLOCKER | TODO |  |
| MATH-014 | All four bounded basis functions are implemented exactly as specified and primary/sensitivity basis sizes select only declared prefixes. | R §4.6 + basis config. | BLOCKER | TODO |  |
| MATH-015 | Coalition tensor basis dimension is derived as L^\|A\| and ordering is deterministic/stable across fit and score paths. | R §4.6. | BLOCKER | TODO |  |
| MATH-016 | Order-1 proper-subset design performs context-specific centering only and introduces no same-order interaction. | R §4.7. | BLOCKER | TODO |  |
| MATH-017 | Order-2 proper-subset design contains intercept plus both members’ singleton basis coordinates and no pair interaction term. | R §4.7 + projection-dimension fixture. | BLOCKER | TODO |  |
| MATH-018 | Order-3 proper-subset design contains intercept, all singleton coordinates, and all three pair tensor-basis blocks, but no triple interaction. | R §4.7 + projection-dimension fixture. | BLOCKER | TODO |  |
| MATH-019 | Ridge projection minimizes the declared mean squared residual objective and never penalizes the intercept. | R §4.8. | BLOCKER | TODO |  |
| MATH-020 | Projection predictor columns are not silently standardized/rescaled and all projection linear algebra is float64. | R §4.8. | BLOCKER | TODO |  |
| MATH-021 | Contiguous blocked folds follow the q=floor(n/k), r=n mod k rule, assign remainder to earliest folds, and never shuffle observations. | R §4.8 blocked folds + §13.1 fixture. | BLOCKER | TODO |  |
| MATH-022 | If n<k for a required blocked fit, the fit abstains/is unsupported; fold count is never silently reduced. | R §4.8. | BLOCKER | TODO |  |
| MATH-023 | Ridge lambda selection uses fold-size-weighted benign validation MSE and resolves MSE ties within tolerance in favor of the larger lambda. | R §4.8 + §13.1 ridge-tie fixture. | BLOCKER | TODO |  |
| MATH-024 | Zero-ridge projection uses Moore–Penrose SVD with the configured relative singular-value cutoff and condition diagnostics. | R §4.8 + projection config. | BLOCKER | TODO |  |
| MATH-025 | Atom computation is exactly full coalition tensor basis minus the fitted projection on proper-subset design in the active context. | R §4.8. | BLOCKER | TODO |  |
| MATH-026 | Nuisance cross-fitting refits marginal CDFs, context centroids, conditional-rank references, and projection on other folds for each held fold. | R §4.9. | BLOCKER | TODO |  |
| MATH-027 | Cross-fitted held-fold innovations are concatenated back in original chronological order and are the only source for benign atom centering/scaling/norm calibration. | R §4.9 + §13.1 cross-fit fixture. | BLOCKER | TODO |  |
| MATH-028 | Final marginal/context/projection artifacts are refit on the complete nuisance-fit split only after cross-fitted calibration statistics are fixed. | R §4.9. | BLOCKER | TODO |  |
| MATH-029 | Atom centering/scaling uses cross-fitted context-specific mean and sample standard deviation (n-1), applies atom scale floor, and rejects context support below two observations. | R §4.10. | BLOCKER | TODO |  |
| MATH-030 | Signed theorem evidence uses only predeclared alternative direction vectors, configured clipping, and exact exponential compensator; it is never substituted into sign-agnostic real-data claims. | R §4.11. | BLOCKER | TODO |  |
| MATH-031 | Operational norm evidence uses the cross-fitted nuisance-fit norm reference quantile, configured floor, clipping, and the declared exponential transform. | R §4.12. | BLOCKER | TODO |  |
| MATH-032 | Within-order aggregation averages active coalition evidence factors and returns exactly 1 when no coalition of that order is active. | R §4.13. | BLOCKER | TODO |  |
| MATH-033 | Across-order aggregation gives equal weight to enabled orders and never multiplies contemporaneous coalition evidence factors in the primary method. | R §4.14. | BLOCKER | TODO |  |
| MATH-034 | Sequential recursion is G0=0 and Gt=(G(t-1)+1)Et with stop predicate Gt>=h; local policy state never modifies G. | R §4.15. | BLOCKER | TODO |  |
| MATH-035 | Distributed-support predicate uses materially active coalitions over the configured trailing window, unions distinct clients, and may only delay—not lower—the statistical threshold stop. | R §4.16 + §13.1 fixture. | BLOCKER | TODO |  |
| MATH-036 | Finite-horizon operational threshold selection evaluates candidate thresholds on independent non-overlapping benign calibration horizons using one-sided Clopper–Pearson UCB and selects the smallest qualifying candidate; no qualifying candidate yields Operating Point Unavailable. | R §4.18 + §13.1 fixture. | BLOCKER | TODO |  |

### E. Detector, local-policy, stopping, and replay contracts

| ID | Requirement | Verification / expected evidence | Severity | Status | Evidence / notes |
|---|---|---|---|---|---|
| DET-001 | Each client’s local detector is fitted only on its permitted benign detector-fit partition with the detector family assigned by the declared deterministic rule. | R §§9.1 + detector-family assignment. | BLOCKER | TODO |  |
| DET-002 | Isolation Forest implementation/hyperparameters match the authoritative detector configuration and expose scores in the common larger-is-more-suspicious orientation. | R local detector config + §9.2. | BLOCKER | TODO |  |
| DET-003 | One-Class SVM implementation/hyperparameters match the authoritative detector configuration and its native score sign is converted exactly once to the common suspicion orientation. | R local detector config + §9.2. | BLOCKER | TODO |  |
| DET-004 | Autoencoder architecture/training/scoring match the authoritative configuration and reconstruction score orientation is consistent with the common detector contract. | R local detector config + §9.2. | BLOCKER | TODO |  |
| DET-005 | Detector-family assignment is deterministic for a stable client identity and cannot change with collection/order/process scheduling. | R Detector-family assignment. | BLOCKER | TODO |  |
| DET-006 | Local policy candidate thresholds are calibrated only from the permitted local benign calibration source and never from campaign or held-out benign outcomes. | R §§9.3–9.4 + local policy config. | BLOCKER | TODO |  |
| DET-007 | Local persistence logic implements the configured window/exceedance rule exactly, including reset behavior. | R local policy config + §13.1 local-persistence fixture. | BLOCKER | TODO |  |
| DET-008 | Held-out local validation is evaluation-only; it cannot choose or tune a local operating point post hoc. | R §9.4. | BLOCKER | TODO |  |
| DET-009 | Local policy artifacts are immutable for a material identity and local policies never participate in computing the global stopping time. | R §§2.1, 9.5. | BLOCKER | TODO |  |
| DET-010 | Campaign replay resets global G and local persistence windows at campaign start, preserves lagged warm-up context, evaluates global/local stops independently, and computes strict ODI using T_G < min_i T_i (same-epoch tie is not ODI). | R §§2.1, 4.19 + §13.1 ODI fixtures. | BLOCKER | TODO |  |

### F. Baseline and comparator contracts

| ID | Requirement | Verification / expected evidence | Severity | Status | Evidence / notes |
|---|---|---|---|---|---|
| CMP-001 | Fixed Local Policies comparator is implemented exactly as the roadmap contract and remains independent of the global method. | R §10.1; inspect method registry and evaluation path. | BLOCKER | TODO |  |
| CMP-002 | Raw Mean Rank Fusion is implemented with the declared inputs, calibration, and stopping semantics without borrowing EMHI-specific purification. | R §10.2. | BLOCKER | TODO |  |
| CMP-003 | Raw Max Rank Fusion is implemented with the declared inputs, calibration, and stopping semantics. | R §10.3. | BLOCKER | TODO |  |
| CMP-004 | Exclusion-Matched Order-One EMHI uses exact-exclusion information and enables only order 1. | R §10.4. | BLOCKER | TODO |  |
| CMP-005 | Exclusion-Matched Order-at-Most-Two EMHI uses exact-exclusion information and enables only orders <=2; this is the causal predecessor for the primary ODI comparison. | R §10.5. | BLOCKER | TODO |  |
| CMP-006 | Full FedCampaign-EMHI enables every order through the maximum coalition order and uses the primary exact-exclusion/purification contracts. | R §10.6. | BLOCKER | TODO |  |
| CMP-007 | Inclusive-Context Full Hierarchy differs from Full EMHI only by the intended inclusive context information violation. | R §10.7 + §8.2. | BLOCKER | TODO |  |
| CMP-008 | Leave-One-Out Insufficient Exclusion differs only by the intended leave-one-out context construction and preserves all other comparable settings. | R §10.8 + §8.3. | BLOCKER | TODO |  |
| CMP-009 | Partial Coalition Exclusion differs only by the declared partial-exclusion rule and preserves comparable settings. | R §10.9 + §8.4. | BLOCKER | TODO |  |
| CMP-010 | No Proper-Subset Purification removes only the lower-order projection/purification mechanism while preserving the remaining comparable pipeline. | R §10.10. | BLOCKER | TODO |  |
| CMP-011 | No-Outside-Context Full Hierarchy disables outside conditioning exactly as declared and is not conflated with one-cell exact-exclusion equivalence setups. | R §10.11 + §8.6. | BLOCKER | TODO |  |
| CMP-012 | Exclusion-Matched Conditional HOFD uses the same admissible outside information, basis/proper-subset space, support, and paired rows required for a fair equivalence comparison. | R §10.12 + §13.4. | BLOCKER | TODO |  |
| CMP-013 | Conditional Pair Dependence reference implements the declared conditional pair-dependence statistic and calibration contract. | R §10.13. | BLOCKER | TODO |  |
| CMP-014 | Exclusion-Matched Lancaster Triple implements the declared triple interaction reference under matched exclusion information. | R §10.14. | BLOCKER | TODO |  |
| CMP-015 | Connected Information Reference implements the declared reference semantics and does not silently reuse an incompatible estimator. | R §10.15. | BLOCKER | TODO |  |
| CMP-016 | D-Vine Conditional Reference implements the declared conditional vine reference and its support/calibration requirements. | R §10.16. | BLOCKER | TODO |  |
| CMP-017 | Conditional Log-Linear Reference implements the declared conditional log-linear reference and its numerical safeguards. | R §10.17. | BLOCKER | TODO |  |
| CMP-018 | Global Factor Residual Reference implements the declared global-factor residualization and uses only its permitted information. | R §10.18. | BLOCKER | TODO |  |
| CMP-019 | Multistream CUSUM Reference implements the configured multistream CUSUM contract and its operating-point calibration independently from EMHI. | R §10.19. | BLOCKER | TODO |  |
| CMP-020 | FedAvg Autoencoder Reference implements the declared federated-autoencoder comparator and does not inherit unintended EMHI context/purification logic. | R §10.20. | BLOCKER | TODO |  |
| CMP-021 | Strong Comparator Composition Selection is development-only where declared, composes/selects only from the allowed comparator set, and cannot inspect confirmatory outcomes to choose the strongest composition. | R §10.21 + §13.5 + §19. | BLOCKER | TODO |  |

### G. Metric registry and scoring semantics

| ID | Requirement | Verification / expected evidence | Severity | Status | Evidence / notes |
|---|---|---|---|---|---|
| MET-001 | Strict ODI: Strict ODI uses the strict T_G < min_i T_i indicator and preserves valid global detections that are not ODI. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-002 | Global stopping time: Global stopping time is first epoch satisfying threshold and distributed-support predicates; no-stop is stored as null. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-003 | Earliest local stopping time: Earliest local stopping time is the minimum independent local policy stopping time with correct no-stop semantics. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-004 | Statistical lead: Statistical lead is min_i T_i - T_G and is defined only under the roadmap’s finite-stop conditions. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-005 | Operational lead: Operational lead subtracts reference-harness latency converted by real-data epoch seconds exactly as specified. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-006 | Seed-level ODI rate: Seed-level ODI rate aggregates over the fixed eligible campaign registry before inference and uses the seed as the real inferential unit. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-007 | Campaign detection rate: Campaign detection rate uses the declared eligible campaigns/horizon and does not treat no-stop as missing. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-008 | Finite-horizon PFA: Finite-horizon PFA uses held-out benign horizons only and the declared denominator/no-stop semantics. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-009 | False campaigns per 10,000 benign epochs: False-campaign rate per 10,000 benign epochs uses the declared horizon/epoch normalization. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-010 | Signed-theorem sequential ARL: Signed-theorem ARL is computed only for the signed-theorem route and retains its restricted theoretical interpretation. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-011 | Self-explanation derivatives: Self-explanation derivatives are computed from the declared perturbation/nuisance/context grid with exact/inclusive identities preserved. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-012 | Self-explanation attenuation: Self-explanation attenuation uses the declared exact-vs-inclusive comparison and direction. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-013 | Mean log-evidence growth: Mean log-evidence growth uses the declared evidence factors/epochs and handles clipping/non-finite states correctly. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-014 | Proper-subset drift: Proper-subset drift uses the declared standardized population/held-out comparison for all proper subsets. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-015 | Target-order drift: Target-order drift uses the declared target-order atom/evidence definition and standardization. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-016 | Order-specific stopping probability: Order-specific stopping probability is computed from the intended isolated order route rather than inferred from final decisive order. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-017 | Order evidence share: Order evidence share uses the roadmap-defined normalization across enabled orders. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-018 | Decisive order: Decisive order follows the roadmap tie/decision semantics and remains nullable where no decision occurs. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-019 | Atom NRMSE: Atom NRMSE uses paired atom outputs and the declared normalization/reference population. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-020 | Atom cosine similarity: Atom cosine similarity uses aligned paired atom vectors and handles zero-norm cases as specified. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-021 | Stopping-time difference: Stopping-time difference uses paired trajectories and the declared horizon/no-stop representation for scientific calculation. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-022 | PFA difference: PFA difference compares methods on matched held-out benign horizons with the declared sign. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-023 | Conditional-rank MAE: Conditional-rank MAE compares the intended conditional-rank estimate/reference and correct population. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-024 | Projection NRMSE: Projection NRMSE measures projection error on the declared held-out/support population and normalization. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-025 | Standardized null bias: Standardized null bias uses null held-out innovations and the declared scaling. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-026 | Context coverage: Context coverage denominator includes all eligible scoring opportunities and reflects abstention/support exactly. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-027 | Abstention rate: Abstention rate distinguishes scientific abstention from numerical/technical failure. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-028 | Numerical failure rate: Numerical failure rate counts only declared numerical failures and preserves the correct pooled denominator. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-029 | Common-mode suppression: Common-mode suppression uses the declared Raw Mean vs EMHI stress-window false-declaration difference. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-030 | Outside-conditioning power loss: Outside-conditioning power loss is DR_NO_OUTSIDE_CONTEXT - DR_EMHI on matched eligible campaigns. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-031 | AUROC: AUROC uses the declared real/synthetic labels and score direction without post-hoc inversion. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-032 | AUPRC: AUPRC uses the declared positive class and score direction. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-033 | Coalition count: Coalition count derives active/enabled coalition combinatorics from client count/order rather than hardcoded values. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-034 | Server compute latency: Server compute latency measures exactly the server-only interval declared by the roadmap and excludes forbidden setup/I/O. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-035 | End-to-end reference-harness latency: End-to-end latency begins/ends at the roadmap-defined in-process decision boundaries and excludes preprocessing/fitting/loading. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-036 | Application payload bytes: Application payload bytes count the declared application message schema only and do not substitute serialized framework overhead unless specified. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |
| MET-037 | Throughput: Throughput uses the declared measured epochs/repetitions/time interval and common timing environment. | R §11 metric registry; inspect authoritative implementation, inputs, denominator, null/no-stop handling, consumers, and tests. | BLOCKER | TODO |  |

### H. Experiment contracts — static/dry-run verification only

| ID | Requirement | Verification / expected evidence | Severity | Status | Evidence / notes |
|---|---|---|---|---|---|
| EXP-001 | Synthetic Module Validation: The `smoke` workflow contains every exact fixture and expected value in the roadmap; it is the only scientific validation execution permitted in this pre-experiment audit. | R §13.1; verify experiment registry/config/dependency graph and `fedcampaign run <name> --dry-run` only where the exact registered kebab-case identity is resolved from code/config. | BLOCKER | TODO |  |
| EXP-002 | Self-Explanation Exclusion Validation: Registry/config/seed grids/context methods/nuisance transformations/primary condition/support criteria are fully implemented and reachable, but no experiment cells are executed. | R §13.2; verify experiment registry/config/dependency graph and `fedcampaign run <name> --dry-run` only where the exact registered kebab-case identity is resolved from code/config. | BLOCKER | TODO |  |
| EXP-003 | Pure-Order Separation Validation: All generators/effect grids/methods/purity validation/seed roles/primary condition are implemented; analytic purity validation is wired before scoring. | R §13.3; verify experiment registry/config/dependency graph and `fedcampaign run <name> --dry-run` only where the exact registered kebab-case identity is resolved from code/config. | BLOCKER | TODO |  |
| EXP-004 | Exclusion-Matched HOFD Equivalence: Shared null rows, one-cell exact-exclusion comparison, paired held-out atom outputs, independent calibration, equivalence metrics/margins/seeds are wired. | R §13.4; verify experiment registry/config/dependency graph and `fedcampaign run <name> --dry-run` only where the exact registered kebab-case identity is resolved from code/config. | BLOCKER | TODO |  |
| EXP-005 | Strong Comparator Composition Challenge: Allowed comparator compositions, development-only selection logic, evaluation inputs, and locked downstream selected composition are wired without confirmatory leakage. | R §13.5; verify experiment registry/config/dependency graph and `fedcampaign run <name> --dry-run` only where the exact registered kebab-case identity is resolved from code/config. | BLOCKER | TODO |  |
| EXP-006 | Estimator Support and Context Feasibility: Support grid, context-cell grid, order-3 feasibility metrics, numerical-failure accounting, and support criteria are wired. | R §13.6; verify experiment registry/config/dependency graph and `fedcampaign run <name> --dry-run` only where the exact registered kebab-case identity is resolved from code/config. | BLOCKER | TODO |  |
| EXP-007 | Sequential Evidence Validation: Signed-theorem and calibrated-finite-horizon routes are distinct, correctly calibrated, and wired to their respective metrics/semantics. | R §13.7; verify experiment registry/config/dependency graph and `fedcampaign run <name> --dry-run` only where the exact registered kebab-case identity is resolved from code/config. | BLOCKER | TODO |  |
| EXP-008 | Primary Strict ODI Evaluation: Primary dataset, methods, paired real seeds, campaign registry, calibrated PFA, strict ODI/lead metrics, predecessor comparison, and support criteria are wired. | R §13.8; verify experiment registry/config/dependency graph and `fedcampaign run <name> --dry-run` only where the exact registered kebab-case identity is resolved from code/config. | BLOCKER | TODO |  |
| EXP-009 | Exclusion Mechanism Ablation: Exact/inclusive/leave-one-out/partial exclusion methods and matched evaluation/statistics are wired with only the intended context difference. | R §13.9; verify experiment registry/config/dependency graph and `fedcampaign run <name> --dry-run` only where the exact registered kebab-case identity is resolved from code/config. | BLOCKER | TODO |  |
| EXP-010 | Purification and Order Ablation: No-purification and order-restricted variants are wired against the same upstream evidence where scientifically compatible. | R §13.10; verify experiment registry/config/dependency graph and `fedcampaign run <name> --dry-run` only where the exact registered kebab-case identity is resolved from code/config. | BLOCKER | TODO |  |
| EXP-011 | Context and Estimator Sensitivity: Declared basis/context/support sensitivity grid is wired and separated from claim-bearing primary settings. | R §13.11; verify experiment registry/config/dependency graph and `fedcampaign run <name> --dry-run` only where the exact registered kebab-case identity is resolved from code/config. | BLOCKER | TODO |  |
| EXP-012 | Benign Common-Mode Robustness: Native non-overlapping horizons, high-volume stress windows, synthetic-on-real count stress, positive-power branch, and support metrics are wired with correct evidence roles. | R §13.12; verify experiment registry/config/dependency graph and `fedcampaign run <name> --dry-run` only where the exact registered kebab-case identity is resolved from code/config. | BLOCKER | TODO |  |
| EXP-013 | Strong Local Policy Challenge: Global EMHI artifacts are shared with primary evaluation; only independently calibrated strong-local policy changes, with matched ODI inference wiring. | R §13.13; verify experiment registry/config/dependency graph and `fedcampaign run <name> --dry-run` only where the exact registered kebab-case identity is resolved from code/config. | BLOCKER | TODO |  |
| EXP-014 | Secondary Controlled-Trace Generalization: Secondary methods/seeds/eligibility are wired, and insufficient eligible clients resolve to Not Tested without substitute data. | R §13.14; verify experiment registry/config/dependency graph and `fedcampaign run <name> --dry-run` only where the exact registered kebab-case identity is resolved from code/config. | BLOCKER | TODO |  |
| EXP-015 | Outside-Campaign Contamination Boundary: Configured correlated-campaign fractions, target triple, seeds, boundary metrics, and limited interpretation are wired. | R §13.15; verify experiment registry/config/dependency graph and `fedcampaign run <name> --dry-run` only where the exact registered kebab-case identity is resolved from code/config. | BLOCKER | TODO |  |
| EXP-016 | Client Dropout and Context Sparsity Boundary: Client-count/dropout grid, development-only role, coverage/abstention/null-bias/detection/latency metrics are wired. | R §13.16; verify experiment registry/config/dependency graph and `fedcampaign run <name> --dry-run` only where the exact registered kebab-case identity is resolved from code/config. | BLOCKER | TODO |  |
| EXP-017 | Coalition Scalability: Synthetic reference harness, production feature dimension/detector-family mix/context/decision path, timing repetitions, exclusions, fallback timing states, and latency metrics are wired. | R §13.17; verify experiment registry/config/dependency graph and `fedcampaign run <name> --dry-run` only where the exact registered kebab-case identity is resolved from code/config. | BLOCKER | TODO |  |
| EXP-018 | Experiment registry completeness: exactly the roadmap-declared experiment contracts are registered, every experiment has deterministic outer-cell derivation/dependencies/mandatory outputs, and no undocumented scientific experiment silently enters the production registry. | R §§13,16.3,16.5; compare roadmap identities to registry and plan output. | BLOCKER | TODO |  |

### I. Statistical analysis protocol

| ID | Requirement | Verification / expected evidence | Severity | Status | Evidence / notes |
|---|---|---|---|---|---|
| STAT-001 | Controlled synthetic experimental unit is the roadmap-defined independent seed/condition unit; repeated rows within a seed are not promoted to independent replicates. | R §14.1. | BLOCKER | TODO |  |
| STAT-002 | Real experimental unit is the seed after aggregating over the fixed campaign registry; campaign×seed rows are never treated as independent confirmatory units. | R §14.2. | BLOCKER | TODO |  |
| STAT-003 | Pairing keys are explicit and stable so paired methods compare the same seed/campaign/condition identities. | R §14.3. | BLOCKER | TODO |  |
| STAT-004 | Real exact sign-flip test enumerates all 2^10=1024 sign assignments for ten confirmatory seeds, retains zero differences, and implements the declared one-/two-sided alternatives exactly. | R §14.4. | BLOCKER | TODO |  |
| STAT-005 | Synthetic sign-flip/permutation inference follows the configured synthetic confirmatory design and does not reuse real-data assumptions incorrectly. | R §14.5. | BLOCKER | TODO |  |
| STAT-006 | Paired BCa bootstrap resamples the declared independent units while preserving pairing and uses the configured analysis seed/count; there is no silent percentile-bootstrap fallback. | R §14.6. | BLOCKER | TODO |  |
| STAT-007 | Hierarchical campaign bootstrap, where used, preserves the declared seed/campaign hierarchy and is not substituted for the primary seed-level inference. | R §14.7. | BLOCKER | TODO |  |
| STAT-008 | Hodges–Lehmann paired shift uses the roadmap-defined Walsh-average construction and correct pairwise differences. | R §14.8. | BLOCKER | TODO |  |
| STAT-009 | Equivalence requires the entire confidence interval inside the declared equivalence region; failure to reject a difference is never interpreted as equivalence. | R §14.9. | BLOCKER | TODO |  |
| STAT-010 | Every predeclared directional hypothesis uses the correct metric, sign, null/materiality shift, independent unit, and one-/two-sided alternative. | R §14.10. | BLOCKER | TODO |  |
| STAT-011 | Primary Holm family contains exactly the declared primary hypotheses in fixed family membership regardless of unavailable cells. | R statistical config + §14.11. | BLOCKER | TODO |  |
| STAT-012 | Secondary ablation Holm family contains exactly the declared contrasts and is kept separate from the primary family. | R statistical config + §14.11. | BLOCKER | TODO |  |
| STAT-013 | Unavailable scientific hypotheses retain null scientific p-values while multiplicity bookkeeping uses the declared conservative Holm input behavior only; unavailable evidence is not imputed. | R §§14.11,14.15. | BLOCKER | TODO |  |
| STAT-014 | PFA inference uses the declared one-sided Clopper–Pearson interval and separates calibration-threshold selection from held-out PFA reporting. | R §§4.18,14.12. | BLOCKER | TODO |  |
| STAT-015 | Binary descriptive intervals use the declared interval method and remain descriptive unless explicitly part of a claim criterion. | R §14.13. | BLOCKER | TODO |  |
| STAT-016 | Primary materiality aggregation for ODI rate, ODI advantage, and operational lead is implemented exactly, and missing/failed/Operating-Point-Unavailable cells follow §14.15/§15 without favorable-value substitution. | R §§14.14–15. | BLOCKER | TODO |  |

### J. CLI, Graphify, workflow reachability, and callable accounting

| ID | Requirement | Verification / expected evidence | Severity | Status | Evidence / notes |
|---|---|---|---|---|---|
| WIRE-001 | Generate a fresh Graphify graph from the current working tree; do not reuse a prior graph as evidence for this audit. | Project rule + R §16 package-topology flexibility; record Graphify command/version/output path actually available in repo. | BLOCKER | TODO |  |
| WIRE-002 | Count total production callables under the implementation package, separated at minimum into module functions and class methods. | Project rule; Graphify + AST/static cross-check. | MAJOR | TODO |  |
| WIRE-003 | Count public CLI command entry callables and map doctor/preprocess/plan/smoke/run/status/report to their implementation entry points. | R §16. | BLOCKER | TODO |  |
| WIRE-004 | Count all production callables transitively reachable from at least one public CLI path. | Project rule; Graphify reachability. | BLOCKER | TODO |  |
| WIRE-005 | Identify dynamically/framework-reachable callables that Graphify cannot resolve statically and justify them with registry/decorator/callback/runtime evidence. | Project rule; do not classify unresolved dynamic code as dead automatically. | MAJOR | TODO |  |
| WIRE-006 | List every production callable unreachable from all CLI/dynamic production roots and classify it as needs-wiring, legitimate non-CLI infrastructure, or dead-code candidate. | Project rule. | BLOCKER | TODO |  |
| WIRE-007 | For each public command, compute its unique transitive callable count from CLI entry through deepest reachable production leaves. | Project rule; Graphify per-root traversal. | MAJOR | TODO |  |
| WIRE-008 | For each public command, compute maximum call depth and terminal/leaf callable count. | Project rule; Graphify per-root traversal. | MAJOR | TODO |  |
| WIRE-009 | For each registered experiment, statically trace the `run` dispatch through experiment resolution, prerequisites, fitting/scoring/calibration/evaluation/metric/statistics/report-source producers to the deepest prospective production leaves without executing the experiment. | R §§13,16.5; Graphify + registry inspection. | BLOCKER | TODO |  |
| WIRE-010 | For each experiment, count unique prospective transitive production callables and identify callables shared with other experiment workflows. | Project rule; Graphify/registry traversal. | MAJOR | TODO |  |
| WIRE-011 | Map every roadmap mathematical operation (§4) to at least one reachable production implementation and caller chain. | R §4; science-to-code matrix + Graphify. | BLOCKER | TODO |  |
| WIRE-012 | Map every baseline/comparator (§10) to a reachable registered implementation and experiment consumer. | R §10; Graphify + registry. | BLOCKER | TODO |  |
| WIRE-013 | Map every metric (§11) to a reachable metric implementation and its experiment/statistical/report consumers. | R §11; Graphify + registry. | BLOCKER | TODO |  |
| WIRE-014 | Detect scientific implementations that exist but are bypassed by the actual production workflow; classify them UNWIRED rather than PASS. | Project rule. | BLOCKER | TODO |  |
| WIRE-015 | Detect duplicate/parallel implementations of the same scientific operation and determine the authoritative reachable implementation. | Project rule; Graphify communities/callers + source audit. | MAJOR | TODO |  |
| WIRE-016 | Before deleting any dead-code candidate, reconcile it against roadmap requirements and potential missing wiring; assume scientific code may need wiring until disproved. | Project rule. | BLOCKER | TODO |  |
| WIRE-017 | Verify no CLI workflow terminates prematurely at a facade/runner while required downstream scientific work exists only in disconnected modules. | Project rule; CLI-to-leaf path inspection. | BLOCKER | TODO |  |
| WIRE-018 | Verify architecture dependency direction has no cycles/bypasses that allow reporting/config/CLI layers to become hidden scientific computation sources. | R §§16.8,18; Graphify dependency graph + architecture tests. | BLOCKER | TODO |  |
| WIRE-019 | After all audit fixes, regenerate Graphify from scratch and require zero unexplained scientific orphans/unwired mandatory methods. | Project rule; final Graphify evidence. | BLOCKER | TODO |  |
| WIRE-020 | Store a compact Graphify summary in the audit evidence: total callables, CLI-reachable, dynamic-justified, unexplained unreachable, terminal leaves, max depth, and per-command/per-experiment counts; do not add this as production claim infrastructure. | Project rule; audit-only artifact. | MAJOR | TODO |  |

### K. Artifact identity, caching, provenance, outputs, and reporting

| ID | Requirement | Verification / expected evidence | Severity | Status | Evidence / notes |
|---|---|---|---|---|---|
| ART-001 | Semantic scientific artifact identity is derived from material scientific coordinates/dependencies, never timestamps, run counters, or “latest file” discovery. | R §§17.1,18. | BLOCKER | TODO |  |
| ART-002 | Artifact dependency graph explicitly records producers/consumers so invalidation follows descendants only and does not invalidate unrelated ancestors/siblings. | R §§17.2,17.5. | BLOCKER | TODO |  |
| ART-003 | Material dependency fingerprints include every scientifically material code/config/data/upstream identity and exclude irrelevant technical noise. | R §17.3. | BLOCKER | TODO |  |
| ART-004 | Reuse validates compatibility independently at each layer; compatible ancestors are reused even when first produced by another experiment. | R §§1,16.5,17.4. | BLOCKER | TODO |  |
| ART-005 | Completion is atomic: partially written artifacts/checkpoints cannot be mistaken for completed scientific evidence. | R §§17.4,17.7–17.8. | BLOCKER | TODO |  |
| ART-006 | Overwrite recomputes only owned/requested semantic artifacts and invalidates descendants only when material identity changes. | R §§16.2,16.4–16.7,17.7. | BLOCKER | TODO |  |
| ART-007 | Caches are explicitly non-authoritative/recomputable and cannot establish scientific validity without authoritative manifests/fingerprints. | R §16 tree + §17.8. | BLOCKER | TODO |  |
| ART-008 | Logs provide structured progress/reuse/failure/runtime diagnostics but are never consumed as scientific evidence. | R §§17.9,18.7. | MAJOR | TODO |  |
| ART-009 | `outputs/` remains the authoritative reusable computational workspace while `results/` is terminal manuscript evidence and is never read back as a scientific input. | R §§16,18.1–18.2. | BLOCKER | TODO |  |
| ART-010 | Preprocessing/campaign/scientific-cell/result/statistical manifests contain the roadmap-required identity, hash, dependency, seed, state, support, runtime, and output fields. | R §§18.3–18.6. | BLOCKER | TODO |  |
| ART-011 | Every figure/table has exactly one machine-readable verified source artifact; visualization/reporting never reads console values or diagnostic logs as scientific data. | R §18.7. | BLOCKER | TODO |  |
| ART-012 | `report` performs no fitting, scoring, calibration, evaluation, metric recomputation, or statistical analysis; before experiments, its behavior must correctly reflect unavailable verified evidence rather than fabricate/repair it. | R §§16.7,18.8,20. | BLOCKER | TODO |  |

### L. Types, enums, primitive-leak prevention, and domain modeling

| ID | Requirement | Verification / expected evidence | Severity | Status | Evidence / notes |
|---|---|---|---|---|---|
| TYPE-001 | Keep `types.py` (or the project’s existing designated domain-type module) and preserve legitimate aliases; do not “simplify” by deleting the type layer. | Project rule. | MAJOR | TODO |  |
| TYPE-002 | Repeated finite domain identities such as dataset, experiment, method, comparator, metric, status/state, execution role, context method, evidence route, and artifact category are represented by Enums/domain types rather than unconstrained hardcoded strings. | Project rule; enumerate repeated literals and public/internal signatures. | BLOCKER | TODO |  |
| TYPE-003 | String-based dispatch/switching on domain values is eliminated in favor of typed enum/registry dispatch, except at serialization/CLI boundaries. | Project rule. | BLOCKER | TODO |  |
| TYPE-004 | Meaningful scientific/public internal APIs do not leak raw `str`, `int`, `float`, `dict`, `object`, or `Any` where a stable domain type already exists. | Project rule; inspect signatures from CLI/service/domain boundaries to leaves. | BLOCKER | TODO |  |
| TYPE-005 | Numeric primitives remain allowed inside numerical algorithms/arrays where they are genuinely mathematical values; the audit targets domain-identity leaks, not arbitrary elimination of numeric computation. | Project rule; prevent over-refactoring. | MAJOR | TODO |  |
| TYPE-006 | Special aliases/wrappers such as NonNegativeInt, PositiveInt, NonNegativeFloat, PositiveFloat, UnitInterval, OpenUnitInterval, FiniteFloat, and SignedInt do not proliferate outside the designated type layer merely as wrapper noise. | Project rule; static search outside types module. | BLOCKER | TODO |  |
| TYPE-007 | No unnecessary `.value` churn is used around enums/domain objects; conversion occurs only at explicit serialization, external-library, CLI, or storage boundaries. | Project rule; search `.value` and inspect necessity. | BLOCKER | TODO |  |
| TYPE-008 | No unnecessary `float()`, `int()`, `str()` casts are used to undo already-correct typing or compensate for weak interfaces. | Project rule; static search + data-flow inspection. | BLOCKER | TODO |  |
| TYPE-009 | No conversion-helper or wrapper-object layer exists solely to repeatedly convert strong types back to primitives and then reconstruct them. | Project rule; inspect adapters/helpers. | BLOCKER | TODO |  |
| TYPE-010 | Raw `dict`/`Any`/`object` are not used as escape hatches for scientific records that have stable schemas; typed models/dataclasses are used where appropriate. | Project rule; inspect records/config/artifact interfaces. | BLOCKER | TODO |  |
| TYPE-011 | Serialization/deserialization boundaries validate and reconstruct domain types exactly once, while internal workflows preserve typed identities end-to-end. | Project rule; trace CLI/config/artifact IO boundaries. | BLOCKER | TODO |  |
| TYPE-012 | Architecture/static tests explicitly catch future enum/domain-string regressions, forbidden primitive aliases outside the type module, primitive leaks in protected APIs, and unnecessary wrapper/cast patterns where mechanically detectable. | Project rule; inspect tests/architecture and Semgrep/Ruff/Pyright rules. | MAJOR | TODO |  |

### M. Duplication, defaults, paths, dead code, libraries, and code hygiene

| ID | Requirement | Verification / expected evidence | Severity | Status | Evidence / notes |
|---|---|---|---|---|---|
| QUAL-001 | No scientific formula/rule (rank, blocked folds, exclusion, calibration, metric, campaign rule, eligibility rule, statistical rule) has multiple drifting implementations; duplicated science is consolidated behind one authoritative implementation. | Project rule; clone/search + Graphify caller analysis. | BLOCKER | TODO |  |
| QUAL-002 | General code duplication/near-duplication is audited and removed where consolidation improves clarity without creating opaque over-general abstractions. | Project rule; duplication tool/static inspection. | MAJOR | TODO |  |
| QUAL-003 | Hardcoded domain strings are eliminated or justified; repeated experiment/dataset/method/metric/status/artifact labels come from typed identities. | Project rule; literal scan cross-checked with TYPE requirements. | BLOCKER | TODO |  |
| QUAL-004 | Magic numbers and scientific default argument values are eliminated from arbitrary call sites and placed in authoritative config, derived formulas, or explicit implementation constants according to roadmap ownership. | Project rule + Configuration YAML semantics. | BLOCKER | TODO |  |
| QUAL-005 | Path construction is centralized through the project’s path/artifact abstraction; scientific code does not concatenate/scatter raw path strings across modules. | Project rule + §§16–18. | MAJOR | TODO |  |
| QUAL-006 | Mature libraries already in the dependency set are used where they safely replace custom boilerplate; custom reimplementations are retained only when roadmap semantics require them. | Project rule; dependency/boilerplate audit. | MAJOR | TODO |  |
| QUAL-007 | Dead-code cleanup is evidence-based: code is deleted only after roadmap reconciliation, Graphify reachability, registries/callbacks, and runtime/dynamic paths show it is neither required nor merely unwired. | Project rule. | BLOCKER | TODO |  |
| QUAL-008 | Production source contains no claim-registry infrastructure, source-code AST/fingerprint gimmicks, git-dirty/dependency policing, prose modules explaining results, or other non-scientific baggage explicitly forbidden by the roadmap/project rules; provenance is limited to what artifact reuse/reproducibility actually requires. | R §18.7 claim-registry prohibition + project rules. | MAJOR | TODO |  |

### N. Tests, short commands, and final pre-experiment readiness gate

| ID | Requirement | Verification / expected evidence | Severity | Status | Evidence / notes |
|---|---|---|---|---|---|
| READY-001 | Run focused unit/architecture/static checks after implementation audit/fixes and then run the full allowed test suite; no ordinary test suite should require claim-bearing experiment execution. | Project rule; record commands/results/runtime. | BLOCKER | TODO |  |
| READY-002 | `fedcampaign doctor` is run before preprocessing and is read-only: it reports readiness/staleness/next action without creating or mutating artifacts. | R §16.1; compare filesystem/material state before/after. | BLOCKER | TODO |  |
| READY-003 | `fedcampaign preprocess` is run on the real configured datasets and completes the full §6–7 preprocessing contract; no experiment is launched as a side effect. | R §16.2; execution evidence. | BLOCKER | TODO |  |
| READY-004 | A second identical `fedcampaign preprocess` run demonstrates compatible-layer reuse/idempotence; optional controlled overwrite verification may be used only if it does not trigger downstream experiments. | R §16.2; compare identities/hashes/state. | BLOCKER | TODO |  |
| READY-005 | `fedcampaign smoke` is run and must pass every exact Synthetic Module Validation fixture; this validation workflow is permitted even though all claim-bearing `run` experiments remain forbidden. | R §§13.1,16.4. | BLOCKER | TODO |  |
| READY-006 | `fedcampaign plan` and `fedcampaign status` are run after preprocessing/smoke; both are read-only and their experiment/cell/dependency counts are reconciled with the authoritative registry and Graphify mapping. | R §§16.3,16.6. | BLOCKER | TODO |  |
| READY-007 | For every registered experiment, `fedcampaign run <experiment-name> --dry-run` may be executed to validate identity/material digest/fixed resume sequence; no non-dry `run` invocation is permitted during this audit. `report` may be invoked only to verify its pre-experiment scientific-no-computation behavior; it may create only eligible report/export descendants and must not fabricate missing evidence. | R §§16.5,16.7; explicitly forbid actual experiment execution. | BLOCKER | TODO |  |
| READY-008 | Final gate: all 250 requirements are resolved; zero unresolved scientific BLOCKERs, zero mandatory UNWIRED/MISSING items, zero leakage defects, zero unexplained Graphify scientific orphans, all allowed commands behave correctly, preprocessing/smoke/tests pass, and no claim-bearing experiment has been executed. | Pre-experiment acceptance condition. | BLOCKER | TODO |  |

## Required final audit summary
At completion, append a concise summary containing: total PASS/FAIL/PARTIAL/UNWIRED/MISSING/justified deviations; all blockers; all major findings; preprocessing identities and selected clients; smoke/test results; Graphify total/CLI-reachable/dynamic-justified/unexplained-unreachable/leaf/max-depth counts; per-command callable counts; per-experiment prospective callable counts; and an explicit statement that no claim-bearing experiment was executed.
