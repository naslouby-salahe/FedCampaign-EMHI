# Roadmap Coverage Inventory

> This inventory is derived exclusively from the authoritative roadmap. It is the traceability bridge between the roadmap and GitHub planning state; it does not replace, reinterpret, weaken, or extend the roadmap.

**Identifier stability rule:** once a `REQ-*` identifier is referenced by a GitHub issue, it must never be renumbered. Newly discovered requirements are appended with new identifiers.

## 1. Inventory Metadata

| Field | Value |
| --- | --- |
| Authoritative roadmap | `docs/FedCampaign_EMHI_Roadmap.md` |
| Roadmap version/date | No separate version/date declared in the roadmap |
| Extraction depth | Entire authoritative roadmap, Sections 1–23, including configuration, fixed scientific definitions, experiment contracts, repository/CLI contracts, artifact/provenance rules, reporting requirements, claim gates, exclusions, and failure semantics |
| Last reconciliation date | 2026-08-21 |
| Source authority | Roadmap first; this inventory is derivative; GitHub milestones/issues/audits are downstream planning state |

## 2. Status Vocabulary

### Mapping status

- `UNMAPPED` — no current GitHub milestone/issue owns the requirement yet.
- `MAPPED` — the requirement is owned by an explicit GitHub milestone and one or more implementation issues.
- `BLOCKED — clarification required` — implementation would have to invent or choose a material decision not resolved by the roadmap/authority.

### Acceptance evidence

- `Not yet recorded` — no objective acceptance target has been established.
- `Defined` — the requirement itself contains or points to an objective verification target, but implementation evidence does not yet exist.
- `Verified` — implementation evidence has been produced and validated.

### Audit status

- `Not yet audited`
- `Audited — pass`
- `Audited — defects found`
- `Re-audited — pass`

## 3. Requirement Inventory

| Requirement ID | Source Location | Requirement Type | Atomic Requirement | Milestone | Issue(s) | Acceptance Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | §1 Conceptual execution lifecycle | Execution / governance | Implement the roadmap-defined scientific prerequisite lifecycle in the stated order while treating it as dependency order, not a mandate to rerun completed compatible work. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-002 | §1 Conceptual execution lifecycle | Runtime / resumability | At every command boundary validate existing artifacts, reuse compatible artifacts, remove stale descendants from active consideration, recompute only missing/invalidated artifacts, and resume from the nearest valid dependency boundary. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-003 | §1 Conceptual execution lifecycle | Failure semantics | Treat correctly executed unfavorable scientific outcomes as Completed; never convert them to Failed or rerun them merely because results are unfavorable. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-004 | §1 Conceptual execution lifecycle | Invalidation | Invalidate only downstream descendants whose material dependencies changed; preserve unrelated ancestors, siblings, and completed experiments. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-005 | §1 Conceptual execution lifecycle | Dependency / blocking | Block downstream work only when a mandatory prerequisite is Failed, Invalid, or scientifically Not Tested in a way that makes the required downstream quantity unavailable. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-006 | §2.1 Operational Distributed Insufficiency | Scientific semantics | Orient every fixed local detector score so larger values mean greater local suspicion. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-007 | §2.1 Operational Distributed Insufficiency | Algorithm / independence | Keep local-policy stopping independent from global statistical stopping; local policies must never participate in computing `T_G`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-008 | §2.1 Operational Distributed Insufficiency | Metric semantics | Define strict ODI exactly as `T_G < min_i(T_i)`; a same-epoch tie is not ODI. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-009 | §2.1 Operational Distributed Insufficiency | Metric / reporting | Record a global statistical stop at or after the earliest local action as a global detection but not ODI. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-010 | §2.2 EMII principle | Scientific / algorithmic | For each coalition `A`, restrict nuisance information used to explain `A` to predictable information generated only by `A^c`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-011 | §2.2 EMII principle | Scientific / algorithmic | Define the order-`|A|` innovation as the coalition-representation component not representable by any proper subcoalition under admissible outside information. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-012 | §2.2 EMII principle | Claim boundary | Restrict novelty claims to EMII information admissibility and its operational consequences; do not claim novelty for the roadmap-listed established decompositions, ranks, copulas, sequential methods, FedAvg, or generic distributed anomaly fusion. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-013 | §2.4 Forbidden extrapolations | Negative requirement / claim boundary | Do not claim formal/cryptographic privacy, differential privacy, Byzantine robustness, poisoning robustness, causal identification, or distribution-free validity under arbitrary concept drift. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-014 | §2.4 Forbidden extrapolations | Negative requirement / claim boundary | Do not infer client independence merely from client representation or claim natural cross-company federation from controlled host-level traces. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-015 | §2.4 Forbidden extrapolations | Negative requirement / claim boundary | Do not claim production-SOC deployment readiness or network-latency performance beyond the in-process reference harness. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-016 | §2.4 Forbidden extrapolations | Negative requirement / claim boundary | Do not claim behavior above `study.maximum_coalition_order` or universal scalability beyond the tested client-count grid. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-017 | §2.4 Forbidden extrapolations | Negative requirement / claim boundary | Do not claim superiority to exclusion-matched conditional HOFD when both target the same population subspace. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-018 | §2.4 Forbidden extrapolations | Negative requirement / claim boundary | Do not claim real-data anytime validity without a separate theorem-quality conditional-null argument. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-019 | §3 Research questions and support criteria | Configuration / governance | Prevent claim thresholds, equivalence margins, comparators, effect settings, metrics, test directions, multiplicity families, development seeds, and confirmatory seeds from changing in response to observed outcomes. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-020 | §4.1 Information fields | Mathematics / provenance | Construct exact-exclusion nuisance context as a deterministic representation measurable with respect to predictable complement field `G^{-A}_{t-1}`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-021 | §4.1 Information fields | Negative requirement / leakage | For exact exclusion, prohibit every current-epoch observation from any member of coalition `A` from entering nuisance/context construction. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-022 | §4.2 Marginal suspicion rank | Algorithm / mathematics | Compute marginal suspicion ranks with the exact roadmap deterministic midrank formula, including half-credit for ties and its continuity/denominator convention. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-023 | §4.2 Marginal suspicion rank; §5 `context.rank_clip_epsilon` | Numerics | Clip marginal ranks with `context.rank_clip_epsilon` while preserving higher-rank-means-more-suspicious orientation. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-024 | §4.3 Outside-context histogram | Algorithm | Construct exact-exclusion outside histograms from previous-epoch marginal ranks of complement clients declared available before current evidence is formed. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-025 | §4.3 Outside-context histogram | Failure semantics | Make coalition `A` abstain when the configured outside-availability support rule is not met. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-026 | §4.3 Outside-context histogram | Configuration ownership | Derive equal-width histogram edges on `[0,1]` from `context.outside_histogram_bin_count`; do not configure edges separately. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-027 | §4.4 Context clustering | Determinism | Fit centroids at the roadmap-defined dataset/order/context-method/(when required) seed scope and cap oversized fit rows by deterministic SHA-256 ranking over the prescribed identity fields. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-028 | §4.4 Context clustering | Tie semantics | Assign contexts by Euclidean distance and choose the smaller centroid index when distances tie within `context.kmeans.assignment_tie_tolerance`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-029 | §4.5 Coalition-conditioned residual ranks | Algorithm | Compute coalition-conditioned residual ranks from nuisance-fit empirical CDFs within the same coalition/context cell using the same midrank convention. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-030 | §4.5 Coalition-conditioned residual ranks | Failure semantics | Abstain whenever coalition/context support is below the order-specific configured minimum. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-031 | §4.6 Bounded basis | Mathematics | Implement the four roadmap-defined bounded shifted-Legendre basis functions exactly and use only configured primary/sensitivity prefixes. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-032 | §4.6 Bounded basis | Derivation | Construct coalition tensor representations with dimension `L^{|A|}`, derived from basis prefix length and coalition order. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-033 | §4.7 Proper-subset design | Algorithm | For order one, use context-specific centering only. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-034 | §4.7 Proper-subset design | Algorithm | For order two, use an intercept and every singleton basis coordinate for both coalition members. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-035 | §4.7 Proper-subset design | Negative requirement / algorithm | For order two, include no order-two interaction term in the proper-subset design. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-036 | §4.7 Proper-subset design | Algorithm | For order three, use an intercept, every singleton basis coordinate, and every pair tensor-basis coordinate for the three proper pairs. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-037 | §4.7 Proper-subset design | Negative requirement / algorithm | For order three, include no order-three interaction term in the proper-subset design. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-038 | §4.8 Ridge projection | Numerics / algorithm | Fit proper-subset projection in float64 with an unpenalized intercept and no predictor-column rescaling. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-039 | §4.8 Ridge projection | Configuration / CV | Select ridge from configured candidates using deterministic contiguous blocked cross-validation and fold-size-weighted benign validation MSE. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-040 | §4.8 Ridge projection | Tie semantics | Treat candidate MSEs within `projection.selection_tie_tolerance_mse` as tied and choose the larger ridge penalty. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-041 | §4.8 Ridge projection | Numerics | For zero ridge compute the Moore-Penrose solution by SVD using the configured relative cutoff. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-042 | §4.8 Ridge projection → blocked folds | Failure semantics / CV | Use exact chronological `q=floor(n/k), r=n mod k` fold boundaries; never shuffle and abstain rather than reducing `k` when `n<k`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-043 | §4.9 Cross-fitted benign innovation calibration | Leakage prevention | Within each held fold fit all nuisance components only on the other folds and compute innovations only on the held fold. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-044 | §4.9 Cross-fitted benign innovation calibration | Calibration | Use only concatenated held-fold innovations for benign atom center/scale/norm calibration, then refit final scoring artifacts on complete nuisance-fit. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-045 | §4.9 Cross-fitted benign innovation calibration | Negative requirement / leakage | Never reuse `threshold_and_policy_calibration` for atom fitting or atom-scale estimation. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-046 | §4.10 Centering/scaling | Numerics | Standardize atom coordinates with the exact roadmap formula, atom-scale floor, and sample SD denominator `n-1`; support requires at least two cross-fitted observations. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-047 | §4.11 Signed theorem evidence | Sequential / claim boundary | Use signed evidence only for a mathematically fixed direction; compute the exact clipped exponential factor/compensator and use this route only for the conditional e-detector statement. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-048 | §4.12 Operational norm evidence | Algorithm / claim boundary | Compute sign-agnostic norm evidence from cross-fitted nuisance-fit norm calibration but never describe it as an anytime-valid real-data e-value. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-049 | §4.13 Within-order aggregation | Algorithm | Average operational evidence over active coalitions of each enabled order. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-050 | §4.13 Within-order aggregation | Algorithm | When no coalition of an enabled order is active, set that order evidence to `1`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-051 | §4.14 Across-order aggregation | Algorithm | Average enabled-order evidences with equal derived weights; do not separately configure order weights. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-052 | §4.14 Across-order aggregation | Negative requirement | Never multiply contemporaneous coalition evidence factors in the primary method. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-053 | §4.15 Sequential recursion | Algorithm / independence | Implement `G_0=0`, `G_t=(G_{t-1}+1)E_t`; statistical stop requires threshold and distributed-support predicates, while local state cannot alter `G_t`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-054 | §4.16 Distributed-support predicate | Algorithm | Define material coalitions by configured evidence threshold and support from the union of distinct clients over the trailing window; support may delay but never lower a threshold. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-055 | §4.17 Signed-Theorem route | Sequential / claim boundary | Use reciprocal `arl_alpha` threshold and restrict interpretation to inherited ARL semantics; never use this route to justify primary real-data finite-horizon PFA. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-056 | §4.18 Finite-Horizon route | Statistics / calibration | Select the smallest configured global threshold whose one-sided exact Clopper-Pearson UCB on non-overlapping calibration horizons is at most target PFA. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-057 | §4.18 Finite-Horizon route | Failure semantics | If no threshold qualifies, emit Operating Point Unavailable as valid Completed science and never retune from held-out benign data. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-058 | §4.18 Finite-Horizon route | Derived constraint | Derive minimum calibration horizons from target PFA/confidence; locked values require 59 even with zero false stops. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-059 | §4.19 Campaign replay | Evaluation | Require clean warm-up, compute lagged contexts through warm-up, reset global/local state at campaign start, and independently evaluate global/local policies for the fixed horizon. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-060 | §4.20 Lead | Metrics | Compute statistical and protocol-adjusted operational lead exactly; define operational lead only when global and earliest local stops are finite. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-061 | §5 Configuration authority | Configuration | Materialize exactly one production scientific configuration at `configs/fedcampaign-emhi.yaml`; reduced `tests.yml` and `smoke.yml` cannot alter claim-bearing science. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-062 | §5 Configuration authority | Configuration ownership | Keep fixed formulas/procedures/architectures/scoring/validation/provenance/failure/reporting rules in roadmap-defined implementation owners rather than duplicating them as config. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-063 | §5 Configuration authority | Negative requirement / configuration | Treat primary YAML values as scientifically locked and vary only values explicitly consumed by declared sensitivity/grid experiments. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-064 | §5 `study` | Configuration | Set `study.maximum_coalition_order=3`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-065 | §5 `time` | Configuration | Set `time.real_data_epoch_seconds=60`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-066 | §5 `campaign` | Configuration | Set evaluation horizon `60` and prestart warm-up `200` epochs. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-067 | §5 `campaign` | Configuration | Set merge gap `10`, distributed first-activity window `10`, and minimum duration `3` epochs. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-068 | §5 `distributed_support` | Configuration | Set minimum clients `2`, trailing window `5`, and material coalition evidence threshold `1.25`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-069 | §5 `context` | Configuration | Set outside lag `1`, outside minimum clients `2`, minimum fraction `.5`, and rank clip epsilon `1e-12`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-070 | §5 `context` | Configuration | Set histogram bins `8`, primary cells `4`, sensitivity cells `[2,8]`, and nuisance cross-fit folds `5`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-071 | §5 `context.minimum_context_support` | Configuration | Set order support exactly `{1:100,2:200,3:400}`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-072 | §5 `context.kmeans` | Configuration | Set `n_init=20`, max iterations `300`, tolerance `1e-4`, max fit rows `200000`, and assignment tie tolerance `1e-12`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-073 | §5 `basis` | Configuration | Set primary basis size `3` and sensitivities `[2,4]`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-074 | §5 `projection` | Configuration | Set ridge candidates `[0,1e-4,1e-3,1e-2,1e-1,1]`, CV folds `5`, and MSE tie tolerance `1e-12`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-075 | §5 `projection` | Configuration | Set zero-ridge SVD cutoff `1e-12` and maximum Gram condition number `1e6`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-076 | §5 `projection` | Configuration | Set atom-scale and norm-reference floors to `1e-6`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-077 | §5 `evidence` | Configuration | Set bounded clip `1`, lambda `.5`, and norm-reference quantile `.95`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-078 | §5 signed-theorem config | Configuration | Set `arl_alpha=.001`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-079 | §5 finite-horizon config | Configuration | Set target PFA `.05`, confidence `.95`, and candidates `[2,3,5,10,20,50,100,200,500,1000]`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-080 | §5 `evidence` | Configuration | Set no-stop plotting offset to `1` epoch. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-081 | §5 `datasets.corrected_optc` | Configuration | Set directory `data/raw/corrected_optc` and target clients `12`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-082 | §5 `datasets.tc_engagement_5` | Configuration | Set directory `data/raw/tc_engagement_5`, target clients `12`, minimum clients `6`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-083 | §5 `datasets` | Configuration | Set external checksum directory `data/external_checksums`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-084 | §5 dataset eligibility | Configuration | Set minimum benign event records `5000` and nonempty benign epochs `600`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-085 | §5 preprocessing | Configuration | Set event hash buckets `64` and robust-scaling IQR floor `1e-6`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-086 | §5 benign split fractions | Configuration | Set detector `.10`, nuisance `.18`, threshold/policy calibration `.36`, derive heldout remainder. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-087 | §5 Isolation Forest config | Configuration | Set trees `300`, max-samples cap `256`, max-features `1`, jobs `1`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-088 | §5 Isolation Forest definition | Detector | Fix bootstrap off, contamination auto, warm-start off, verbose0, deterministic random state, `max_samples=min(cap,n_fit)`, anomaly score `-score_samples`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-089 | §5 One-Class SVM config/definition | Detector | Implement RBF OCSVM with `nu=.01`, gamma scale formula, coef0, tolerance `.001`, cache `1024MiB`, max-iter `-1`, shrinking on, anomaly score `-decision_function`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-090 | §5 Autoencoder config/definition | Detector / training | Implement `d→32→8→32→d`, ReLU/linear/MSE, Adam `lr=.001`, betas(.9,.999), eps1e-8, wd0, batch128, epochs50, roadmap training/checkpoint semantics. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-091 | §5 Autoencoder definition | Initialization / determinism | Use float32 weights, roadmap Xavier gains/zero biases, reconstruction-MSE score, and batch permutation substreams keyed by root/client/training epoch. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-092 | §5 Detector-family assignment | Deterministic assignment | Sort clients lexicographically and assign IF/OCSVM/AE by zero-based index modulo3 before evaluation labels are inspected. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-093 | §5 local-policy config | Configuration | Set quantiles `[.99,.995,.999,.9995,.9999]`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-094 | §5 local-policy persistence | Configuration | Set exact persistence rules `1-of-1`, `2-of-3`, `3-of-5`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-095 | §5 local-policy config | Configuration | Set primary PFA `.05`, strong PFA `.10`, confidence `.95`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-096 | §5 local-policy definition | Calibration / selection | Derive horizon60, thresholds from nuisance-fit, PFA from independent calibration horizons, exact m-of-n semantics, and least-stringent passing candidate order. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-097 | §5 local-policy definition | Failure semantics | If no candidate qualifies, return Operating Point Unavailable and make dependent claims Not Tested without technical failure. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-098 | §5 randomness | Randomness | Use exact roots: synth dev1000–1029, synth confirm9000–9029, real dev0–9, real confirm9000–9009, smoke999, analysis3000, context4100. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-099 | §5 canonical serialization | Reproducibility / hashing | Use RFC8785 JCS over I-JSON-compatible values encoded UTF-8 for every scientific hash, seed, digest, fingerprint, checksum, and artifact identity. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-100 | §5 canonical serialization | Negative requirement / hashing | Reject NaN/Inf, duplicate keys, lone surrogates, negative zero; never use language-native repr/pickle/YAML/object serialization for scientific hashing. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-101 | §5 canonical serialization | Serialization | Preserve arrays, semantically sort unordered sets before arrays, omit absent optionals, encode explicit null as JSON null, and follow JCS number rules. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-102 | §5 seed derivation | Randomness | Build exact canonical seed object, SHA-256 it, take first64 bits big-endian, reduce mod2^32 only if required, and make spawn order irrelevant. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-103 | §5 synthetic sample sizes | Configuration | Implement nuisance8000, crossfit-eval4000, calibration200, heldout-null1000, self-explanation600+20 settling, pure-order10000, HOFD4000/context/seed, estimator4000/context/seed. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-104 | §5 Common-mode generator | Synthetic generator | Implement stationary AR(1) common mode `rho=.8`, lexical loadings `.6–1.0`, client Gaussian noise SD `.75`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-105 | §5 Controlled campaign generators | Synthetic generator | Implement marginal first-three shift1, pair first-two correlation `0→.6` with uniform marginals, and single-client first-client shift2 with distributed-support blocking. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-106 | §5 Self-explanation generator | Synthetic generator | Reuse one latent/noise realization across perturbations; perturb only target members, discard20 settling epochs, evaluate next600, keep outside process unchanged. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-107 | §5 Self-explanation generator | Mathematics / statistics | Implement roadmap scalar fixture/transforms and OLS-with-intercept derivative estimation; analytic direct derivative is1 and endpoint finite-difference substitution is forbidden. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-108 | §5 Pure-order population completion | Synthetic generator | Use first `r` lexical clients as target, independent U(0,1) non-targets, iid evaluation samples, and roadmap iid warm-up/calibration/campaign/reset semantics. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-109 | §5 Pure polynomial generator | Synthetic generator / validation | Implement `p_theta=1+theta∏phi1`, legal bound, exact rejection sampler/envelope, and Invalid on negative/non-finite density. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-110 | §5 Pure-polynomial grid | Experiment grid | Use exact order1 `[0,.05,.1,.2,.4]`, order2 `[0,.05,.1,.2,.3]`, order3 `[0,.025,.05,.1,.15,.18]`, reference theta `.1`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-111 | §5 XOR generator | Synthetic generator | Implement exact XOR law with strengths `[0,.25,.5,.75,1]`, reference `.5`, continuous jitter ranks, uniform univariate and independent pair marginals. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-112 | §5 Mixed-order generator | Synthetic generator | Implement roadmap phi1 order terms, enabled sets `[1,2],[1,3],[2,3],[1,2,3]`, coefficient `.05`, exact rejection sampler/envelope. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-113 | §5 Context-dependent triple | Synthetic generator | Implement two-state Markov context, same-state `.9`, equal initial probabilities, theta `.1`, outside intervals `[.25,.35]/[.65,.75]`, oracle sees only lagged latent state. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-114 | §5 Outside-contamination generator | Synthetic robustness | Use K12/first-three/theta.1/fractions `[0,.25,.5,1]`, round-half-up count, lexical contaminated outside clients, +.25 clipped rank shift. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-115 | §5 Client-dropout generator | Synthetic robustness | Draw client availability independently with probability `1-f` before evidence for fractions `[0,.1,.25,.5]`; coalition active only with complete members and outside support. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-116 | §5 Comparator calibration | Comparator calibration | Require declared score orientation, nuisance-fit center/scale/reference quantile for sign-agnostic comparators, independent finite-horizon threshold calibration, and no attack-informed normalization. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-117 | §6.1 Dataset authority | Dataset authority | Use official docs/publications for expected structure and actual mounted raw bytes as execution authority. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-118 | §6.1 Dataset authority | Negative requirement / dataset | Never manufacture missing hosts/records/files/labels/time coverage to match expected counts; inventory discrepancies and block only on explicit eligibility or unresolved required semantics. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-119 | §6.1 Adaptation rules 1–4 | Dataset adaptation | Discover raw files first, read release schema before field selection, map fields only when uniquely justified, and record aliases in manifests rather than config. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-120 | §6.1 Adaptation rules 5–7 | Negative requirement / dataset | Never pad/synthesize/truncate/resample records, never invent timestamp/timezone/host/performer/label, and retain unknown structurally valid events. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-121 | §6.1 Adaptation rules 8–10 | Dataset adaptation / scope | Proceed with observed material only when predeclared eligibility/chronology/GT/horizon rules hold; process valid extras; never adapt target counts, eligibility, fractions, horizon, claims, or grids. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-122 | §6.2 Corrected OpTC raw identity | Dataset provenance | Record persistent ID/version, every acquired path/SHA-256/bytes, GT-source SHA, adapter material-code fingerprint, producer commit; MD5 is external cross-check only. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-123 | §6.2 Corrected OpTC client selection | Dataset selection | Define client as canonical host; select benign-eligible first12 by descending event count then host before outcomes; fewer than12 makes primary claim Not Tested with no smaller fallback. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-124 | §6.2 Corrected OpTC benign/evaluation separation | Dataset / leakage | Separate benign/evaluation only via explicit release semantics and official GT; ambiguity is Invalid and dates must not be guessed from filenames when authoritative markers exist. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-125 | §6.2 Corrected OpTC ground truth | Ground truth | Use only explicit official annotations/host-time intervals/deterministic one-to-one host-IP mappings; never heuristically expand malicious labels. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-126 | §6.2 Corrected OpTC ground truth | Ground truth / provenance | Point GT marks containing epoch, intervals use `[start,end)`; ambiguous mappings stay in discrepancy manifest, not silently malicious. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-127 | §6.3 TC Engagement5 client definition/selection | Dataset semantics | Define client `(ta1_performer,canonical_host_id)`, call controlled stream-host, benign-select12 or all6–11; fewer than6 makes secondary claim Not Tested with no replacement. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-128 | §6.3 TC Engagement5 benign interval/GT | Dataset / labels | Use intersection of maximal initial pre-attack stream intervals as benign; no attack annotations in benign; TA3 events take precedence and TA5.1 supplies campaign/completeness context; contradictions are discrepancies. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-129 | §7.1 Duplicate handling | Preprocessing | Prefer authoritative corrected IDs, retain chronological first duplicate, conflicting payload IDs are Invalid absent release rule; otherwise dedupe only complete canonical-record equality and record counts. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-130 | §7.2 Invalid records | Preprocessing | Exclude only unparseable timestamp, unusable host, or structurally invalid event semantics with deterministic reason code; retain unknown structurally valid event types. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-131 | §7.3 Epoch features | Feature engineering | Per client/epoch compute bucket counts→log1p, raw total count, Shannon entropy; empty epochs are all-zero features and never dropped. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-132 | §7.4 Non-finite handling | Negative requirement / preprocessing | Treat non-finite generated feature as failure; prohibit replacement/fill/interpolation/mean imputation/attack-informed repair. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-133 | §7.5 Robust local scaling | Preprocessing / leakage | Fit client-feature median/IQR scaler only on detector_fit with floor and reuse unchanged on every later partition. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-134 | §7.6 Chronological benign partitions | Preprocessing / leakage | Create detector_fit→nuisance_fit→threshold/policy calibration→heldout chronologically with identical client boundaries; no shuffled/random splits. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-135 | §7.6 Eligibility checks | Dataset eligibility | Require at least59 complete non-overlap calibration horizons,59 heldout horizons, and detector-fit sufficiency for every selected client. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-136 | §7.6 Eligibility checks | Negative requirement / failure semantics | If observed data cannot satisfy eligibility, mark affected claim Not Tested; never shorten horizon/lower confidence/overlap CP horizons/merge benign partitions. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-137 | §7.7 Benign horizons | Evaluation | Build consecutive complete non-overlap horizons from split start, discard trailing incomplete block, reset sequential state each horizon, keep prior fitted artifacts fixed. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-138 | §8.1 Exact exclusion | Context method | Use `A^c` at the configured lag as primary context members. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-139 | §8.2 Inclusive context | Ablation | Use all selected clients as lagged context members, intentionally allowing historical coalition information. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-140 | §8.3 Leave-one-out insufficient exclusion | Ablation | Remove only lexicographically first member of `A` from lagged context. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-141 | §8.4 Partial coalition exclusion | Ablation | For triples remove only first two lexical coalition members; for pairs equal leave-one-out. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-142 | §8.5 Oracle outside latent context | Synthetic comparator | Use true lagged outside latent state in four fixed normal-quartile cells with no K-means; synthetic mechanism experiments only. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-143 | §8.6 No outside context | Ablation | Use one global context cell while retaining purification and all enabled orders. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-144 | §8.7 Shuffled outside context | Sensitivity | Deterministically permute lagged outside-context rows within each split; do not shuffle ranks, scores, or attack labels. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-145 | §8.8 Local-history-only context | Sensitivity / violation diagnostic | Build context only from lagged coalition-member ranks as deliberate exact-exclusion violation. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-146 | §8.9 Forced no-abstention | Sensitivity | Pool coalition-specific nuisance-fit reference over contexts when support is insufficient; never use this diagnostic as primary. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-147 | §9 Local detector contract | Training / leakage | Train detectors exclusively on detector_fit; prohibit calibration labels, heldout fitting, attack observations, campaign identities, FedCampaign evidence; preserve score orientation. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-148 | §9 Local-policy contract | Calibration / immutability | Source thresholds from nuisance-fit and PFA from independent calibration; heldout PFA never retunes; freeze detector/scaler/policy and prohibit global-evidence/label/campaign access. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-149 | §10 Baseline/comparator contract | Baseline fairness | Matched comparisons share data, clients, preprocessing, applicable score streams, campaign registry, splits, horizon, PFA target, threshold rule, replay, seeds, latency accounting; differ only in declared evidence representation. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-150 | §10.1 Fixed Local Policies | Baseline | Implement local policies with no global fusion solely as operational local reference. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-151 | §10.2 Raw Mean | Baseline | Compute raw mean marginal-rank fusion, high anomalous, and common nuisance/finite-horizon calibration. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-152 | §10.3 Raw Max | Baseline | Compute raw max marginal-rank fusion, high anomalous, and common nuisance/finite-horizon calibration. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-153 | §10.4 Order-One EMHI | Comparator | Use exact outside context with enabled order `{1}`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-154 | §10.5 Order-at-Most-Two EMHI | Comparator | Use exact outside context/orders `{1,2}` with derived equal weights; primary lower-order causal predecessor. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-155 | §10.6 Full FedCampaign-EMHI | Primary method | Use exact outside context/orders `{1,2,3}`, proper-subset purification, primary basis/context/ridge. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-156 | §10.7 Inclusive Full | Ablation | Full method with only Inclusive Context change. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-157 | §10.8 LOO Full | Ablation | Full method with only Leave-One-Out context change. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-158 | §10.9 Partial Full | Ablation | Full method with only Partial Exclusion context change. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-159 | §10.10 No Purification | Ablation | Exact context but center/scale full tensor directly without proper-subset projection. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-160 | §10.11 No Outside Full | Ablation | One-cell context while retaining all orders and purification. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-161 | §10.12 Conditional HOFD | Comparator / claim boundary | Implement fixed exclusion-matched HOFD in same outside/basis/nuisance/proper-subset space; equivalence comparator only. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-162 | §10.13 Conditional Pair Dependence | Comparator | Implement fixed pair-dependence predecessor with maximum order2 and roadmap score/calibration. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-163 | §10.14 Lancaster Triple | Comparator | Implement fixed finite-dimensional Lancaster-style triple reference without claiming all general variants. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-164 | §10.15 Connected Information | Comparator | Implement configured maximum-entropy lower-order reconstruction reference. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-165 | §10.16 D-Vine | Comparator | Implement fixed lexicographic Gaussian D-vine reference with no family search. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-166 | §10.17 Conditional Log-Linear | Comparator | Implement configured singleton+pair/no-triple lower-order log-linear reference. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-167 | §10.18 Global Factor Residual | Comparator | Implement configured PCA/global-factor residual reference. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-168 | §10.19 Multistream CUSUM | Comparator | Implement configured per-client CUSUM and max fusion with independently calibrated threshold. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-169 | §10.20 FedAvg AE | Comparator / federated training | Implement AE reference with same local-AE architecture/training,50 rounds,1 local epoch, full participation, sample-count weighted float64 aggregation, float32 storage, optimizer reset; detector-fit benign only then ranks+raw mean. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-170 | §10.20 FedAvg AE | Claim boundary | Mark FedAvg AE unmatched ecological context and exclude it from primary causal claim. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-171 | §10.21 Strong Comparator Selection | Comparator selection | Select before real outcomes; eligibility requires invariants and synthetic calibration/heldout PFA; evaluate native-order pure-polynomial targets only. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-172 | §10.21 / §13.5 Strong Comparator Selection | Tie rules | Choose minimum mean standardized target error; within `.01` choose lower median runtime; within `1e-6` choose lexical method; real outcomes never enter selection. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-173 | §13.5 Strong Comparator artifact | Artifact / immutability | Write exact `strongest-comparator-composition.json` contract and keep selected identity immutable until a material dependency changes. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-174 | §11.1 Strict ODI | Metric | Compute `1{T_G<min_i T_i}`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-175 | §11.2 Global stopping time | Metric | Store first global stop; if absent raw null and plotting horizon+offset; censor value never inferential. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-176 | §11.3 Earliest local stop | Metric | Compute `min_i T_i` with raw-null no-stop semantics. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-177 | §11.4 Statistical lead | Metric | Compute `T_local,min-T_G` only for finite paired stops. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-178 | §11.5 Operational lead | Metric | Compute protocol-adjusted lead exactly only for finite paired stops. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-179 | §11.6 Seed ODI rate | Metric / inferential unit | Compute ODI rate over complete fixed campaign registry per seed and use seed-level rate for primary real inference. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-180 | §11.7 Detection rate | Metric | Compute fraction of campaigns with global stop within horizon independently of ODI. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-181 | §11.8 PFA | Metric | Compute finite-horizon PFA and report point estimate plus one-sided exact95% UCB. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-182 | §16 fixed repository tree → `docs/Roadmap.md`; repository authority | Architecture / clarification | Resolve the roadmap's fixed target path `docs/Roadmap.md` without editing the actual authoritative `docs/FedCampaign_EMHI_Roadmap.md`; do not guess rename/copy/alias semantics. | BLOCKED — clarification required | UNMAPPED | Defined | CLARIFICATION_REQUIRED: CLAR-001 |
| REQ-183 | §11.9 False campaigns / 10k | Metric / descriptive | Compute false declarations per10,000 benign epochs as descriptive only. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-184 | §11.10 Signed-route ARL | Metric / claim boundary | Compute mean no-change stopping time as theorem-implementation diagnostic, not substitute theorem evidence. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-185 | §11.11 Self-explanation derivatives | Metric | Compute `D_eta`, `D_R`, and predeclared target-coordinate `D_Z` by roadmap procedures; never select coordinate by observed magnitude. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-186 | §11.11 Self-explanation attenuation | Metric | Compute `A_self` and primary Inclusive-minus-Exact attenuation exactly. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-187 | §11.12 Mean log evidence | Metric | Compute attack-interval mean `log e_{A,t}`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-188 | §11.13 Proper-subset drift | Metric | Compute standardized drift for each proper subset and maximum over proper subsets. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-189 | §11.14 Target-order drift | Metric | Compute signed target-order standardized drift at the predeclared target coordinate. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-190 | §11.15 Order stop probability | Metric | Compute seeded probability independently calibrated specified-order method stops within horizon. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-191 | §11.16 Order evidence share | Metric / descriptive | Compute roadmap order-evidence share descriptively only. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-192 | §11.17 Decisive order | Metric | At global stop choose enabled order with evidence>1 maximizing log evidence; tolerance ties choose smaller order; null if none. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-193 | §11.17 Decisive order | Negative requirement / metric | Never let decisive-order calculation affect stopping. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-194 | §11.18 Atom NRMSE | Metric | Compute exact EMHI-HOFD atom NRMSE. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-195 | §11.19 Atom cosine | Metric | Compute exact EMHI-HOFD atom cosine similarity. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-196 | §11.20 Stopping difference | Metric | Compute EMHI-minus-HOFD stopping-time difference only for finite paired stops. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-197 | §11.20 Stopping difference | Reporting requirement | Always report companion paired detection-indicator difference. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-198 | §11.21 PFA difference | Metric | Compute `PFA_EMHI-PFA_comparison`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-199 | §11.22 Conditional-rank MAE | Metric / synthetic | Compute mean absolute error against known conditional ranks. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-200 | §11.23 Projection NRMSE | Metric / synthetic | Evaluate fitted/population projection on same independent rows and normalize RMSE by full-tensor RMS plus floor. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-201 | §11.24 Null bias | Metric | Compute roadmap standardized null-bias formula. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-202 | §11.25 Coverage | Metric | Supported eligible coalition-epochs divided by eligible coalition-epochs with member/outside availability rules. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-203 | §11.26 Abstention | Metric | Compute `1-context coverage`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-204 | §11.27 Numerical failure | Metric | Compute numerical-invariant failures/attempted fits and exclude ordinary support abstention. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-205 | §11.28 Common-mode suppression | Metric | Compute roadmap suppression formula with denominator floor. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-206 | §11.29 Outside power loss | Metric | Compute `DR_NoOutside-DR_EMHI`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-207 | §11.30 AUROC | Metric / failure semantics | Malicious positive, ties `.5`; return Not Defined with one class. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-208 | §11.31 AUPRC | Metric / failure semantics | Compute average precision with malicious positive; return Not Defined with one class. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-209 | §11.32 Coalition count | Metric / derivation | Derive `sum_{r=1..R} C(K,r)`, primary `R=3`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-210 | §11.33–§11.34 Latency | Timing / claim boundary | Measure exact server and reference-harness computational scopes; exclude real network/disk and never label reference harness real network end-to-end. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-211 | §11.35 Payload bytes | Metric | Use fixed uint16/uint64/float64/uint8/uint8 schema and derive20 logical bytes/client/epoch, headers excluded. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-212 | §11.36 Throughput | Metric | Compute coalitions scored per server-compute second. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-213 | §12 Campaign construction | Campaign registry | Union explicit malicious epochs, form contiguous runs, merge runs separated by at most configured benign gap. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-214 | §12 Campaign eligibility | Campaign registry | Require≥2 participating clients, first-activity spread≤10, inclusive duration≥3, and clean200-epoch warm-up. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-215 | §12 Campaign selection | Negative requirement | Retain every eligible campaign including unfavorable ones; attacks within clean-warmup distance cannot become independent campaigns. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-216 | §12 Campaign identity | Identity / provenance | Use dataset/start/end/sorted participants as semantic key; SHA only integrity, not identity. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-217 | §13.1 Synthetic Module Validation | Validation | Run smoke seed999 and enforce every exact fixture; visual inspection cannot pass. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-218 | §13.1 rank/context fixtures | Validation fixtures | Validate midrank, rank clipping, histogram, context membership, lag semantics, deterministic K-means tie exactly. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-219 | §13.1 projection/crossfit fixtures | Validation fixtures | Validate projection dimensions, ridge tie, support boundary, blocked folds, cross-fit fold/order exactly. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-220 | §13.1 evidence/stopping fixtures | Validation fixtures | Validate signed/norm evidence factors, distributed support, finite threshold, persistence, strict ODI/tie, no-stop storage exactly. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-221 | §13.1 semantic idempotency | Validation fixture | Repeated canonical fixture must produce identical JCS bytes, fingerprint, semantic active path, and one active artifact identity. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-222 | §13.2 Self-Explanation | Experiment | Execute complete K×order×perturbation×five-context×three-transform seed bundles for declared development/confirmatory roots. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-223 | §13.2 Self-Explanation | Acceptance / claim | Primary K12/order3/linear Exact-vs-Inclusive must meet nuisance derivative equivalence, mean attenuation≥.1, adjusted directional test; other rows diagnostic. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-224 | §13.3 Pure-Order | Experiment | Execute declared nine generators/nine methods at K12 grids; primary Pure Continuous Triple/Full/order3/theta.1 across dev/confirm. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-225 | §13.3 Pure-Order purity | Validation / mathematics | Validate pure-polynomial identities, XOR enumeration, context-triple state identity, mixed-term truth before scoring; analytic failure is Invalid, finite-sample drift diagnostic only. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-226 | §13.4 HOFD Equivalence | Experiment | Orders1–3/support sweep share populations/exact context/one cell/basis/subspace/nuisance/heldout; calibrate methods independently; primary supports6400/12800. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-227 | §13.4 HOFD Equivalence | Acceptance / equivalence | Both null-PFA eligible; full95% BCa atom-NRMSE CI<.05, mean cosine≥.99, stopping-difference CI inside[-1,1], companion detection difference. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-228 | §13.4 HOFD Equivalence | Claim boundary | Investigate unexpected superiority; do not market it as expected superiority. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-229 | §13.5 Strong Comparator | Experiment / timing | Use synth dev only; post-fit one warm scoring pass then time one10000-row native-order pass, fitting/I/O excluded, common process/environment. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-230 | §13.6 Estimator Feasibility | Experiment / generator | Generate exact deterministic context-support substrate `c_t=t mod C`, outside midpoint ranks, independent target uniform, one lag row, exactly `nC+1` rows. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-231 | §13.6 Estimator Feasibility | Known truth / metrics | Under zero effect use target rank truth, zero projection, zero/unit atom truth and independent evaluation for MAE/NRMSE/bias/coverage/abstention/condition/failure. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-232 | §13.6 Estimator Feasibility | Grid / claim boundary | Sweep declared supports/orders/settings; sensitivities only `[800,1600]`; confirmatory only primary order3 support400; failed criteria downscope rather than technical fail. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-233 | §13.7 Signed-Theorem | Experiment | Use first-three iid uniform ranks/product phi1 coordinate;100 trajectories/seed max10000; restricted ARL seed means and one-sided95% BCa lower bound. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-234 | §13.7 Signed-Theorem | Validation / acceptance | Mechanically verify fixed coordinate/bound/null/compensator/e-factor/threshold/exclusions; require confirmatory lower ARL bound≥900; never infer real anytime validity. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-235 | §13.7 Finite-Horizon | Experiment | Under common-mode K12 all orders/clients, per seed use200 calibration+1000 heldout null horizons, independent nuisance material, full operational path. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-236 | §13.7 Finite-Horizon | Acceptance / failure semantics | Every confirmatory seed with available threshold meets heldout CP-UCB target; required Operating Point Unavailable remains Completed but route support Not Supported. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-237 | §13.8 Primary Strict ODI | Experiment / baseline | On every eligible Corrected OpTC campaign execute exact ten methods for real dev0–9/confirm9000–9009; Order≤2 primary paired comparator, HOFD equivalence, FedAvg unmatched. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-238 | §13.8 Primary Strict ODI | Acceptance / claim | Require Full PFA eligibility, mean ODI≥.2, paired advantage≥.1, pooled median operational lead≥2, adjusted inference, matched Full/Order≤2 points. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-239 | §13.9 Exclusion Ablation | Experiment / statistics | Execute Full/Inclusive/LOO/Partial across real dev/confirm, report declared metrics, and place three Full-minus-insufficient contrasts in secondary Holm. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-240 | §13.10 Purification/Order Ablation | Experiment / claim | Execute Full/NoPurification/Order1/Order≤2 and compute real Full-minus-Order≤2 ODI contribution≥.02 gate alongside controlled support. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-241 | §13.11 Context/Estimator Sensitivity | Development-only | Real dev only; reuse matching primary artifacts, change one factor at a time, recompute only changed descendants; never replace primary values or claim from unadjusted sensitivity p. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-242 | §13.12 Common-Mode Robustness | Experiment | Run Full/RawMean/Inclusive/NoOutside over real dev/confirm with heldout-benign negative and same eligible-campaign positive branches; never create attacks from benign. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-243 | §13.12 Common-Mode Robustness | Stress construction | Use native non-overlap horizons; rolling60 stride1 top1% volume windows with ties diagnostic only; count factors before log1p/total, preserve entropy, no rounding, recompute from first changed layer. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-244 | §13.12 Common-Mode Robustness | Acceptance / negative | Count-stress remains benign/out of campaign power; matched Full-vs-NoOutside campaign power; require suppression≥.5, power-loss≤.1, adjusted RawMean-Full high-volume p<alpha. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-245 | §13.13 Strong Local | Experiment / reuse | Reuse unchanged primary Full global artifacts, change only strong-local policy across real dev/confirm; require ODI≥.2 and adjusted shifted test. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-246 | §13.14 Secondary Trace | Experiment / scope | If eligible, execute six declared methods across real dev/confirm and restrict interpretation to a second controlled provenance trace. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-247 | §13.15 Outside Contamination | Experiment / scope | Run K12/first-three/theta.1/fractions `[0,.25,.5,1]` across synth dev/confirm, report drift/detection/coverage/abstention/null-PFA; claim only tested boundary. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-248 | §13.16 Dropout/Context Sparsity | Development-only | Run K `[6,12,24,48]` × dropout `[0,.1,.25,.5]` on synth dev, report declared metrics, create no independent support claim. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-249 | §13.17 Coalition Scalability | Timing / scope | Run K `[6,12,24,48]`, orders1–3 for real dev/confirm timing roots with exact synthetic production-dimensional workload; timing evidence only. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-250 | §13.17 Coalition Scalability | Timing workload | Create lexical clients,8000 detector-fit rows/client under configured common-factor law, production detector mix, independent nuisance/context stream/full EMHI; record fit time separately. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-251 | §13.17 Coalition Scalability | Timing fallback semantics | If local/global timing operating point unavailable, use only roadmap fallback candidate to exercise timing path, mark unavailable, and prohibit fallback from PFA/ODI/detection support. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-252 | §13.17 Coalition Scalability | Measurement procedure | Preload, warm100, measure5×600, reset global/local state per repetition, concurrency1, exclude I/O/loading/preprocess/fits/calibration, measure exact latency/RSS scopes. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-253 | §13.17 Coalition Scalability | Metrics / acceptance | Report all declared timing/resource metrics; confirmatory requires pooled numerical failure≤.01 and aggregate p95 harness latency≤30s every K under one common environment. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-254 | §13.17 Coalition Scalability | Claim boundary | Restrict timing/scalability statements to recorded in-process environment; do not imply real network latency/production deployment. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-255 | §14.1 Controlled unit | Statistics | Generator root seed is independent controlled unit; within-seed clients/coalitions/contexts/time/perturbations/effects are repeated measurements. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-256 | §14.2 Real unit | Statistics | Real algorithm root seed after complete fixed-campaign aggregation is independent; ten seed-level values are paired sample, not campaign×seed rows. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-257 | §14.3 Pairing key | Statistics / provenance | Paired real comparisons require identical roadmap pairing key; intentionally unmatched methods are excluded from primary causal inference. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-258 | §14.4 Real sign-flip | Statistics | For10 confirmatory seeds enumerate all1024 sign assignments exactly under declared one-/two-sided rule and retain zeros. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-259 | §14.5 Synthetic sign-flip | Statistics | Exact if `2^n≤100000`; otherwise exactly100000 deterministic assignments from analysis seed, observed all-positive once, `(1+extreme)/(1+B)` correction, retain zeros. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-260 | §14.6 BCa | Statistics / failure semantics | Paired BCa with10000 seed resamples preserving pairing; exact degeneracy interval is point interval; any other BCa failure is Invalid with no percentile fallback. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-261 | §14.7 Hierarchical bootstrap | Statistics / scope | Use campaign+seed hierarchical bootstrap only for secondary descriptive intervals; never replace seed-level primary inference. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-262 | §14.8 Hodges-Lehmann | Statistics | Compute median of all Walsh averages `(d_i+d_j)/2`, `i≤j`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-263 | §14.9 Equivalence | Statistics / negative | Equivalence requires entire configured CI inside region; nonsignificance is never equivalence. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-264 | §14.10 Primary Holm | Statistics / multiplicity | Keep exactly five one-sided primary hypotheses named in roadmap. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-265 | §14.10 Secondary Holm | Statistics / multiplicity | Keep exactly six one-sided Full-minus-ablation ODI hypotheses named in roadmap. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-266 | §14.10 Not Tested Holm | Statistics / failure semantics | Scientific raw/adjusted p remain null/Not Tested; separate `holm_input_p=1` preserves family size only. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-267 | §14.11 Holm correction | Statistics | Sort p ascending with lexical hypothesis-ID tie-break; apply standard sequential Holm reproducibly. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-268 | §14.12–§14.13 Exact binomial intervals | Statistics | One-sided exact CP for PFA selection/heldout; two-sided equal-tail95% CP for other binary descriptive proportions; PFA failure is valid but claim-ineligible. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-269 | §14.14 Materiality aggregation | Statistics | Mean ODI/advantage over confirmatory seeds; operational lead criterion pooled median only over Full strict-ODI cells while inference remains seed-level. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-270 | §14.15 Missing/failed cells | Failure semantics | Never impute confirmatory values; no-stop/unfavorable/operating-point outcomes valid; retries exhausted→Failed; provenance/leakage/schema/math→Invalid; mandatory missing tolerance zero. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-271 | §15.1 Order3 feasibility downscope | Downscope | Failed confirmatory order3 feasibility blocks Supported order3 claim, retains executed results, discloses limitation, and forbids post-hoc support/context rescue. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-272 | §15.2 No calibrated real threshold | Downscope | Full no operating point→Strict ODI Not Supported/no new threshold grid; Order≤2 no matched point→superiority Not Tested while Full absolute evidence remains. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-273 | §15.3 Secondary ineligibility | Downscope | Secondary eligibility failure→Not Tested, unchanged contribution scope, no post-hoc replacement dataset. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-274 | §15.4 Real order3 null contribution | Downscope | Controlled order3 passes but real contribution<.02→Mechanism Only; no material real order3 wording. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-275 | §16 Fixed repository tree | Architecture | Implement roadmap top-level structure, outputs/results ownership, package boundaries, and tests hierarchy. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-276 | §16 configs/data tree | Architecture | Create production/test/smoke configs, immutable `data/raw→/external/datasets` symlink, external checksums. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-277 | §16 package tree | Architecture | Implement exact responsibility modules and do not move responsibilities when science/artifact ownership would change. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-278 | §16 architecture tests | Engineering quality | Enforce dependency boundaries, meaningful typed interfaces, no inappropriate Any/object/anonymous dict payloads, no primitive leaks. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-279 | §16 architecture tests | Engineering quality | Reject hardcoded governed values, duplicated owners/constants, dead/obsolete code, unused enums, and test-only production code. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-280 | §16 architecture tests | Engineering quality / negative | Reject redirects/shims/legacy aliases/transitional wrappers/re-export-only modules; enforce canonical descriptive vocabulary and no artificial version naming. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-281 | §16 architecture tests | Engineering quality / negative | Reject Python comments/docstrings/TODO/FIXME/HACK/XXX/commented-out/temp residue; enforce strict Pyright, Ruff, dependency hygiene. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-282 | §16 tests tree | Testing architecture | Implement exact unit package coverage and named scientific/integration/e2e/smoke test files. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-283 | §16 Public CLI | CLI | Expose only `fedcampaign` with exact commands `doctor`, `preprocess`, `plan`, `smoke`, `run`, `status`, `report` and declared arguments. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-284 | §16 Public CLI | Negative requirement / CLI | Expose no public run-ID/UUID/lifecycle/seed/method/order/basis/context/threshold/PFA/statistical/sensitivity scientific overrides. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-285 | §16 Public CLI | Runtime / reuse | Every mutating command validates/reuses compatible ancestors, invalidates only descendants, rebuilds minimum subgraph, atomically publishes, and never duplicates shared work across experiments. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-286 | §16.1 doctor | CLI / read-only | Report exhaustive readiness/reuse/staleness/confirmatory state/next action; never mutate; commit/lock are trace-only, not universal invalidators. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-287 | §16.2 preprocess | CLI | Execute roadmap preprocessing layers with optional dataset scope, validating/reusing each layer independently. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-288 | §16.2 preprocess | Overwrite semantics | `preprocess --overwrite` rebuilds requested preprocessing ownership only; no model/score/analysis force; only changed material identity stales descendants. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-289 | §16.3 plan | CLI / read-only | Display dependencies/datasets/methods/seeds/cell counts/grids/dev-confirm obligations/readiness/reuse/stale/resume; derive counts, never manually configure them. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-290 | §16.3 plan | Execution identity | Use default outer-cell granularity exactly, with only roadmap-declared immutable within-seed bundles. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-291 | §16.4 smoke | CLI | Execute Synthetic Module Validation; reuse valid completion; overwrite same spec only; do not invalidate real artifacts absent genuine invariant defect. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-292 | §16.5 run | CLI / execution | Resolve authoritative dependency graph, validate/reuse layers, rebuild minimum subgraph, compute fixed metrics/stats/gates, validate provenance/invariants, atomically publish. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-293 | §16.5 run | Execution role / resume | Automatically run missing development then eligible confirmatory cells; no role selector/second-phase command; interrupted identical run resumes. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-294 | §16.5 run | Overwrite semantics | `run --overwrite` recomputes target experiment-owned artifacts at same semantic paths, not compatible shared prerequisites; descendants only if material identity changes. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-295 | §16.6 status | CLI / read-only | Report expected dev/confirm cells, scientific/technical states, blockers, paths, reusable ancestors, stale descendants, nearest resume. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-296 | §16.7 report | CLI / reporting | Perform no new science/stats; export only current verified evidence, gate claims on complete mandatory confirmatory cells, confine report overwrite invalidation to report descendants. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-297 | §16.8 CLI ownership | Architecture / ownership | Enforce exact per-command create/replace and must-not-implicitly-regenerate ownership table. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-298 | §16.9 Command sequence | Execution order / resume | Support exact authoritative command order; repeated identical `run` resumes missing cells and never creates a second scientific result. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-299 | §17.1 Scientific identity | Identity | Scientific cell identity contains only roadmap semantic coordinates; timestamps/UUIDs/hashes/attempts/run IDs never define identity or independence. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-300 | §17.1 Scientific identity | Artifact paths / reuse | Same semantic cell resolves to same active paths; reusable artifact identity is separate and shareable without duplication. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-301 | §17.2 Dependency map | Dependency graph | Implement complete experiment prerequisite/producer/consumer/reuse map. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-302 | §17.2 Dependency map | Negative requirement / duplication | Identical prepared data/models/scores/fits/calibrations/evaluations under identical dependencies use one reusable artifact identity. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-303 | §17.3 Dependency fingerprints | Provenance / hashing | Compute dependency fingerprint and artifact identity exactly from canonical material dependency and content records. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-304 | §17.3 Dependency fingerprints | Negative requirement / identity | Exclude attempts/timestamps/staging/producer commit labels from artifact identity. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-305 | §17.3 Dependency fingerprints | Provenance | Material dependency record contains only value-changing upstream/config/data/model/score/fit/calibration/condition/analysis/material-code/material-library and applicable runtime inputs. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-306 | §17.3 Dependency fingerprints | Code provenance | Maintain artifact-family→transitively executed material-code mapping; never default fingerprint to entire repository. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-307 | §17.3 Dependency fingerprints | Trace-only provenance | Record commit/full-lock/unrelated code/tests/docs/format/log/time for traceability, never universal invalidation. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-308 | §17.4 Reuse | Artifact reuse | Reuse only when role/fingerprint/upstreams/content/schema/invariants/atomic completion all validate. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-309 | §17.4 Atomic completion | Atomicity / negative | Stage→hash/validate→atomic publish completion; directory/RUNNING/log/partial file without completion is never reusable. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-310 | §17.4 Cell completion | Completion gate | Complete cell only when all required outputs/reusable refs/metrics/stats/source records/declared undefined values/finite rules/keys/completion validate. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-311 | §17.5 Selective invalidation | Invalidation | Implement roadmap invalidation boundaries for every artifact family. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-312 | §17.5 Selective invalidation | Invalidation / reuse | Changed parent identity stales only referencing descendants; equivalent recompute preserves compatible descendants. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-313 | §17.6 States | State model | Implement exact experiment/cell state vocabularies. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-314 | §17.6 States | Execution role / staleness | Execution role immutable; staleness is compatibility, and stale completions are excluded from synthesis. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-315 | §17.6 States | Failure semantics | Operating Point Unavailable is Completed attribute; exhausted technical retries→Failed; provenance/leakage/schema/math violations→Invalid; unfavorable science→Completed. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-316 | §17.7 Recovery | Recovery | Validate oldest ancestor first, retain compatible work, find first broken boundary, deactivate only descendants, resume nearest compatible, atomically replace, rerun only stale descendants. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-317 | §17.7 Recovery | Negative requirement / invalidation | Later experiment failure never invalidates prior work without dependency change; stale/partial/corrupt/Failed/Invalid active cells cannot remain selectable. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-318 | §17.7 Overwrite | Overwrite semantics | Preserve scientific inputs/identity, no duplicate rows/run_2, no recursive compatible-ancestor overwrite, descendants only on changed identity. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-319 | §17.7 Technical attempts | Technical-attempt boundary | Attempts/timestamps only in logs/cache/staging/provenance, never active scientific state/stats/report/manuscript evidence. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-320 | §17.8 Checkpoints | Checkpoint / resume | Reuse checkpoint only under exact semantic/upstream/config/model/fit/seed/material compatibility; automatic recovery resumes latest compatible boundary. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-321 | §17.8 Caches | Cache semantics | Cache non-authoritative, exact-compatible only; deleting all caches cannot change science. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-322 | §17.9 Logs | Logging / evidence | Logs diagnose technical failures but are never parsed as scientific/manuscript evidence. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-323 | §17.9 Dependency index | Dependency index | Maintain rebuildable derived dependency index with exact roadmap fields; never independent scientific truth. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-324 | §18.1 Evidence boundary | Artifact boundary | `outputs/` is complete generated computational workspace/only generated scientific input; `results/` terminal verified evidence and never consumed scientifically. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-325 | §18.1 Evidence boundary | Negative requirement / reporting | Never let stale/Failed/Invalid/partial/debug/cache content become manuscript evidence. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-326 | §18.1 Namespaces/lifecycle | Architecture / lifecycle | Implement exact outputs/results namespaces and Staging→Validated→Active+Atomically Published lifecycle; only active completed artifacts consumable. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-327 | §18.2 Artifact ownership | Ownership | Every reusable artifact has exactly one producer contract; first needing command may invoke producer, later consumers reuse active identity. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-328 | §18.3 Dataset/preprocess provenance | Provenance schema | Implement exact dataset-inventory key/fields and preprocessing-manifest source/code/dependency/content/count/dimension/client/partition/horizon/discrepancy fields. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-329 | §18.4 Campaign provenance | Provenance schema | Implement exact campaign-registry key and required duration/client/warmup/horizon/eligibility/integrity/fingerprint/completion fields. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-330 | §18.5 Cell manifest | Provenance schema | Record all roadmap scientific-cell coordinate/state/config/data/client/campaign/upstream/fitted/fingerprint/code/dependency/commit/lock/environment/warning/failure/runtime/output/completion fields. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-331 | §18.5 Cell manifest | Compatibility | Commit/full lock trace-only generally; runtime environment affects validity only where scientific value is environment-dependent, especially timing. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-332 | §18.6 Result/analysis records | Evidence schema | Implement exact keys/required fields for campaign, benign-horizon, seed-summary, and statistical records with source identities/fingerprints/content hashes. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-333 | §18.6 Statistical invalidation | Selective invalidation | Material statistical-code change invalidates affected stats/report descendants only unless evaluation logic also changed. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-334 | §18.7 Figure/table sources | Reporting provenance | Every manuscript figure/table has exactly one verified outputs machine-readable source with required hashes/paths; no log or manual console copying. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-335 | §18.7 Claim registry | Claim registry | Record exact claim wording/experiments/metrics/stat rule/materiality/failure/scope/forbidden extrapolation/supporting artifacts/state/reason/source hashes. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-336 | §18.7 Claim registry | Artifact boundary | Claim registry is materialized only under project-summary results as reporting descendant and never used by scientific execution. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-337 | §18.8 Reproducibility export | Reproducibility | Export exact per-experiment evidence and project reproducibility configuration/datasets/seeds/software/execution identities and plans. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-338 | §18.8 Reproducibility export | Provenance | Resumed unchanged campaigns may record multiple producer commits while retaining exact per-artifact provenance without implying unaffected recomputation. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-339 | §19.1 Execution roles | Confirmatory governance | Confirmatory roots are independent inferential samples; development roots never reused as claim-bearing samples. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-340 | §19.1 Execution roles | Negative requirement / confirmatory | Development may diagnose/verify prerequisites but never change confirmatory scientific values, selection, grids, metrics, claim thresholds, directions, multiplicity. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-341 | §19.1 Confirmatory eligibility | Confirmatory eligibility | Run confirmatory cell only when prerequisites/current fingerprints/comparator/data identities/config validity/quantity availability satisfy roadmap. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-342 | §19.2 Confirmatory obligations | Completeness | Implement exact per-experiment obligations; zero mandatory missing technical cells, distinct from predeclared scientific Not Tested. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-343 | §19.3 Timing environment | Timing provenance | All claim-bearing scalability K cells share exact roadmap environment identity fields. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-344 | §19.3 Timing environment | Validation / timing | `doctor` records environment; scalability validates exact equality, mismatch Invalid only for cross-K claim; constant threads/concurrency1/in-process/no I/O/monotonic/GPU sync. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-345 | §19.3 Timing environment | Claim boundary | Every latency acceptance statement names/cites recorded environment and remains reference-harness computational scope. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-346 | §19.4 Synthesis completeness | Synthesis gate | Before claim materialization verify mandatory confirm cells, current provenance, complete Holm families, required intervals, evaluable/Not-Tested gates, mechanical claim rules, and no `results/` input. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-347 | §19.4 Synthesis completeness | Negative requirement / reporting | `report` cannot repair missing scientific evidence; stop with precise missing dependency. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-348 | §20.1 Source-data rule | Reporting | Generate each manuscript table/figure from compact machine-readable source data derived only from current verified outputs with required metadata. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-349 | §20.1 Source-data rule | Negative requirement / reporting | `report` may only select/sort/reshape/label/round; never recompute metrics/CIs/p-values/gates/claim states; machine values stay full precision. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-350 | §20.2 Dataset/evidence table | Reporting / table | Generate exact dataset/evidence-role source/rendered table; observed values come from validated manifests, not literature. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-351 | §20.3 Numerical protocol table | Reporting / table | Generate authoritative numerical-protocol table directly from production config with exact columns; no manually duplicated numerical registry. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-352 | §20.4 Detector/policy table | Reporting / table | Generate exact local-detector/policy configuration table. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-353 | §20.5 Baseline fairness table | Reporting / table | Generate exact baseline-fairness table and strong-comparator selection supplementary table. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-354 | §20.6 Self-explanation table | Reporting / table | Generate exact self-explanation-results source/rendered table. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-355 | §20.7 Pure-order/HOFD tables | Reporting / tables | Generate exact experiment-local and project-summary pure-order/HOFD tables. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-356 | §20.8 Feasibility/sequential tables | Reporting / tables | Generate exact order3-feasibility and sequential-validation tables. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-357 | §20.9 Primary ODI table | Reporting / table | Generate exact primary strict-ODI table in configured method order with all declared columns. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-358 | §20.10 Other result tables | Reporting / tables | Generate every specified ablation/sensitivity/robustness/strong-local/secondary/contamination/dropout/scalability source/rendered table at exact paths/columns. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-359 | §20.11–§20.18 Figures | Reporting / figures | Generate every specified manuscript figure/source artifact with exact axes/groups/facets/uncertainty/reference/denominator semantics. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-360 | §20.18 Vector figures | Reporting / consistency | Render PDF and SVG from same source data with numerically identical values; PNG optional. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-361 | §20.19 Project summary | Reporting / claims | Generate exact claim-summary, primary-evidence, source-data, and claim-registry paths; one row/claim and no new primary-evidence aggregate. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-362 | §20.19 Project summary | Claim registry authority | Claim registry is manuscript-state authority; prose cannot exceed permitted claim/scope/forbidden-extrapolation. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-363 | §21 Claim states | Claim state model | Support exactly SUPPORTED, PARTIALLY_SUPPORTED, MECHANISM_ONLY, CONDITIONAL, NULL_RESULT, NOT_SUPPORTED, NOT_TESTED from current verified artifacts. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-364 | §21 Claim states | Failure semantics | Technical/provenance defects block claim evaluation until repaired; NOT_TESTED only for predeclared scientific/data eligibility unavailability. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-365 | §21.1 `CLAIM_EMII_ADMISSIBLE_INFORMATION` | Claim rule | SUPPORTED only with complement math/tests/provenance/no-current-target/smoke and eligible real ablation with ≥1 positive insufficient-exclusion contrast, adjusted p<alpha. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-366 | §21.1 `CLAIM_EMII_ADMISSIBLE_INFORMATION` | Claim rule | MECHANISM_ONLY when controlled mechanism passes but real directional consequence unavailable/fails; NOT_SUPPORTED only on valid complement contradiction. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-367 | §21.2 `CLAIM_SELF_EXPLANATION` | Claim rule | SUPPORTED only with direct fixture, exact D_eta BCa equivalence, mean attenuation≥.1, adjusted primary p<alpha. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-368 | §21.2 `CLAIM_SELF_EXPLANATION` | Claim rule | NULL_RESULT when valid identity not contradicted but material/inference fails; NOT_SUPPORTED on valid exact-exclusion contradiction. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-369 | §21.3 `CLAIM_PURE_ORDER_SEPARATION` | Claim rule | SUPPORTED only with analytic purity, proper-subset drift≤.1, target drift≥.5, adjusted p<alpha; MECHANISM_ONLY if estimator feasibility fails; NOT_SUPPORTED on valid purity/target failure. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-370 | §21.4 `CLAIM_SEQUENTIAL_CONSEQUENCE` | Claim rule / boundary | CONDITIONAL only with theorem assumptions/implementation and restricted-ARL lower bound≥900; NOT_SUPPORTED on valid contradiction; never unconditional real-data SUPPORTED. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-371 | §21.5 `CLAIM_STRICT_ODI` | Claim rule | SUPPORTED only with matched eligible Full/Order≤2 PFA, Full ODI≥.2, advantage≥.1, median lead≥2, adjusted p<alpha. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-372 | §21.5 `CLAIM_STRICT_ODI` | Claim rule | Apply exact PARTIALLY_SUPPORTED/NULL_RESULT/NOT_SUPPORTED/NOT_TESTED state conditions and wording restrictions. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-373 | §21.6 `CLAIM_ORDER_THREE_SCOPE` | Claim rule | SUPPORTED requires pure-order Supported + estimator feasible + real contribution≥.02; apply exact mechanism/not-supported/not-tested states; never imply >order3. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-374 | §21.7 `CLAIM_OPERATIONAL_FEASIBILITY` | Claim rule | SUPPORTED requires common environment, failure≤.01, p95 harness≤30s every K, no timing fallback, primary median lead≥2. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-375 | §21.7 `CLAIM_OPERATIONAL_FEASIBILITY` | Claim rule / boundary | Apply exact Conditional/Not Supported/Not Tested conditions and restrict wording to tested K/in-process environment. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-376 | §22 Research grounding | Research grounding / datasets | Ground expected dataset semantics in official Corrected OpTC/DARPA TC docs while raw bytes remain execution authority. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-377 | §22 Research grounding | Research grounding / theorem | Ground signed sequential claim only in cited e-detector ARL theory and separate it from operational finite-horizon PFA. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-378 | §22 Research grounding | Claim boundary / comparators | Use HOFD/connected-information/copula literature only to ground fixed comparator adaptations; claim neither new HOFD nor all literature variants. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-379 | §22 Research grounding | Reproducibility | Use RFC8785 exactly and do not add Unicode normalization beyond explicit dataset-specific normalization. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-380 | §23 Readiness | Readiness gate | Implementation may begin only when production config validates, raw inventory checks execute, fixed validators are implementable, and no mandatory scientific/architectural choice remains unspecified. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-381 | §23 Readiness | Dataset adaptation | Resolve release-dependent facts only through deterministic raw validation/adaptation; never invented literature constants; surface discrepancies via provenance and predeclared state semantics. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-382 | §23 Readiness | Failure semantics | Treat unfavorable science, unavailable operating points, abstention, dataset ineligibility as executable outcomes; repair technical/provenance/leakage/schema/math/fingerprint failures before interpretation. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-383 | §5 OpTC event canonicalization | Preprocessing / canonicalization | Canonicalize `NFKC(upper(strip(object)))::NFKC(upper(strip(action)))`; missing values become `UNKNOWN_OBJECT`/`UNKNOWN_ACTION`; retain if host/timestamp valid. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-384 | §5 TC5 event canonicalization | Preprocessing / canonicalization | Only CDM event records enter counts; canonicalize `EVENT::` + NFKC uppercase stripped enum; unknown→`EVENT::UNKNOWN_EVENT_TYPE`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-385 | §5 Event hash mapping | Preprocessing / deterministic hashing | SHA-256 canonical event UTF-8, first8 bytes unsigned big-endian modulo64; never language-randomized hash. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-386 | §5 Timestamp configuration | Preprocessing / time | Normalize UTC using schema unit/explicit offsets; naive text invalid absent documented dataset timezone; never machine timezone. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-387 | §5 Epoch configuration | Preprocessing / time | Epoch index is `floor(unix_seconds/60)`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-388 | §5 Comparator common config | Configuration | Set reference quantile `.95`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-389 | §5 Connected Information config | Configuration | Set bins4, pseudocount.5, IPF max10000/error1e-8, probability floor1e-12. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-390 | §5 Conditional Log-Linear config | Configuration | Set bins4, fit max10000/tolerance1e-8, probability floor1e-12. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-391 | §5 HOFD config | Configuration | Set SVD cutoff1e-12 and ridge0. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-392 | §5 Factor Residual config | Configuration | Set candidate ranks `[1,2,3]`, variance target `.8`, fallback3. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-393 | §5 CUSUM config | Configuration | Set center `.5`, drift `.05`, initial0. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-394 | §5 FedAvg config | Configuration | Set rounds50, local epochs1, participation1. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-395 | §5 Numerics/statistics config | Configuration | Set numerical floors/tolerances1e-12, smoke repeatability1e-8, confidence.95, alpha.05, BCa10000, synthetic non-exact sign-flips100000. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-396 | §5 Self-explanation materiality | Configuration / materiality | Set derivative equivalence fraction `.05`, minimum attenuation `.10`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-397 | §5 Pure-order materiality | Configuration / materiality | Set max proper-subset drift `.10`, min target drift `.50`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-398 | §5 Order3-estimator materiality | Configuration / materiality | Set min coverage `.80`, max NRMSE `.10`, max bias `.05`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-399 | §5 Numerical-failure materiality | Configuration / materiality | Set max pooled numerical-failure rate `.01`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-400 | §5 HOFD-equivalence materiality | Configuration / equivalence | Set NRMSE margin `.05`, min cosine `.99`, stopping-difference interval `[-1,1]`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-401 | §5 Primary-real materiality | Configuration / materiality | Set min ODI `.20`, min advantage `.10`, min pooled median operational lead `2`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-402 | §5 Common-mode materiality | Configuration / materiality | Set min suppression `.50`, max power loss `.10`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-403 | §5 Strong-local materiality | Configuration / materiality | Set min ODI `.20`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-404 | §5 Real order3 materiality | Configuration / materiality | Set min mean ODI contribution `.02`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-405 | §5 Operational-feasibility materiality | Configuration / materiality | Set max p95 reference-harness latency `30s`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-406 | §5 Estimator support grids | Configuration / experiment grid | Primary `[100,200,400,800,1600,3200]`, sensitivity `[800,1600]`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-407 | §5 HOFD support grid | Configuration / experiment grid | Set `[800,1600,3200,6400,12800]`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-408 | §5 Benign count-stress grid | Configuration / experiment grid | Set `[1.25,1.5,2.0]`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-409 | §5 Scalability grid | Configuration / experiment grid | Set client counts `[6,12,24,48]`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-410 | §5 Timing config | Configuration / timing | Set repetitions5, warm-up100, epochs/repetition600, concurrency1, quantile.95. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-411 | §5 Runtime config | Configuration / retry | Exactly two retries after initial technical failure; retries preserve scientific inputs/seeds and reuse compatible checkpoints/ancestors; required missing-confirmatory tolerance0. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-412 | §5 Reporting config | Configuration / reporting | Use outputs/results roots; display precision probs/effects3, epochs/min1, ms/sec2, adjusted p4, lower p `.0001`; no significance stars; machine precision retained. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-413 | §5 Dropout support derivation | Derivation | Required outside count is `max(min_clients,ceil(.5*|A^c|))`. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-414 | §5 Conditional Pair details | Comparator | Score `(2U_i-1)(2U_j-1)`, cross-fitted benign standardize, absolute standardized nonconformity; max order2. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-415 | §5 Lancaster details | Comparator | Score triple product `(2U_i-1)(2U_j-1)(2U_k-1)`, benign center/scale, absolute standardized magnitude. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-416 | §5 Connected Information details | Comparator | Equal4-bin ranks, Jeffreys .5, uniform-initialized IPF pair-maxent with configured tolerances, log density-ratio cell score then absolute standardization. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-417 | §5 Conditional Log-Linear details | Comparator | Fit intercept+singletons+pairs/no triple lower-order model; raw score `-log p_lower-order(cell)` then common nuisance calibration. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-418 | §5 D-Vine details | Comparator | Lexical `i<j<k`, Gaussian rho from Kendall tau, Gaussian h-functions, absolute highest-tree log-density; no family search. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-419 | §5 Global Factor Residual details | Comparator | Mean-center ranks/no variance scale, deterministic full SVD, smallest rank reaching.8 else fallback3, score L2 residual. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-420 | §5 CUSUM details | Comparator | `Y=U-.5`, `C_t=max(0,C_{t-1}+Y-.05)`, global max, independently finite-horizon calibrate. | UNMAPPED | UNMAPPED | Defined | — |
| REQ-421 | §5 Projection condition rule | Numerics / failure semantics | Compute unregularized `X'X` condition after removing exact constant zero-variance columns; abstain on support unavailable/nonfinite/condition-limit/provenance mismatch. | UNMAPPED | UNMAPPED | Defined | — |

## 4. Non-Implementation-Bearing Roadmap Content

| Roadmap Subsection | Source Location | Content Summary | Implementation Consequence | Linked Requirement IDs |
| --- | --- | --- | --- | --- |
| Research identity and motivation | Roadmap title, preamble, §1 prose | Names FedCampaign-EMHI, ODI, EMII and explains the scientific story. | Terminology and claim boundaries bind where separately extracted; narrative itself adds no extra code. | REQ-006–REQ-019 |
| Research questions as narrative | §3 | States questions answered by the fixed experiment/claim contracts. | No implementation beyond separately extracted experiments, metrics, statistics, and claim gates. | REQ-019; §13/§21 requirements |
| Dataset background expectations | §6 descriptive notes | Describes expected release structure and literature context. | Expected structure is not execution truth; raw bytes/adaptation rules govern. | REQ-117–REQ-137, REQ-383–REQ-387 |
| Research-grounding prose/citations | §22 | Positions official dataset docs, e-detector theory, HOFD, connected information, copulas, JCS. | Constrains interpretation/identity; adds no unlisted algorithms/claims. | REQ-376–REQ-379 |
| Readiness conclusion prose | §23 | Explains roadmap implementation-readiness subject to validation/failure semantics. | Adds no new feature; closes readiness authority chain. | REQ-380–REQ-382 |

## 5. Clarification Register

| Clarification ID | Source Location | Ambiguity or Conflict | Affected Requirements | Blocking Scope | GitHub Issue | Resolution Status |
| --- | --- | --- | --- | --- | --- | --- |
| CLAR-001 | §16 fixed tree → `docs/Roadmap.md`; current repository authority | Roadmap target tree calls `docs/Roadmap.md` the authoritative repository copy, while the actual authoritative immutable roadmap is `docs/FedCampaign_EMHI_Roadmap.md` and the planning authority says the roadmap filename is not fixed and must never be edited. Implementation must not guess rename, duplicate-copy, or alias semantics. | REQ-182 | Only future repository-path realization of the roadmap document; unrelated planning remains unblocked. | UNMAPPED | Open — clarification required |

## 6. Requirement-to-Milestone Summary

| Mapping State | Requirement Count | Notes |
| --- | ---: | --- |
| `UNMAPPED` | 420 | Expected at Phase 1; replace with actual GitHub milestone ownership during planning reconciliation. |
| `BLOCKED — clarification required` | 1 | CLAR-001; unrelated planning remains unblocked. |
| `MAPPED` | 0 | Milestones not yet created at this extraction point. |

## 7. Requirement-to-Issue Summary

| Mapping State | Requirement Count | Notes |
| --- | ---: | --- |
| `UNMAPPED` | 421 | Implementation issues have not yet been reconciled. |
| `MAPPED` | 0 | Must be populated before final global planning audit can pass. |

## 8. Unmapped Requirement Review

- Total requirements: **421**.
- Currently unmapped to implementation issues: **421**.
- Phase-1 extraction is complete; `UNMAPPED` is intentional until milestone/issue creation.
- Overall completion requires every implementation-bearing requirement to resolve to exactly one owning milestone and one or more concrete implementation issues, except explicitly blocked clarification scope.
- No requirement may be silently dropped because it is unfavorable, operationally inconvenient, negative, diagnostic-only, development-only, or expected to produce Not Tested/Not Supported.

## 9. Negative Requirement Review

- Negative/scope/forbidden-behavior obligations are explicitly first-class requirements.
- Covered categories include novelty/claim boundaries, privacy/robustness prohibitions, leakage prevention, post-hoc tuning bans, dataset non-invention, no imputation, CLI override bans, duplicate-run bans, selective invalidation, no log-derived manuscript evidence, terminal `results/`, timing/deployment scope, and claim-language restrictions.
- Applicable negative requirements must appear in downstream issue tests/acceptance criteria.

## 10. Dependency Review

- The inventory captures prerequisite lifecycle, experiment graph, reusable-artifact producer/consumer rules, selective invalidation, command ownership, development/confirmatory sequencing, and terminal reporting.
- GitHub dependency edges are not yet instantiated; downstream issue creation must translate them without circular or duplicate ownership.
- CLAR-001 is intentionally narrow and must not block unrelated planning.

## 11. Acceptance Evidence Review

- **421 / 421** requirements have a source-defined, objectively checkable contract and carry `Defined` status.
- `Defined` does not mean implemented/verified; downstream issues must identify the concrete tests/artifacts/evidence proving linked requirements.
- `Verified` is assigned only after implementation evidence exists and milestone audit validates it.

## 12. Final Inventory Audit Log

| Audit | Independent Perspective | Result | Defects Found and Resolution |
| ---: | --- | --- | --- |
| 1 | Roadmap omission / full-section coverage | Re-audited — pass | Normalized fixed configuration/scientific-definition locations to §5; automated section check now covers every §1–§23. |
| 2 | Atomicity / independent verification | Re-audited — pass | Split compound proper-subset, aggregation, metric, context, baseline, configuration, and materiality rows; remaining lists are single schema/namespace contracts. |
| 3 | Negative constraints / exclusions | Audited — pass | Confirmed explicit coverage of forbidden claims, leakage barriers, post-hoc bans, dataset non-invention, no-imputation, run-identity, reporting, and deployment/order bounds. |
| 4 | Scientific semantics / mathematics | Audited — pass | Re-derived strict ODI, complement admissibility, current-epoch exclusion, ranks, cross-fitting, purification, recursion, support, finite-horizon calibration, replay. |
| 5 | Datasets / preprocessing / configuration | Re-audited — pass | Added previously underrepresented event canonicalization, timestamps, hash bucketing, comparator constants, materiality/support grids, reporting precision and rechecked §5–§7. |
| 6 | Experiment matrix / controls / ablations / robustness | Audited — pass | Confirmed explicit representation of every experiment §13.1–§13.17 including development-only/confirmatory scope, controls, comparator selection, ablations, boundaries, fallbacks. |
| 7 | Statistics / multiplicity / uncertainty | Audited — pass | Confirmed seed-level units, exact1024 real sign-flips, deterministic synthetic fallback, paired BCa/no fallback, HL, CP, equivalence, fixed Holm5+6, Not Tested bookkeeping. |
| 8 | Artifacts / provenance / reproducibility / reporting | Audited — pass | Re-derived semantic identity, JCS, material fingerprints/code scope, atomic publication/completion, caches/logs, dependency index, outputs/results boundary, source data, claim registry. |
| 9 | Dependencies / ordering / ownership / resume | Audited — pass | Checked prerequisite/experiment graphs, shared reuse, ancestor-first repair, stale descendants, command ownership, strong-local reuse, one-factor sensitivities, operational sequence. |
| 10 | Fresh hostile re-derivation / claim boundaries | Re-audited — pass | Fresh reread found the `docs/Roadmap.md` vs immutable current-roadmap conflict; isolated as CLAR-001 instead of guessing. Re-derived all seven claim contracts and forbidden extrapolations. |

## 13. Completion Gate

- [x] Entire authoritative roadmap read before extraction.
- [x] Every roadmap section 1–23 represented in inventory or non-implementation content register.
- [x] Implementation, mathematics, configuration, datasets, preprocessing, experiments, metrics, statistics, artifacts, provenance, CLI/runtime, tests, failure semantics, assumptions, terminology, negative requirements, exclusions, and claim boundaries extracted.
- [x] At least ten independent audits completed with defects repaired and re-audited.
- [x] Requirement identifiers assigned deterministically and ready to become stable once referenced by GitHub issues.
- [x] Genuine ambiguity isolated without editing/reinterpreting roadmap.
- [ ] Every requirement mapped to an actual GitHub milestone.
- [ ] Every implementation-bearing requirement mapped to actual GitHub issue(s).
- [ ] Every clarification linked to its dedicated GitHub issue.
- [ ] Every milestone has exactly one milestone-audit issue.
- [ ] Exactly one global-roadmap-audit issue exists and passes.
- [ ] Bidirectional roadmap ↔ inventory ↔ milestone ↔ issue ↔ audit reconciliation passes with no actionable defect.

**Phase-1 inventory extraction status:** `Re-audited — pass`.

**Overall planning-system status:** `IN PROGRESS — downstream GitHub mappings not yet created/reconciled`.
