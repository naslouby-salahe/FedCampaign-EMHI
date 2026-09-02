# FedCampaign-EMHI — Authoritative Research Roadmap

**Contribution:** FedCampaign-EMHI — Exclusion-Matched Hierarchical Innovation
**Research object:** Operational Distributed Insufficiency (ODI)
**Theoretical principle:** Exclusion-Matched Irreducible Innovation (EMII)
**Maximum implemented coalition order:** `study.maximum_coalition_order`
**Scientific authority:** this roadmap

This roadmap is the scientific and execution specification for the study. Implementation may mirror it in typed code, but no external plan, user-editable configuration, undocumented default, or post-hoc implementation choice may alter its scientific contract.

## Protocol amendment 1 — primary cohort support correction

**Status:** adopted before inspection of any method, detection, false-alarm, effect, or
claim result.  **Scope:** TON_IoT Network primary real-data cohort only.

The originally specified 12-client primary cohort was found, during raw-input and
preprocessing validation, to have no common benign interval from which the required
detector-fit, nuisance-fit, calibration, and held-out partitions could all be formed.
That is a data-availability failure, not an unfavorable method outcome.  The primary
cohort size is therefore revised to four clients, selected by the unchanged benign-only
eligibility ranking in Section 6.2.  This is the largest leading ranked cohort in the
observed release with adequate common benign support for all required partitions.

This amendment changes only `datasets.primary.target_client_count` from 12 to 4.
It does not change the client-eligibility minima, client ordering, campaign definition,
held-out partition proportions, methods, operating-point calibration, inferential
thresholds, multiplicity families, effect directions, or seeds.  Artifacts produced
under the previous 12-client material digest are not evidence for this amended primary
protocol; the amended digest and selection record are the authoritative provenance.

## Protocol amendment 2 — secondary trace availability finding

**Status:** observed during raw-input and preprocessing validation. **Scope:**
Edge-IIoTset secondary trace only.

The configured release contains two eligible source-host identities under the unchanged
benign-event and nonempty-epoch rules: `192.168.0.128` and `192.168.0.101`. This is
below the predeclared minimum eligible-client count of six. Secondary controlled-trace
generalization therefore remains `Not Tested`; the implementation must not fabricate
clients, relax the eligibility rule, or represent this release as a 12-client trace.

This finding changes no scientific threshold, method, seed, or eligibility policy. It
records the measured release limitation and the required unavailable-evidence outcome.

---

# 1. Conceptual execution lifecycle

```text
Repository and Environment Validation
→ Raw Dataset Inventory
→ Deterministic Preprocessing
→ Synthetic Module Validation
→ Local Detector Validation
→ EMHI Estimator Validation
→ Sequential Evidence Validation
→ Self-Explanation Validation
→ Pure-Order Validation
→ Exclusion-Matched HOFD Validation
→ Strongest Comparator Composition Selection
→ Primary Real-Data Evaluation
→ Mechanism Ablations
→ Robustness and Strong-Local Challenge
→ Secondary Trace Generalization
→ Failure-Boundary and Scalability Evaluation
→ Analysis Code Validation
→ Confirmatory Statistical Synthesis
→ Claim Registry Materialization
→ Manuscript Evidence Materialization
```

This lifecycle defines scientific prerequisite order. It does not imply that every later invocation reruns every earlier computation.

Execution is artifact-first and resumable. At every command boundary the required behavior is:

```text
validate existing artifacts
→ reuse compatible artifacts
→ identify stale descendants
→ remove stale descendants from active scientific consideration
→ recompute only missing or invalidated artifacts
→ continue from the nearest valid dependency boundary
```

The reusable computational spine is:

```text
raw inputs
→ prepared epoch data and deterministic splits
→ fitted local detectors
→ detector score streams
→ nuisance/context/projection and cross-fitted calibration artifacts
→ sequential calibration/threshold artifacts
→ campaign and benign-horizon evaluations
→ seed-level summaries and statistical analysis
→ tables/figures/claim registry/reporting
```

An artifact remains valid after a later experiment fails, after a technical retry, or after an unrelated code change unless one of that artifact's material dependencies changes. Invalidation is therefore selective: an invalidated artifact invalidates only its downstream descendants, never unrelated ancestors, siblings, or completed experiments.

A downstream step is blocked only by a mandatory prerequisite that is technically Failed, scientifically/provenance Invalid, or explicitly Not Tested where that prerequisite is necessary for the downstream claim.

A correctly executed unfavorable scientific outcome remains Completed. It must never be converted into Failed or rerun merely because the result is unfavorable.

---

# 2. Scientific identity and claim boundaries

## 2.1 Operational Distributed Insufficiency

There are $K$ monitored clients. Client $i$ exposes a fixed local detector score

$$
S_{i,t}=f_i(X_{i,t}),
$$

where larger $S_{i,t}$ means greater local suspicion.

Each client also owns a fixed local policy $\pi_i$ with stopping time

$$
T_i=\inf{t:\pi_i\text{ acts at }t}.
$$

The federation independently produces a statistical global stopping time

$$
T_G.
$$

The local policies never participate in computing $T_G$.

Strict ODI is

$$
\boxed{
T_G\lt \min_iT_i.
}
$$

The strict ODI indicator is therefore

$$
I_{ODI} =
\mathbf 1
\left\lbrace
T_G\lt \min_iT_i
\right\rbrace.
$$

A global statistical stop that occurs at or after the earliest local action is still recorded as a global detection; it simply does not qualify as ODI.

This separation is mandatory so that ODI is measured rather than enforced by construction.

## 2.2 EMII principle

For every coalition $A\subseteq[K]$, nuisance information used to explain $A$ must be generated only from predictable information belonging to the complement $A^c$.

Under the admissible outside information, the order-$|A|$ innovation is the component of the coalition representation that cannot be represented by any proper subcoalition.

The novelty claim ends at this information-admissibility principle and its operational consequences.

The study does not claim novelty for:

* Hoeffding or functional-ANOVA decompositions;
* hierarchical orthogonal functional decomposition;
* Hilbert-space projection;
* empirical ranks or conditional PITs;
* copulas;
* Lancaster/Streitberg interactions;
* connected information;
* vine decompositions;
* e-values or e-processes;
* e-detectors;
* CUSUM;
* Shiryaev-Roberts recursions;
* federated averaging;
* generic distributed anomaly fusion.

## 2.3 Manuscript claims

The exact permitted claims, mandatory evidence, and claim-state rules are defined once in Section 21.

## 2.4 Forbidden extrapolations

The manuscript must not claim:

* formal privacy or cryptographic privacy;
* differential privacy;
* Byzantine robustness;
* poisoning robustness;
* causal identification;
* distribution-free validity under arbitrary concept drift;
* independence of clients merely because they are represented as clients;
* natural cross-company federation from host-level controlled traces;
* production-SOC deployment readiness;
* network-latency performance beyond the reference harness;
* behavior above `study.maximum_coalition_order`;
* universal scalability beyond the tested client-count range;
* superiority to exclusion-matched conditional HOFD when both target the same population subspace;
* real-data anytime validity unless a separate theorem-quality conditional-null argument is established.

---

# 3. Research questions and predeclared support criteria

| Research question                                                                                         | Predeclared support rule                                                                                                                                                                                                                                |
| --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Does exact coalition exclusion suppress self-explanation?                                                 | Exact-exclusion nuisance derivative must lie within the configured equivalence margin around zero; inclusive context must show at least the configured material attenuation difference; the primary directional test must pass the primary Holm family. |
| Can a pure order-$r$ alternative preserve all proper subsets while the order-$r$ term moves?              | Every proper-subset standardized drift must satisfy the configured upper bound while target-order drift satisfies the configured lower bound and the directional test passes.                                                                           |
| Is the finite order-3 estimator feasible at its declared minimum support?                                 | Mean context coverage, projection NRMSE, standardized null bias, and pooled numerical-failure rate must satisfy the configured feasibility criteria.                                                                                                    |
| Is the internal projection practically equivalent to exclusion-matched conditional HOFD at large support? | The complete paired CI for atom NRMSE and stopping-time difference must lie inside their configured equivalence regions and cosine similarity must meet its configured minimum.                                                                         |
| Does FedCampaign-EMHI establish material strict ODI on TON_IoT Network?                                    | Full FedCampaign-EMHI must pass held-out PFA, mean strict-ODI rate, ODI advantage over the exclusion-matched order-$\le2$ predecessor, operational-lead materiality, and adjusted directional inference.                                                |
| Does outside conditioning suppress hard benign coordination without excessive campaign-power loss?        | Common-mode false-campaign suppression and campaign-power-loss criteria must both pass.                                                                                                                                                                 |
| Does ODI persist against the predeclared stronger local policy?                                           | Mean strict-ODI rate under the strong local policy must meet its configured minimum and adjusted directional inference.                                                                                                                                 |
| Is execution practical at the declared scale?                                                             | Numerical failure and reference-harness p95 latency must meet their configured limits for every client count in `robustness.scalability_client_counts`; any practical early-warning wording additionally requires the primary operational-lead criterion. |

No claim threshold, equivalence margin, comparator, effect setting, metric, test direction, multiplicity family, development seed, or confirmatory seed may be changed in response to observed outcomes. These quantities are fixed by this roadmap.

---

# 4. Mathematical specification

## 4.1 Information fields

Let $\mathcal F^G_{t-1}$ be the global history available before current-epoch evidence is formed.

Let $\mathcal H_{i,t-1}$ denote the predictable history generated by client $i$.

For coalition $A$,

$$
\boxed{
\mathcal G^{-A}_{t-1} =
\sigma
\left(
\bigcup_{j\notin A}
\mathcal H_{j,t-1}
\right).
}
$$

The admissible nuisance family is

$$
\mathfrak G_A(t-1) =
\left\lbrace
\mathcal G:
\mathcal G\subseteq
\mathcal G^{-A}_{t-1}
\right\rbrace.
$$

The population principle uses the maximal admissible outside field.

The implementation uses a deterministic compressed context

$$
C^{-A}_{t-1}
$$

that is measurable with respect to $\mathcal G^{-A}_{t-1}$.

No current-epoch observation from any member of $A$ may enter the exact-exclusion nuisance representation.

## 4.2 Marginal suspicion rank

For client $i$, with benign reference scores $s_1,\ldots,s_{n_i}$,

$$
U^M_{i,t} =
\frac{
\left\lvert\lbrace k:s_k\lt S_{i,t}\rbrace\right\rvert
+\frac12\left\lvert\lbrace k:s_k=S_{i,t}\rbrace\right\rvert
+\frac12
}{
n_i+1
}.
$$

This deterministic midrank orientation ensures that larger rank means greater local suspicion.

The rank is clipped using `context.rank_clip_epsilon` from the Configuration YAML.

## 4.3 Outside-context histogram

For a coalition $A$, the exact-exclusion implementation uses previous-epoch marginal ranks of available complement clients.

Let $J^{-A}_t\subseteq A^c$ be the outside clients declared available for epoch $t$ before current evidence is computed.

Then

$$
H^{-A}_{t-1} =
\frac{1}{|J^{-A}_t|}
\sum_{j\in J^{-A}_t}
e(B(U^M_{j,t-1})),
$$

where $B(\cdot)$ is the equal-width histogram-bin map defined by the authoritative histogram-bin count.

If the outside-availability support rule is not met, coalition $A$ abstains.

The histogram edges are derived from the configured bin count and $[0,1]$; they are not separately configurable.

## 4.4 Context clustering

Context centroids are fitted separately for:

```text
dataset
coalition_order
context_method
experiment_seed when the upstream detector scores are seed-dependent
```

For exact exclusion, training rows are pooled deterministic coalition/epoch histograms of the same order.

If the number of candidate rows exceeds `context.kmeans.max_fit_rows`, the implementation retains the rows with the smallest deterministic SHA-256 ranking values computed from:

```text
context_seed
dataset
coalition_order
coalition_client_ids
epoch_index
```

The cap therefore does not depend on iteration order.

K-means assignments use Euclidean distance.

If two centroid distances differ by no more than `context.kmeans.assignment_tie_tolerance`, the smaller centroid index is selected.

## 4.5 Coalition-conditioned residual ranks

For member $i\in A$ and context cell $c$,

$$
U^{(-A)}_{i,t} =
\widehat F_{i,A,c}
\left(
U^M_{i,t}
\right),
$$

where $\widehat F_{i,A,c}$ is the empirical CDF obtained from nuisance-fit epochs assigned to context $c$ for coalition $A$.

The same midrank convention as Section 4.2 is mandatory.

If the coalition/context support is below the order-specific configured minimum, the coalition abstains.

## 4.6 Bounded basis

For $u\in[0,1]$,

$$
\phi_1(u)=\sqrt3(2u-1),
$$

$$
\phi_2(u)=\sqrt5(6u^2-6u+1),
$$

$$
\phi_3(u)=\sqrt7(20u^3-30u^2+12u-1),
$$

$$
\phi_4(u) =
3
\left(
70u^4-140u^3+90u^2-20u+1
\right).
$$

The primary basis uses the first `basis.primary_size` functions.

A sensitivity setting uses the configured alternative prefix length.

For coalition $A$,

$$
\Phi_A(U_A) =
\bigotimes_{i\in A}
\varphi(U_i).
$$

Its dimension is derived as

$$
L^{|A|}.
$$

## 4.7 Proper-subset design

For coalition $A$, the lower-order design uses the same coalition-specific outside context as the full coalition.

For order 1:

* context-specific centering only.

For order 2:

* intercept;
* every singleton basis coordinate for both members.

For order 3:

* intercept;
* every singleton basis coordinate;
* every pair tensor-basis coordinate for the three proper pairs.

No interaction of the same order as $A$ is included in the design.

## 4.8 Ridge projection

Within a context cell,

$$
\widehat M_{A,c} =
\arg\min_M
\frac1n
\sum_s
\left\|
\Phi_{A,s} -
M^\top X_{\lt A,s}
\right\|_2^2
+
\lambda
\left\|M_{\text{penalized}}\right\|_F^2.
$$

The intercept is not penalized.

No predictor-column rescaling is performed.

All projection linear algebra uses float64.

The ridge candidate set, blocked-fold count, MSE tie tolerance, SVD relative cutoff, and condition-number limit are numerical configuration values. Contiguous blocked folds, fold-size-weighted MSE selection, the larger-$\lambda$ tie resolution, intercept handling, and SVD solution semantics are fixed algorithmic rules in this section.

The selected $\lambda$ minimizes fold-size-weighted benign validation MSE.

Candidates whose MSE values differ by at most `projection.selection_tie_tolerance_mse` are tied; the larger $\lambda$ wins.

For $\lambda=0$, the Moore-Penrose solution is computed by SVD with the configured relative singular-value cutoff.

### Contiguous blocked-fold construction

Every contiguous blocked split in nuisance cross-fitting and projection cross-validation uses the same deterministic boundary rule. For $n$ chronologically ordered observations and $k$ folds, let

$$
q=\left\lfloor\frac nk\right\rfloor,
\qquad
r=n\bmod k.
$$

Folds are numbered from zero. The first $r$ folds contain $q+1$ consecutive observations and the remaining $k-r$ folds contain $q$ consecutive observations. No observation is shuffled. Fold boundaries are therefore identical to splitting the ordered index array into $k$ contiguous parts whose sizes differ by at most one, with any remainder assigned to the earliest folds.

If $n\lt k$, the requested fit is unsupported and abstains rather than silently reducing the fold count.

The atom is

$$
\widehat Z_{A,t} =
\Phi_A(U^{(-A)}_{A,t}) -
\widehat M_{A,c}^\top
X_{\lt A,t}.
$$

## 4.9 Cross-fitted benign innovation calibration

The nuisance-fit split is divided into the configured number of contiguous blocked folds.

For each fold:

1. marginal CDFs are fitted on the other folds;
2. context centroids are fitted on the other folds;
3. conditional-rank references are fitted on the other folds;
4. the projection is fitted on the other folds;
5. held-fold innovations are computed.

The concatenated held-fold innovations are the only observations used to estimate benign atom centering, scaling, and operational norm calibration.

After those cross-fitted calibration statistics are fixed, final marginal/context/projection artifacts are refitted on the complete nuisance-fit split for later scoring.

This prevents the threshold-calibration split from being reused for atom fitting or atom-scale estimation.

## 4.10 Centering and scaling

For atom coordinate $j$,

$$
\widetilde Z_{A,t,j} =
\frac{
\widehat Z_{A,t,j}-\widehat\mu_{A,c,j}
}{
\max
(
\widehat\sigma_{A,c,j},
\texttt{projection.atom＿scale＿floor}
)
}.
$$

$\widehat\mu$ and $\widehat\sigma$ are computed from cross-fitted nuisance-fit innovations.

The standard deviation convention is sample standard deviation with denominator $n-1$.

A context with fewer than two cross-fitted observations is unsupported.

## 4.11 Signed theorem evidence

Signed evidence is used only when an alternative direction is mathematically fixed before evaluation.

For a predeclared unit vector $v_A$,

$$
X^{signed}_{A,t} =
\mathrm{clip}
\left(
v_A^\top
\widetilde Z_{A,t},
-b,
b
\right),
$$

with $b=\texttt{evidence.clip＿bound}$.

For the pure polynomial generators, $v_A$ selects the tensor coordinate containing $\phi_1$ for every member of $A$, with sign fixed by the generator coefficient.

Under the declared conditional-null contract

$$
E_0[
X^{signed}_{A,t}
\mid
\mathcal F^G_{t-1}
]
\le0,
$$

the one-step evidence factor is

$$
e^{signed}_{A,t} =
\exp
\left(
\lambda X^{signed}_{A,t} -
\frac{\lambda^2(2b)^2}{8}
\right).
$$

For the locked values $b=1$ and $\lambda=0.5$, the compensator is $0.125$.

This signed-theorem sequential construction is the only evidence path used to support the conditional e-detector statement.

## 4.12 Operational norm evidence

The primary real-data path is sign-agnostic.

For coalition/context $A,c$, let

$$
q^{norm}_{A,c} =
Q_{\texttt{evidence.operational＿norm＿reference＿quantile}}
\left(
|\widetilde Z_{A,t}|_2
\right)
$$

over cross-fitted nuisance-fit innovations.

Then

$$
X^{norm}_{A,t} =
\mathrm{clip}
\left(
\frac{
\left\|\widetilde Z_{A,t}\right\|_2
}{
\max
(
q^{norm}_{A,c},
\texttt{projection.norm＿reference＿floor}
)
}
-1,
-b,
b
\right).
$$

The operational evidence factor is

$$
e^{op}_{A,t} =
\exp
\left(
\lambda X^{norm}_{A,t} -
0.125
\right).
$$

This transform is not described as an anytime-valid real-data e-value.

Its real-data error semantics come from independent finite-horizon calibration of the complete stopping procedure.

## 4.13 Within-order aggregation

For active order $r$,

$$
E_t^{(r)} =
\frac{
1
}{
N_{\text{active},r,t}
}
\sum_{\substack{|A|=r\\A\text{ active}}}
e^{op}_{A,t}.
$$

If no coalition of order $r$ is active,

$$
E_t^{(r)}=1.
$$

## 4.14 Across-order aggregation

Enabled orders receive equal weight.

If $\mathcal R$ is the enabled order set,

$$
E_t =
\frac1{|\mathcal R|}
\sum_{r\in\mathcal R}
E_t^{(r)}.
$$

The equal weight is derived from the enabled-order set and is not configured separately.

Contemporaneous coalition evidence factors are never multiplied in the primary method.

## 4.15 Sequential recursion

The global state is

$$
G_0=0,
\qquad
G_t=(G_{t-1}+1)E_t.
$$

For a threshold $h$, the threshold predicate is

$$
G_t\ge h.
$$

A statistical global stop occurs at the first epoch satisfying both:

1. the threshold predicate;
2. the distributed-support predicate.

Local-policy state never alters $G_t$ and never suppresses the statistical stop.

## 4.16 Distributed-support predicate

A coalition is materially active when

$$
e^{op}_{A,t}
\ge
\texttt{distributed＿support.material＿coalition＿evidence＿threshold}.
$$

At epoch $t$, form the union of clients appearing in materially active coalitions during the configured trailing support window.

The support predicate is true when the union contains at least the configured number of distinct clients.

The support predicate may delay a threshold stop.

It may never lower a statistical threshold.

## 4.17 Signed-Theorem Sequential Route

signed-theorem sequential route uses the signed theorem evidence.

The e-SR threshold is the reciprocal of `evidence.signed_theorem_sequential.arl_alpha`.

The resulting claim is restricted to the average-run-length semantics justified by the inherited e-detector theory, which provides nonasymptotic ARL control under its required e-process assumptions.

signed-theorem sequential route is not used to justify the primary real-data finite-horizon PFA claim.

## 4.18 Calibrated Finite-Horizon Route

The real-data contract is

$$
P_0(T_G\le H)
\le
\texttt{evidence.calibrated＿finite＿horizon.target＿pfa},
$$

where $H$ is `campaign.evaluation_horizon_epochs`.

Candidate thresholds are evaluated on non-overlapping benign calibration horizons.

For a candidate threshold with $x$ false stops among $n$ horizons, the one-sided Clopper-Pearson upper bound is

$$
U=
\begin{cases}
1,&x=n,\\[4pt]
\mathrm{Beta}^{-1}
\left(
\texttt{evidence.calibrated＿finite＿horizon.calibration＿confidence};
x+1,n-x
\right),&x\lt n.
\end{cases}
$$

The selected threshold is the smallest candidate from `evidence.calibrated_finite_horizon.threshold_candidates` with

$$
U\le
\texttt{evidence.calibrated＿finite＿horizon.target＿pfa}.
$$

The minimum horizon count needed even for a zero-false-stop calibration to potentially pass is derived from the target PFA and confidence level; with the authoritative values it is 59.

If no candidate qualifies, the scientific outcome is:

```text
Operating Point Unavailable
```

not Invalid.

The cell remains Completed, but it is not eligible for a matched-PFA superiority claim.

The threshold is never modified using held-out benign data.

## 4.19 Campaign-anchored replay

For each real campaign:

1. the configured clean pre-campaign warm-up must exist;
2. lagged contexts are computed through the warm-up;
3. at campaign start, global sequential state is reset to $G=0$;
4. local persistence windows are reset;
5. global and local policies are evaluated independently for the configured campaign horizon.

This makes campaign detection delay comparable across methods while finite-horizon false-alarm behavior is measured separately on held-out benign horizons.

## 4.20 Lead

Statistical lead is

$$
L_{stat} =
\min_iT_i-T_G.
$$

Reference-harness latency is measured in seconds.

Operational lead is

$$
L_{op} =
\min_iT_i -
\left(
T_G+
\frac{\delta_{\text{seconds}}}
{\texttt{time.real＿data＿epoch＿seconds}}
\right).
$$

Operational lead is defined only when both the global stop and earliest local stop are finite.

---

# Configuration YAML

This section is the single authoritative source of user-supplied, technically selectable, or experiment-grid values. The production study uses one authoritative scientific configuration file, `configs/fedcampaign-emhi.yaml`. `configs/tests.yml` and `configs/smoke.yml` are reduced non-production configurations for automated tests and smoke execution and cannot alter the claim-bearing scientific configuration. Fixed formulas, procedures, architectures, scoring definitions, validation rules, provenance rules, failure semantics, derivations, and reporting semantics are defined in the relevant roadmap sections rather than encoded as configuration data.

A value's presence in YAML does not make it scientifically free to tune. Primary-study values are scientifically locked; only values explicitly consumed by a declared sensitivity or experiment grid may vary in that declared role. Derived values are computed by the implementation from the primitive values below and are not separately configurable.

```yaml
study:
  maximum_coalition_order: 3

time:
  real_data_epoch_seconds: 60

campaign:
  evaluation_horizon_epochs: 60
  prestart_warmup_epochs: 200
  merge_max_intervening_benign_epochs: 10
  distributed_first_activity_window_epochs: 10
  minimum_duration_epochs: 3

distributed_support:
  minimum_clients: 2
  trailing_window_epochs: 5
  material_coalition_evidence_threshold: 1.25

context:
  outside_lag_epochs: 1
  minimum_available_outside_clients: 2
  minimum_available_outside_fraction: 0.5
  rank_clip_epsilon: 1.0e-12
  outside_histogram_bin_count: 8
  primary_cell_count: 4
  cell_count_sensitivity: [2, 8]
  kmeans:
    n_init: 20
    max_iterations: 300
    tolerance: 0.0001
    max_fit_rows: 200000
    assignment_tie_tolerance: 1.0e-12
  minimum_support_epochs:
    order_one: 100
    order_two: 200
    order_three: 400
  nuisance_crossfit:
    fold_count: 5

basis:
  primary_size: 3
  sensitivity_sizes: [2, 4]

projection:
  ridge_candidates: [0.0, 0.0001, 0.001, 0.01, 0.1, 1.0]
  cross_validation:
    fold_count: 5
  selection_tie_tolerance_mse: 1.0e-12
  zero_ridge_svd_relative_cutoff: 1.0e-12
  maximum_gram_condition_number: 1000000.0
  atom_scale_floor: 1.0e-06
  norm_reference_floor: 1.0e-06

evidence:
  clip_bound: 1.0
  bet_lambda: 0.5
  operational_norm_reference_quantile: 0.95
  signed_theorem_sequential:
    arl_alpha: 0.001
  calibrated_finite_horizon:
    target_pfa: 0.05
    calibration_confidence: 0.95
    threshold_candidates: [2, 3, 5, 10, 20, 50, 100, 200, 500, 1000]
  no_stop_plot_offset_epochs: 1

datasets:
  primary:
    name: TON_IoT Network
    raw_directory: data/raw/TON-IoT/Processed_datasets/Processed_Network_dataset
    target_client_count: 4
  secondary:
    name: Edge-IIoTset
    raw_directory: data/raw/Edge-IIoTset/Edge-IIoTset dataset/Selected dataset for ML and DL/DNN-EdgeIIoT-dataset.csv
    target_client_count: 12
    minimum_eligible_client_count: 6
  external_checksums_directory: data/external_checksums
  eligibility:
    minimum_benign_event_records: 5000
    minimum_nonempty_benign_epochs: 600
  preprocessing:
    event_type_hash_bucket_count: 64
    robust_scaling_iqr_floor: 1.0e-06
    benign_partition_fractions:
      detector_fit: 0.1
      nuisance_fit: 0.18
      threshold_and_policy_calibration: 0.36

detectors:
  isolation_forest:
    trees: 300
    max_samples_cap: 256
    max_features: 1.0
    jobs: 1
  one_class_svm:
    nu: 0.01
    coefficient_zero: 0.0
    solver_tolerance: 0.001
    kernel_cache_mib: 1024
    max_iterations: -1
  autoencoder:
    learning_rate: 0.001
    betas: [0.9, 0.999]
    optimizer_epsilon: 1.0e-08
    weight_decay: 0.0
    batch_size: 128
    epochs: 50

local_policy:
  candidate_score_quantiles: [0.99, 0.995, 0.999, 0.9995, 0.9999]
  candidate_persistence:
    - required_exceedances: 1
      window_epochs: 1
    - required_exceedances: 2
      window_epochs: 3
    - required_exceedances: 3
      window_epochs: 5
  primary_horizon_pfa_target: 0.05
  strong_horizon_pfa_target: 0.1
  pfa_confidence: 0.95

randomness:
  synthetic_development_roots: [1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010, 1011, 1012, 1013, 1014, 1015, 1016, 1017, 1018, 1019, 1020, 1021, 1022, 1023, 1024, 1025, 1026, 1027, 1028, 1029]
  synthetic_confirmatory_roots: [9000, 9001, 9002, 9003, 9004, 9005, 9006, 9007, 9008, 9009, 9010, 9011, 9012, 9013, 9014, 9015, 9016, 9017, 9018, 9019, 9020, 9021, 9022, 9023, 9024, 9025, 9026, 9027, 9028, 9029]
  real_development_roots: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
  real_confirmatory_roots: [9000, 9001, 9002, 9003, 9004, 9005, 9006, 9007, 9008, 9009]
  engineering_smoke_root: 999
  statistical_analysis_base_seed: 3000
  context_base_seed: 4100

synthetic:
  sample_sizes:
    generic_nuisance_fit_epochs: 8000
    generic_cross_fitted_evaluation_epochs: 4000
    finite_horizon_calibration_horizons_per_seed: 200
    finite_horizon_heldout_null_horizons_per_seed: 1000
    self_explanation_epochs_per_perturbation: 600
    self_explanation_lag_settling_epochs_discarded: 20
    pure_order_independent_evaluation_samples_per_condition_seed: 10000
    hofd_equivalence_heldout_samples_per_context_seed: 4000
    estimator_evaluation_samples_per_context_seed: 4000

generators:
  common_mode:
    latent_ar_coefficient: 0.8
    client_loading_minimum: 0.6
    client_loading_maximum: 1.0
    client_noise_standard_deviation: 0.75
  controlled_campaigns:
    marginal:
      score_shift: 1.0
    pair_relation:
      benign_correlation: 0.0
      campaign_correlation: 0.6
    single_client:
      score_shift: 2.0
  self_explanation:
    perturbations: [-0.2, -0.1, -0.05, 0.0, 0.05, 0.1, 0.2]
    derivative_regression_perturbations: [-0.1, -0.05, 0.0, 0.05, 0.1]
  pure_polynomial:
    theta:
      order_one: [0.0, 0.05, 0.1, 0.2, 0.4]
      order_two: [0.0, 0.05, 0.1, 0.2, 0.3]
      order_three: [0.0, 0.025, 0.05, 0.1, 0.15, 0.18]
    primary_reference_theta: 0.1
  xor:
    strengths: [0.0, 0.25, 0.5, 0.75, 1.0]
    primary_reference_strength: 0.5
  mixed_order:
    enabled_term_sets:
      - [1, 2]
      - [1, 3]
      - [2, 3]
      - [1, 2, 3]
    term_coefficient: 0.05
  context_dependent_triple:
    markov_same_probability: 0.9
    initial_state_probabilities:
      negative_one: 0.5
      positive_one: 0.5
    primary_theta: 0.1
    outside_rank_intervals:
      negative_state: [0.25, 0.35]
      positive_state: [0.65, 0.75]
  outside_contamination:
    client_count: 12
    target_triple_theta: 0.1
    correlated_campaign_fractions: [0.0, 0.25, 0.5, 1.0]
    outside_rank_shift: 0.25
  client_dropout:
    unavailable_fractions: [0.0, 0.1, 0.25, 0.5]

comparators:
  common_calibration:
    nuisance_reference_quantile: 0.95
  connected_information:
    bins_per_client: 4
    jeffreys_pseudocount_per_cell: 0.5
    ipf_max_iterations: 10000
    maximum_marginal_absolute_error: 1.0e-08
    probability_floor: 1.0e-12
  conditional_log_linear:
    bins_per_client: 4
    max_iterations: 10000
    maximum_fitted_marginal_absolute_error: 1.0e-08
    probability_floor: 1.0e-12
  exclusion_matched_conditional_hofd:
    relative_singular_cutoff: 1.0e-12
    ridge_penalty: 0.0
  global_factor_residual:
    candidate_ranks: [1, 2, 3]
    cumulative_variance_target: 0.8
    fallback_rank: 3
  multistream_cusum:
    rank_center: 0.5
    drift_subtraction: 0.05
    initial_state: 0.0
  fedavg_autoencoder:
    rounds: 50
    local_epochs_per_round: 1
    client_participation_fraction: 1.0

numerics:
  metric_denominator_floor: 1.0e-12
  deterministic_comparison_tolerance: 1.0e-12
  smoke_repeatability_tolerance: 1.0e-08

statistics:
  confidence_level: 0.95
  nominal_significance_alpha: 0.05
  bootstrap_replicates: 10000
  synthetic_sign_flip_replicates_when_not_exact: 100000

claim_materiality:
  self_explanation:
    exact_exclusion_nuisance_derivative_equivalence_fraction_of_direct: 0.05
    minimum_attenuation_difference: 0.1
  pure_order:
    maximum_proper_subset_standardized_drift: 0.1
    minimum_target_order_standardized_drift: 0.5
  order_three_estimator:
    minimum_mean_context_coverage: 0.8
    maximum_mean_projection_nrmse: 0.1
    maximum_mean_standardized_null_bias: 0.05
  maximum_pooled_numerical_failure_rate: 0.01
  hofd_equivalence:
    atom_nrmse_upper_margin: 0.05
    minimum_cosine_similarity: 0.99
    stopping_time_difference_interval_epochs: [-1.0, 1.0]
  primary_real:
    minimum_strict_odi_rate: 0.2
    minimum_odi_rate_advantage_over_order_at_most_two: 0.1
    minimum_median_operational_lead_epochs: 2.0
  benign_common_mode:
    minimum_false_campaign_suppression: 0.5
    maximum_detection_rate_loss: 0.1
  strong_local:
    minimum_strict_odi_rate: 0.2
  order_three_real:
    minimum_material_odi_contribution: 0.02
  reference_harness:
    p95_latency_maximum_seconds: 30.0

support_grids:
  estimator_samples_per_context: [100, 200, 400, 800, 1600, 3200]
  hofd_equivalence_samples_per_context: [800, 1600, 3200, 6400, 12800]
  estimator_one_factor_sensitivity_samples_per_context: [800, 1600]

robustness:
  benign_count_multiplication_factors: [1.25, 1.5, 2.0]
  scalability_client_counts: [6, 12, 24, 48]

experiments:
  self_explanation_exclusion_validation:
    context_methods:
      - Inclusive Context
      - Leave-One-Out Insufficient Exclusion
      - Partial Coalition Exclusion
      - Exact Coalition Exclusion
      - Oracle Outside Latent Context
    primary_condition:
      client_count: 12
      coalition_order: 3
      nuisance_transform: linear
      comparison:
        - Exact Coalition Exclusion
        - Inclusive Context

  pure_order_separation_validation:
    primary_client_count: 12
    generators:
      - Pure Order One
      - Pure Order Two
      - Pure Continuous Triple
      - XOR Parity Triple
      - Context-Dependent Pure Triple
      - Mixed Order One Plus Two
      - Mixed Order One Plus Three
      - Mixed Order Two Plus Three
      - Mixed Order One Plus Two Plus Three
    methods:
      - Exclusion-Matched Order-One EMHI
      - Exclusion-Matched Order-at-Most-Two EMHI
      - Full FedCampaign-EMHI
      - Exclusion-Matched Conditional HOFD
      - Conditional Pair Dependence
      - Exclusion-Matched Lancaster Triple
      - Connected Information Reference
      - Conditional Log-Linear Reference
      - D-Vine Conditional Reference
    primary_condition:
      generator: Pure Continuous Triple
      method: Full FedCampaign-EMHI
      coalition_order: 3

  exclusion_matched_hofd_equivalence:
    methods:
      - Full FedCampaign-EMHI
      - Exclusion-Matched Conditional HOFD
    context_cell_count: 1
    primary_support_levels: [6400, 12800]

  strong_comparator_composition_challenge:
    candidates:
      - Conditional Pair Dependence
      - Exclusion-Matched Lancaster Triple
      - Connected Information Reference
      - D-Vine Conditional Reference
      - Conditional Log-Linear Reference
    error_tie_tolerance_standardized_units: 0.01
    runtime_tie_tolerance_seconds: 1.0e-06
    artifact_filename: strongest-comparator-composition.json

  estimator_support_and_context_feasibility:
    sensitivity:
      forced_ridge: 0.0
      forced_no_abstention: true

  sequential_evidence_validation:
    signed_theorem:
      null_theta: 0.0
      trajectories_per_seed: 100
      maximum_trajectory_epochs: 10000
      restricted_arl_bootstrap_lower_bound_minimum_epochs: 900

  primary_strict_odi_evaluation:
    methods:
      - Full FedCampaign-EMHI
      - Raw Mean Rank Fusion
      - Raw Max Rank Fusion
      - Exclusion-Matched Order-One EMHI
      - Exclusion-Matched Order-at-Most-Two EMHI
      - Exclusion-Matched Conditional HOFD
      - Global Factor Residual Reference
      - Multistream CUSUM Reference
      - Selected Strong Comparator Composition
      - FedAvg Autoencoder Reference

  exclusion_mechanism_ablation:
    methods:
      - Full FedCampaign-EMHI
      - Inclusive-Context Full Hierarchy
      - Leave-One-Out Insufficient Exclusion
      - Partial Coalition Exclusion

  purification_and_order_ablation:
    methods:
      - Full FedCampaign-EMHI
      - No Proper-Subset Purification
      - Exclusion-Matched Order-One EMHI
      - Exclusion-Matched Order-at-Most-Two EMHI

  context_and_estimator_sensitivity:
    forced_ridge: 0.0
    context_variants:
      - Shuffled Outside Context
      - Local-History-Only Context
      - Forced No-Abstention

  benign_common_mode_robustness:
    methods:
      - Full FedCampaign-EMHI
      - Raw Mean Rank Fusion
      - Inclusive-Context Full Hierarchy
      - No-Outside-Context Full Hierarchy
    native_high_volume_window:
      stride_epochs: 1
      top_event_count_fraction: 0.01

  secondary_controlled_trace_generalization:
    methods:
      - Full FedCampaign-EMHI
      - Raw Mean Rank Fusion
      - Exclusion-Matched Order-One EMHI
      - Exclusion-Matched Order-at-Most-Two EMHI
      - Exclusion-Matched Conditional HOFD
      - Selected Strong Comparator Composition

scalability_timing:
  measured_repetitions_per_seed_client_count: 5
  unmeasured_harness_warmup_epochs: 100
  measured_epochs_per_repetition: 600
  concurrent_experiment_cells: 1
  result_quantile: 0.95

runtime:
  automatic_technical_retries_after_initial_failure: 2
  required_confirmatory_missing_cell_tolerance: 0

artifacts:
  outputs_root: outputs
  results_root: results

reporting:
  precision:
    probabilities_and_rates_decimals: 3
    effect_sizes_decimals: 3
    epochs_and_minutes_decimals: 1
    milliseconds_and_seconds_decimals: 2
    adjusted_p_values_decimals: 4
    p_value_lower_display_threshold: 0.0001
```

## Scientific definitions, derivations, and fixed method rules

The YAML above is authoritative only for values that remain in configuration. Fixed scientific behavior, algorithmic definitions, validation rules, derivations, provenance rules, and execution semantics are authoritative in the methodological sections below and elsewhere in this roadmap. A fixed rule is not user-selectable merely because an implementation library exposes a corresponding option. Numerical values retained in YAML are scientifically locked unless an experiment contract explicitly identifies them as a sensitivity or grid parameter.

### Core scientific configuration

All core numerical values remain authoritative in the Configuration YAML. They are scientifically locked for the primary study; only experiment contracts explicitly labeled as sensitivity or grid studies may vary the corresponding sensitivity keys.

For dropout experiments, the required outside-client count is derived as

$$
\max
\left(
\texttt{context.minimum＿available＿outside＿clients},
\left\lceil
\texttt{context.minimum＿available＿outside＿fraction}
|A^c|
\right\rceil
\right).
$$

### Rank and context configuration

All rank, context-count, support, and K-means numerical values remain authoritative in the Configuration YAML. K-means initialization is fixed to k-means++, the algorithm is fixed to Lloyd's algorithm, and nuisance cross-fitting uses contiguous blocked folds. The context seed is `randomness.context_base_seed`.

Histogram edges are derived from `context.outside_histogram_bin_count`.

### Basis and projection configuration

All basis-size, ridge-candidate, projection-tolerance, support-floor, and cross-validation-count values remain authoritative in the Configuration YAML. Projection cross-validation uses contiguous blocked folds.

The projection Gram condition number is calculated on the unregularized $X^\top X$ matrix after removing exactly constant zero-variance columns.

A fitted coalition/context artifact abstains if:

* required support is unavailable;
* any fitted value is non-finite;
* the condition-number limit is exceeded;
* the fitted artifact provenance does not match the current semantic cell.

### Evidence and sequential configuration

All evidence magnitudes, ARL/PFA targets, calibration confidence, candidate thresholds, and plotting offsets remain authoritative in the Configuration YAML. Quantiles throughout the study use linear interpolation. The calibrated finite-horizon confidence bound is one-sided.

A held-out real PFA claim also requires at least 59 non-overlapping held-out benign horizons.

### Dataset and preprocessing configuration

Dataset identifiers, paths, target/minimum client counts, eligibility counts, hash-bucket count, scaling floor, and the first three benign partition fractions remain authoritative in the Configuration YAML. `heldout_benign` is the chronological remainder and is not independently configurable.

The model input dimension is derived as

$$
\texttt{datasets.preprocessing.event＿type＿hash＿bucket＿count}+2.
$$

With the primary configuration this evaluates to 66 but 66 is not independently configurable.

The four chronological benign partitions are:

```text
detector_fit
nuisance_fit
threshold_and_policy_calibration
heldout_benign
```

The first three partition sizes use floor on their configured fraction of the complete common benign epoch count.

The remainder belongs to `heldout_benign`.

All selected clients use identical temporal boundaries.

### Event canonicalization

#### TON_IoT Network

A retained flow record has canonical event type

```text
NFKC(upper(strip(proto))) + "::" + NFKC(upper(strip(service)))
```

Missing values are represented by the literal tokens:

```text
UNKNOWN_PROTO
UNKNOWN_SERVICE
```

and are not silently discarded if the client (`src_ip`) and timestamp remain valid. The exact resolution of `proto`/`service` against the observed raw schema is a documented expectation only; the observed raw manifest/release is authoritative.

#### Edge-IIoTset

Only records with a resolvable dominant protocol-specific column group (`arp.*`, `http.*`, `tcp.*`, `udp.*`, `icmp.*`, `mqtt.*`, `mbtcp.*`) enter the epoch event-count feature.

The canonical type is

```text
"PROTOCOL::" + NFKC(upper(strip(dominant_protocol_group)))
```

An unrecognized or unresolvable protocol group becomes

```text
PROTOCOL::UNKNOWN_PROTOCOL
```

rather than being dropped. The exact column-group resolution order against the observed raw schema is a documented expectation only; the observed raw manifest/release is authoritative.

#### Hash mapping

For the canonical UTF-8 string:

1. compute SHA-256;
2. interpret the first 8 digest bytes as an unsigned big-endian integer;
3. take modulo `datasets.preprocessing.event_type_hash_bucket_count`.

No process-randomized language hash may be used.

### Timestamp and epoch configuration

All timestamps are normalized to UTC.

* Unix numeric timestamps are interpreted relative to the Unix UTC epoch according to the dataset schema's declared unit.
* Offset-aware textual timestamps are converted to UTC.
* A naive textual timestamp is invalid unless the corresponding dataset adapter has a documented dataset-level timezone rule.
* No timezone is guessed from the machine executing the code.

The epoch index is

$$
\left\lfloor
\frac{\text{Unix timestamp seconds}}
{\texttt{time.real＿data＿epoch＿seconds}}
\right\rfloor.
$$

Epoch boundaries are therefore globally deterministic.

### Local detector configuration

Detector numerical hyperparameters remain authoritative under `detectors`. The following fixed algorithmic rules are not configuration choices.

#### Isolation Forest

* estimators: `detectors.isolation_forest.trees`;
* maximum samples: $\min(\texttt{detectors.isolation＿forest.max＿samples＿cap}, n_{\text{detector fit}})$;
* maximum features: `detectors.isolation_forest.max_features`;
* worker jobs: `detectors.isolation_forest.jobs`; verbosity is fixed to 0;
* bootstrap: disabled;
* contamination: `auto`;
* warm start: disabled;
* random state: deterministic detector substream;
* anomaly score: $-\mathrm{score_samples}(x)$.

#### One-Class SVM

* kernel: RBF;
* $\nu$: `detectors.one_class_svm.nu`;
* gamma: the library `scale` rule, explicitly resolved as $1/(d\mathrm{Var}(X))$;
* coefficient zero, solver tolerance, kernel cache, and maximum iterations: the corresponding `detectors.one_class_svm` values;
* shrinking: enabled;
* verbose: disabled;
* anomaly score: $-\mathrm{decision_function}(x)$.

#### Autoencoder

The fixed architecture for input dimension $d$ is

$$
d\rightarrow32\rightarrow8\rightarrow32\rightarrow d.
$$

The hidden activation is ReLU, the output activation is linear, and the loss is elementwise squared error averaged over features and batch. Optimization uses Adam with learning rate, betas, optimizer epsilon, weight decay, batch size, and epoch count from `detectors.autoencoder`.

Training shuffles each epoch, does not drop the final partial batch, uses no early stopping, no gradient clipping, and no mixed precision. The claim-bearing network weights use float32. Hidden-layer weights use Xavier-uniform initialization with ReLU gain; the output layer uses Xavier-uniform initialization with gain 1; all biases are zero. Checkpoint selection is the final epoch. The anomaly score is per-sample reconstruction MSE.

Batch permutation seeds are deterministic substreams of:

```text
root_seed
client_id
training_epoch
```

No early stopping is permitted.

### Detector-family assignment

Selected client IDs are sorted lexicographically.

For zero-based client index $j$:

```text
j mod 3 = 0 → Isolation Forest
j mod 3 = 1 → One-Class SVM
j mod 3 = 2 → Autoencoder
```

This assignment is fixed before evaluation labels are inspected.

### Local policy configuration

Candidate score quantiles, persistence pairs, PFA targets, and PFA confidence remain authoritative in the Configuration YAML. The local horizon is exactly the global calibrated finite-horizon campaign horizon; it is derived rather than configured separately.

Candidate score thresholds are quantiles of detector scores on `nuisance_fit`, not on the policy-calibration split.

Candidate PFA is evaluated on non-overlapping `threshold_and_policy_calibration` horizons.

For a persistence rule $m$-of-$n$:

* the current epoch is included;
* the last at most $n$ epochs are examined;
* the rule may trigger as soon as at least $m$ observations have occurred;
* an exceedance is `score >= threshold`.

Candidate ordering from least to most stringent is:

1. lower threshold quantile;
2. for the same quantile: 1-of-1;
3. 2-of-3;
4. 3-of-5.

The least stringent candidate whose one-sided PFA UCB passes the required target is selected.

If no candidate passes, the local policy state is:

```text
Operating Point Unavailable
```

and any claim that mathematically requires that local policy becomes Not Tested.

This is a scientific result, not an implementation error.

### Synthetic RNG configuration

Root-seed sequences and base seeds remain authoritative in the Configuration YAML. The number of seeds is derived from each configured sequence.

### Canonical serialization for hashes and deterministic seed derivation

Every `canonical(...)` or `canonical_utf8(...)` operation in this roadmap uses RFC 8785 JSON Canonicalization Scheme semantics over an I-JSON-compatible value. The implementation first constructs a JSON object with the exact field names declared by the relevant semantic record, then canonicalizes it according to RFC 8785 and encodes the canonical JSON as UTF-8 before hashing.

The following rules are mandatory:

* JSON object properties are recursively sorted by RFC 8785 ordering;
* array element order is preserved and is scientifically meaningful;
* strings are serialized exactly as stored after any dataset-specific normalization explicitly required elsewhere in this roadmap; canonical hashing performs no additional Unicode normalization;
* integers that must retain integer identity are represented as JSON integers within the exact IEEE-754 safe integer range; larger integer identities are decimal strings;
* finite floating-point scientific values are represented as IEEE-754 binary64 JSON numbers under RFC 8785 number serialization;
* NaN, positive/negative infinity, duplicate object keys, lone Unicode surrogates, and negative zero are invalid canonical inputs;
* optional absent fields are omitted; an explicit scientific null is encoded as JSON `null`;
* sets are never serialized directly: where a scientific collection is mathematically unordered, the roadmap-defined semantic sort order is applied first and the result is serialized as an array;
* SHA-256 always receives the resulting canonical UTF-8 bytes with no trailing newline or separator.

This canonical representation is used consistently for deterministic RNG substreams, configuration digests, material dependency fingerprints, semantic checksums, and artifact identities. No language-native dictionary, tuple, pickle, YAML, or object-repr serialization may enter a scientific hash.

Component substream seeds are computed from the exact JSON object:

```json
{
  "base_seed": <decimal-string>,
  "component_name": <string>,
  "dataset": <string-or-null>,
  "client_ids": [<canonical client IDs in lexicographic order>],
  "coalition_ids": [<canonical coalition client IDs in lexicographic order>],
  "condition_coordinates": {<scientific coordinate name>: <value>, ...}
}
```

`condition_coordinates` contains every experiment coordinate that can change the stochastic realization, using the exact roadmap/configuration coordinate names and no derived display labels. Its object properties are then ordered by JCS; `client_ids` and `coalition_ids` are explicitly sorted before serialization. When a field is not applicable, `dataset` is JSON `null` and the client/coalition arrays are empty rather than omitted.

The seed is

```text
SHA256(canonical_utf8(the_exact_object_above))
```

The first 64 digest bits, in network byte order (most-significant byte first), are
interpreted as an unsigned integer and reduced modulo $2^{53}$ before being retained
as a reusable component seed.  This keeps every subsequently serialized seed within
the RFC 8785/I-JSON exact-integer domain.  Base seeds are always encoded as their
decimal-string identities before hashing, avoiding a representation change when a
derived seed becomes the base seed of a nested component.

Libraries restricted to 32-bit seeds receive the value modulo $2^{32}$.

No sequential RNG-spawn order may affect a scientific result.

### Generic synthetic sample sizes

Generic synthetic sample counts remain authoritative in `synthetic.sample_sizes`. Synthetic campaign horizon and warm-up are exactly `campaign.evaluation_horizon_epochs` and `campaign.prestart_warmup_epochs`; they are derived rather than duplicated in configuration.

These counts may be replaced only where an experiment contract explicitly declares a different sample count.

### Common-mode generator configuration

For common-mode score generators,

$$
Z_t =
\rho Z_{t-1}
+
\sqrt{1-\rho^2}\eta_t,
\qquad
\eta_t\sim N(0,1),
$$

with $\rho=\texttt{generators.common＿mode.latent＿ar＿coefficient}$. This normalization fixes the stationary latent variance to 1; it is an algorithmic invariant, not a configurable parameter.

Client loadings are equally spaced from `generators.common_mode.client_loading_minimum` through `generators.common_mode.client_loading_maximum` in lexicographic client order.

Thus

$$
S_{i,t} =
\beta_iZ_t+\varepsilon_{i,t},
\qquad
\varepsilon_{i,t}\overset{iid}{\sim}
N
\left(
0,
\texttt{generators.common＿mode.client＿noise＿standard＿deviation}^2
\right).
$$

### Controlled attack-generator configuration

#### Marginal campaign

The attacked coalition is the lexicographically first three clients unless an experiment explicitly tests another order.

During the attack,

$$
S_{i,t} =
\beta_iZ_t
+
\delta
+
\varepsilon_{i,t},
\qquad i\in A,
$$

with $\delta=\texttt{generators.controlled＿campaigns.marginal.score＿shift}$ in raw common-mode score units.

#### Pair-relation campaign

The target pair is the first two clients. Their latent Gaussian-copula correlation is `generators.controlled_campaigns.pair_relation.benign_correlation` under benign data and `generators.controlled_campaigns.pair_relation.campaign_correlation` during the campaign.

Marginals remain standard uniform after the Gaussian-copula transform.

#### Single-client anomaly

Only the first client is shifted by `generators.controlled_campaigns.single_client.score_shift`.

The distributed-support predicate must prevent a global campaign declaration caused solely by that single client.

### Self-explanation generator configuration

Primary coalition membership for order $r$ is the first $r$ lexicographic clients.

Persistent perturbations are exactly `generators.self_explanation.perturbations`. The derivative regression uses exactly `generators.self_explanation.derivative_regression_perturbations`.

For every root seed, one common-mode latent/noise realization is generated and reused across all perturbation values so that the perturbation grid is paired within seed. For perturbation $\epsilon$, every member of the target coalition receives the persistent additive intervention

$$
S^{(\epsilon)}_{i,t}=S^{(0)}_{i,t}+\epsilon,
\qquad i\in A,
$$

while every client outside $A$, the latent common-mode process, availability, and noise realization remain unchanged. The intervention begins before the lag-settling segment. Exactly `synthetic.sample_sizes.self_explanation_lag_settling_epochs_discarded` post-intervention epochs are discarded; the following `synthetic.sample_sizes.self_explanation_epochs_per_perturbation` epochs are used for derivative estimation. No perturbation condition is allowed to regenerate a different latent/noise trajectory.

For the analytic scalar fixture,

$$
Y_{A,t} =
\frac1{|A|}
\sum_{i\in A}
S_{i,t}.
$$

A context-member set $B$ produces nuisance statistic

$$
m_{B,t} =
\frac1{|B|}
\sum_{j\in B}
S_{j,t-1}.
$$

The nuisance transformations are fixed as

$$
g_{\text{linear}}(m)=m,
$$

$$
g_{\tanh}(m)=\tanh(2m),
$$

$$
g_{\text{softplus}}(m) =
\log(1+e^m)-\log2.
$$

Define the nuisance statistic after transformation as

$$
\eta_{A,t}=g(m_{B,t}).
$$

The scalar innovation fixture is

$$
R_{A,t} =
Y_{A,t}-\eta_{A,t}.
$$

Context-member sets are defined in Section 8 and are identical between the fixture and the corresponding context ablation.

For each seed and context method, ordinary least squares with an intercept is fit over the configured derivative-regression perturbations. The response at each perturbation is the mean of the corresponding post-settling evaluation epochs. The fitted slope defines the derivative; no finite-difference endpoint rule is substituted.

The direct derivative is

$$
D_{\text{direct}} =
\frac{dE[Y_A]}{d\epsilon}.
$$

Under the additive intervention above, the analytic value is $D_{\text{direct}}=1$. The nuisance and residual derivatives are

$$
D_{\eta} =
\frac{dE[\eta_A]}{d\epsilon},
$$

$$
D_R =
\frac{dE[R_A]}{d\epsilon}.
$$

The primary derivative equivalence margin is defined relative to $|D_{\text{direct}}|$.

### Pure-order population completion

Unless a generator-specific section states otherwise, synthetic pure-order experiments use the configured experiment client count $K$, the target coalition is the lexicographically first $r$ clients for order $r$, and every non-target client emits an independent $U(0,1)$ rank. Non-target clients are mutually independent, independent of the target coalition, and independent across samples/epochs. XOR and mixed-order conditions use the first three clients as their target set and complete the remaining $K-3$ clients by the same independent-uniform rule.

Independent-evaluation pure-order samples are temporally iid. When a pure-order condition is used in a finite-horizon sequential evaluation, null warm-up/calibration epochs are iid draws from the corresponding zero-effect population and campaign epochs are iid draws from the declared nonzero-effect population; the sequential state is reset exactly as specified by the applicable horizon/campaign contract.

Development pure-order cells use `randomness.synthetic_development_roots`; confirmatory pure-order cells use `randomness.synthetic_confirmatory_roots`.

### Pure polynomial generators

Let

$$
m_r=(\sqrt3)^r.
$$

For a pure order-$r$ coalition $A$,

$$
p_\theta(u_A) =
1+
\theta
\prod_{i\in A}\phi_1(u_i).
$$

The density is valid only when

$$
|\theta|
\le
\frac1{m_r}.
$$

The authoritative legal effect grids are `generators.pure_polynomial.theta.order_one`, `generators.pure_polynomial.theta.order_two`, and `generators.pure_polynomial.theta.order_three`.

The previously tempting values $0.20$ and $0.40$ are not legal for the normalized third-order density because the density would become negative.

The primary reference effect for inferential pure-order testing is `generators.pure_polynomial.primary_reference_theta` for every order where that value is valid.

Exact samples are generated by rejection sampling from independent uniform proposals with envelope

$$
M=1+|\theta|m_r.
$$

A negative or non-finite evaluated density is an invariant violation.

### XOR generator

For each sample:

$$
X_1,X_2\overset{iid}{\sim}\mathrm{Bernoulli}(0.5).
$$

Let interaction strength $\gamma$ range over `generators.xor.strengths` and set

$$
P
\left(
X_3=X_1\oplus X_2
\right) =
0.5+0.5\gamma.
$$

Continuous ranks are produced using independent

$$
V_i\sim U(0,1)
$$

and

$$
U_i =
\frac{X_i+V_i}{2}.
$$

Every univariate and pairwise marginal remains uniform/independent.

The primary XOR reference strength is `generators.xor.primary_reference_strength`.

### Mixed-order generator

For clients $1,2,3$, define the canonical terms

$$
q_1=\phi_1(u_1),
$$

$$
q_2=\phi_1(u_1)\phi_1(u_2),
$$

$$
q_3=\phi_1(u_1)\phi_1(u_2)\phi_1(u_3).
$$

The enabled mixed-order term sets are `generators.mixed_order.enabled_term_sets`. Every enabled term receives coefficient `generators.mixed_order.term_coefficient`, so that the complete enabled density remains strictly nonnegative under the basis bounds.

Samples are generated by exact rejection sampling using the deterministic sum-of-absolute-bounds envelope.

### Context-dependent pure triple

Let $C_t\in\lbrace-1,+1\rbrace$ be a stationary two-state Markov chain with same-state probability `generators.context_dependent_triple.markov_same_probability`. The change probability is its complement, $1-\texttt{generators.context＿dependent＿triple.markov＿same＿probability}$. Initial-state probabilities are `generators.context_dependent_triple.initial_state_probabilities`.

For the target triple,

$$
p_\theta
(
u_A\mid C_{t-1}=c
) =
1+
\theta c
\prod_{i\in A}\phi_1(u_i),
$$

with primary effect `generators.context_dependent_triple.primary_theta`.

Every outside client $j\notin A$ emits an informative rank from the interval selected by `generators.context_dependent_triple.outside_rank_intervals` for the current latent state. If the selected interval is $[a_c,b_c]$, then

$$
U_{j,t}\mid C_t=c\sim U(a_c,b_c).
$$

Conditional on $C_t$, outside clients are mutually independent and independent of the target-coalition rejection-sampling randomness. Interval endpoints are interpreted literally; no midpoint or additional noise model is permitted.

The oracle-context comparator uses the true $C_{t-1}$.

### Outside-contamination generator

The target client count is `generators.outside_contamination.client_count`. The target coalition is the first three lexicographic clients and the target triple effect is `generators.outside_contamination.target_triple_theta`.

Outside correlated-campaign fractions are exactly `generators.outside_contamination.correlated_campaign_fractions`.

For fraction $f$, the number of contaminated outside clients is derived by round-half-up of

$$
f|A^c|.
$$

The lexicographically first required outside clients are contaminated.

During the campaign their outside ranks are transformed as

$$
U'=
\min
\left(
U+\texttt{generators.outside＿contamination.outside＿rank＿shift},
1-\texttt{context.rank＿clip＿epsilon}
\right).
$$

No other generator parameter changes.

### Client-dropout generator

Unavailable-client fractions are exactly `generators.client_dropout.unavailable_fractions`.

For each client and epoch, availability is independently drawn with probability

$$
1-f.
$$

The availability mask for epoch $t$ is generated before current evidence and is therefore predictable.

A coalition is active only when:

1. every member of the tested coalition is available;
2. the configured outside-availability requirement is met.

### Comparator calibration configuration

Any comparator producing a scalar or vector interaction score must declare its score orientation.

For a sign-agnostic comparator:

1. score centering/scaling is estimated from nuisance-fit data;
2. absolute or norm nonconformity is taken as specified by that comparator;
3. the reference quantile `comparators.common_calibration.nuisance_reference_quantile` is estimated on nuisance-fit data and used to map the score into the same bounded operational transform;
4. calibrated finite-horizon threshold selection is performed independently on `threshold_and_policy_calibration` horizons.

No comparator receives attack-informed score normalization.

### Conditional pair-dependence reference

For pair $i,j$,

$$
P_{ij,t} =
(2U^{(-A)}_{i,t}-1)
(2U^{(-A)}_{j,t}-1).
$$

Its benign mean and sample standard deviation are estimated from cross-fitted nuisance-fit data.

The sign-agnostic nonconformity is the absolute standardized value.

Maximum order: 2.

### Lancaster-moment triple reference

For triple $i,j,k$,

$$
L_{ijk,t} =
(2U_i-1)
(2U_j-1)
(2U_k-1).
$$

The coordinates are exact outside-conditioned ranks.

The score is centered/scaled on benign nuisance-fit observations and its absolute standardized magnitude is used as nonconformity.

This comparator is explicitly a finite-dimensional Lancaster-style third-order moment reference, not a claim to implement every general Lancaster/Streitberg interaction measure.

### Connected-information reference

Conditional ranks are discretized into `comparators.connected_information.bins_per_client` equal-width bins over $[0,1]$.

Contingency probabilities use the Jeffreys pseudocount `comparators.connected_information.jeffreys_pseudocount_per_cell`.

For triples, the lower-order maximum-entropy distribution matching all pair marginals is fitted by iterative proportional fitting with maximum iterations, marginal-error tolerance, and probability floor from `comparators.connected_information`. The initial table is fixed to uniform.

The per-cell interaction score is

$$
\log
\frac{
p_{\text{full,benign}}(c)
}{
p_{\text{pair-maxent,benign}}(c)
}.
$$

The absolute standardized score is used operationally.

Connected information is based on comparing a distribution with the maximum-entropy distribution constrained by lower-order marginals.

### Conditional log-linear reference

Ranks use `comparators.conditional_log_linear.bins_per_client` equal-width bins over $[0,1]$.

Fit a hierarchical multinomial/Poisson log-linear model containing:

* intercept;
* every singleton term;
* every pair term;
* no triple term.

Maximum iterations, fitted-marginal convergence tolerance, and cell probability floor are the corresponding `comparators.conditional_log_linear` values.

The per-observation raw anomaly score is

$$
-\log p_{\text{lower-order}}(c).
$$

It receives the common nuisance-fit nonconformity calibration.

### D-vine conditional reference

For each triple with lexicographically ordered members $i\lt j\lt k$, use the fixed D-vine

```text
i — j — k
```

All pair copulas are Gaussian.

Benign pair parameters are estimated by Kendall's $\tau$, converted through

$$
\rho =
\sin
\left(
\frac{\pi}{2}\tau
\right).
$$

The second-tree conditional pseudo-observations are computed with the Gaussian copula h-functions.

The raw highest-tree score is the absolute log-density contribution of the $i,k\mid j$ Gaussian pair copula.

No copula-family search is performed.

The pair-copula construction follows the established pair-copula decomposition framework.

### Exclusion-matched conditional HOFD reference

The HOFD comparator uses:

* exactly the same outside context;
* exactly the same basis;
* exactly the same nuisance-fit split;
* exactly the same proper-subset column space;
* no attack data.

For each highest-order basis coordinate, perform empirical hierarchical orthogonalization against the complete proper-subset design using QR/SVD projection with relative singular cutoff `comparators.exclusion_matched_conditional_hofd.relative_singular_cutoff` and ridge penalty `comparators.exclusion_matched_conditional_hofd.ridge_penalty`.

The highest-order residual is the HOFD atom estimate.

The comparator is intended to target the same hierarchical lower-order subspace as EMHI at large benign support; the HOFD literature establishes hierarchical orthogonal decompositions for dependent inputs under suitable conditions.

### Global factor residual reference

Input is the client marginal-rank panel on nuisance-fit epochs.

Processing:

* subtract per-client nuisance-fit mean;
* perform no variance scaling;
* compute a full deterministic SVD;
* choose the smallest rank in `comparators.global_factor_residual.candidate_ranks` explaining at least `comparators.global_factor_residual.cumulative_variance_target` cumulative variance;
* if no candidate reaches the target, use `comparators.global_factor_residual.fallback_rank`.

The raw score is L2 reconstruction residual.

### Multistream CUSUM reference

For client $i$,

$$
Y_{i,t} =
U^M_{i,t}-\texttt{comparators.multistream＿cusum.rank＿center},
$$

$$
C_{i,0} =
\texttt{comparators.multistream＿cusum.initial＿state},
$$

$$
C_{i,t} =
\max
\left(
0,
C_{i,t-1}
+
Y_{i,t} -
\texttt{comparators.multistream＿cusum.drift＿subtraction}
\right).
$$

The global raw score is

$$
\max_i C_{i,t}.
$$

The final stopping threshold is independently calibrated by the calibrated finite-horizon route.

### Federated autoencoder reference

Architecture, initialization, local optimizer, and local training hyperparameters are identical to the local autoencoder. The number of FedAvg rounds, local epochs per round, and client participation fraction are `comparators.fedavg_autoencoder.rounds`, `comparators.fedavg_autoencoder.local_epochs_per_round`, and `comparators.fedavg_autoencoder.client_participation_fraction`.

Aggregation is the sample-count-weighted arithmetic mean. Server accumulation uses float64 and stored model parameters use float32. Local optimizer state is reset at the start of every round. Training uses detector-fit benign data only.

After federated fitting, client reconstruction scores are converted to marginal ranks and fused by raw mean.

This comparator is explicitly unmatched because it receives collaborative training information unavailable to the primary local detectors.

### PCA and linear-algebra numerical configuration

General matrix arithmetic for EMHI and statistics uses float64. Neural-network training and inference use float32. Generic metric-denominator, deterministic-comparison, and smoke-repeatability tolerances remain authoritative under `numerics`.

Concept-specific floors remain distinct and must not be replaced by a single global epsilon.

### Statistical configuration

Confidence level, nominal significance alpha, paired-bootstrap resample count, and non-exact synthetic sign-flip replicate count remain authoritative under `statistics`. Statistical-analysis RNG uses `randomness.statistical_analysis_base_seed`.

The paired bootstrap method is fixed to BCa. Real ten-seed sign-flip inference uses exact enumeration of all $2^{10}=1024$ assignments; the value is derived from the ten configured real confirmatory seeds and is not separately configured. Multiplicity correction is Holm. PFA intervals use exact Clopper-Pearson; ordinary binary descriptive intervals use two-sided exact Clopper-Pearson. Quantile interpolation is fixed to linear.

#### Primary directional Holm family

Exactly these five directional hypotheses form the primary p-value family:

```text
Self-Explanation Material Attenuation
Pure-Order Target Drift
Primary ODI Advantage over Order-at-Most-Two EMHI
Common-Mode False-Campaign Reduction
Strong-Local ODI above Minimum
```

Equivalence criteria, PFA confidence bounds, estimator feasibility criteria, and latency criteria are not converted into null-hypothesis significance tests merely to enlarge this family.

#### Secondary ablation Holm family

Exactly these contrasts form the secondary family:

```text
Full FedCampaign-EMHI vs Inclusive Context
Full FedCampaign-EMHI vs Leave-One-Out Context
Full FedCampaign-EMHI vs Partial Exclusion
Full FedCampaign-EMHI vs No Purification
Full FedCampaign-EMHI vs Order One
Full FedCampaign-EMHI vs Order at Most Two
```

### Claim and materiality criteria

Every numerical materiality, equivalence, feasibility, PFA, ODI, robustness, and latency criterion remains authoritative under `claim_materiality` and the other cited Configuration YAML keys. The criteria are scientifically locked and may not be tuned from observed outcomes.

### Synthetic estimator and equivalence grids

The primary estimator support sweep is `support_grids.estimator_samples_per_context`. The HOFD equivalence support sweep is `support_grids.hofd_equivalence_samples_per_context`. Estimator one-factor sensitivity is evaluated only at `support_grids.estimator_one_factor_sensitivity_samples_per_context` benign samples per context.

### Robustness grids

Benign count-stress factors are `robustness.benign_count_multiplication_factors`. Outside-contamination fractions are `generators.outside_contamination.correlated_campaign_fractions`. Client-dropout fractions are `generators.client_dropout.unavailable_fractions`. Scalability client counts are `robustness.scalability_client_counts`.

### Scalability timing configuration

Development timing uses `randomness.real_development_roots`. Repetition count, unmeasured warm-up epochs, measured epochs per repetition, concurrent experiment cells, and result quantile remain authoritative under `scalability_timing`.

Network transport is excluded and the reference harness is in-process. Disk I/O is excluded from the timed interval. Timing uses a monotonic high-resolution clock. GPU sections, when present, are synchronized immediately before and after the timed region. The reported timing quantile uses the fixed linear quantile interpolation rule.

The latency criterion applies to the complete end-to-end reference harness defined in Section 11.34, not to real network deployment.

### Runtime and retry configuration

The number of automatic technical retries after the initial failure is `runtime.automatic_technical_retries_after_initial_failure`. Claim-bearing synthesis permits at most `runtime.required_confirmatory_missing_cell_tolerance` missing required confirmatory cells.

Every technical retry uses identical scientific inputs and seeds. A valid completed cell is skipped by default. A stale, incomplete, or failed cell is rebuilt at the same semantic identity. Invalidation is limited to the affected artifact and its downstream descendants. Unrelated code or configuration changes do not invalidate unaffected artifacts. Recomputing a parent without changing its material identity preserves compatible descendants. `--overwrite` forces target recomputation without forcing unrelated prerequisites.

A retry may resume from any complete compatible checkpoint or upstream artifact; it must not restart an expensive ancestor merely because a downstream step failed.

### Reporting configuration

Reporting decimal precision remains authoritative under `reporting.precision`. Confidence bounds use the same displayed precision as their estimate. The primary ODI table row order is exactly the method order in `experiments.primary_strict_odi_evaluation.methods` and is derived rather than separately configured.

No significance stars are used. Machine-readable results always retain full precision. These are fixed reporting rules, not configuration choices.

---

# 6. Dataset protocol

## 6.1 Two levels of dataset authority

Every dataset has two classes of facts.

### Documented expected structure

This is derived from official release documentation or the original publication and is used for inventory checking.

### Observed raw structure

The actual raw files mounted in the repository are authoritative for execution.

The implementation must never manufacture missing hosts, records, files, labels, or time coverage merely to match a literature number.

Every discrepancy between documented and observed structure is written to the dataset inventory.

A discrepancy becomes blocking only if it violates an explicit eligibility rule or makes a required semantic field ambiguous.

### Raw-dataset adaptation rule

All dataset-specific counts, file inventories, schemas, field names, event enums, timestamp units, host identities, labels, and time coverage are subject to validation against the actual mounted raw release during implementation. Official documentation defines expected semantics; observed raw bytes define what is executable.

The adapter must follow these rules:

1. discover and record the actual raw files before applying any expected count or filename assumption;
2. read the release-provided schema or machine-readable record schema when present before selecting fields;
3. map a documented semantic field to an observed field only when the mapping is unique and justified by the official schema/README or by an unambiguous schema-level semantic identity;
4. record every such mapping in the preprocessing manifest; field aliases are adapter facts, not new scientific configuration;
5. never pad, synthesize, truncate, or resample raw records merely to reproduce a published record/client/file count;
6. never invent a timestamp unit, timezone, host mapping, or malicious label; if more than one interpretation remains compatible with authoritative metadata, preprocessing is Invalid;
7. unknown but structurally valid event types remain governed by the canonical unknown-event rules in this roadmap rather than being dropped;
8. if documented files or clients are absent, execution proceeds only with the observed material that still satisfies the predeclared eligibility, chronology, ground-truth, and horizon rules; otherwise the affected experiment/claim is Not Tested;
9. if the observed release contains additional files, hosts, or valid event types, they are inventoried and processed under the same predeclared rules rather than excluded to force literature counts;
10. no implementation-time adaptation may alter target client count, eligibility thresholds, chronological fractions, horizon length, claim thresholds, or experiment grids.

For TON_IoT Network, the authoritative release identity is the IEEE DataPort / UNSW Research "The TON_IoT Datasets" project release (Network flow variant), mirrored on Kaggle; the release documentation and the UNSW Canberra Cyber publications describing the ToN_IoT dataset family define the documented expected semantics. For Edge-IIoTset, the authoritative release identity is IEEE DataPort DOI `10.21227/mbc1-1h68`, and the release documentation together with Ferrag et al. (2022) define the documented expected semantics. These documented properties are inventory expectations only and never override contradictory observed raw bytes silently.

---

## 6.2 TON_IoT Network

The primary cyber trace is the Network flow variant of the TON_IoT Datasets, created by UNSW Canberra Cyber (Cyber Range and IoT Labs, School of Engineering and IT, UNSW Canberra @ ADFA). It is one variant of the broader ToN_IoT dataset family, which also includes Linux, Windows, and IoT/IIoT host-telemetry variants; this project uses only the Network flow variant. The dataset is distributed as CSV via the IEEE DataPort / UNSW Research "The TON_IoT Datasets" project release and is mirrored on Kaggle.

Flow records are generated with the Bro/Zeek IDS and follow a Zeek `conn.log`-style schema of approximately 44 features: `ts` (flow start timestamp, epoch seconds), `src_ip`, `src_port`, `dst_ip`, `dst_port`, `proto`, `service`, `duration`, `src_bytes`, `dst_bytes`, `conn_state`, `missed_bytes`, `src_pkts`, `src_ip_bytes`, `dst_pkts`, `dst_ip_bytes`, plus protocol-specific extension fields (`dns_*`, `ssl_*`, `http_*`, `weird_*`) contributed by other joined Zeek logs.

Two label columns are documented: a binary `label` column (0 = normal, 1 = attack) and a multi-class `type` column with values `normal`, `backdoor`, `dos`, `ddos`, `injection`, `mitm`, `password`, `ransomware`, `scanning`, `xss`.

These are documented expectations only; the observed raw manifest/release is authoritative for the exact file inventory, feature set, and record counts.

### Raw identity

The preprocessing identity records:

```text
release persistent identifier or page reference
dataset/version label
every acquired file path
every acquired file SHA-256
every acquired file byte count
ground-truth source SHA-256
adapter material code fingerprint
adapter producer code commit for traceability
```

Checksum values published by the distributing repository may be recorded as external cross-checks, but SHA-256 computed over the actual local raw files is the execution identity.

### Client definition

A client is the canonical device IP address (`src_ip`) in the Network flow records. The capture is IoT/IIoT-device-centric flow data from a single network range, so there is no cross-performer namespace concern; a composite-identity client definition is not required for this dataset.

### Primary client selection

Using benign material only:

1. aggregate retained flow records by canonical device IP (`src_ip`);
2. compute benign event-record count;
3. compute benign nonempty-epoch count;
4. exclude a device if either configured minimum is violated;
5. exclude a device if its identity mapping is ambiguous;
6. sort eligible devices by descending benign event count;
7. break ties by canonical device IP;
8. select the first `datasets.primary.target_client_count`;
9. fix the list before any campaign outcome or method result is inspected.

If fewer than the target count satisfy these predeclared rules, the primary real claim is Not Tested.

No smaller opportunistic primary federation is substituted.

### Benign/evaluation separation

Benign records are identified per-record from the explicit `label`/`type` columns (`label = 0`, `type = normal`); all other records belong to the evaluation/scored material. This is a per-record determination rather than a phase-based archive split, and requires no chronological collection-phase inference.

If the adapter cannot determine this partition unambiguously from the observed release structure, preprocessing is Invalid.

### Ground-truth semantics

The event/epoch ground-truth adapter may use only:

* the explicit binary `label` column for malicious/benign determination;
* the explicit multi-class `type` column for attack-subclass identity.

It may not propagate labels by graph proximity, process ancestry, hostname similarity, IP proximity, or other heuristic expansion.

Ground truth is per-record: a flow record's `ts` places it in exactly one epoch under the epoch-index rule in this section, and that epoch inherits the record's label. This is a simpler mechanism than an interval-annotation scheme, since there is no separate annotation file whose intervals must be intersected against the trace; half-open interval semantics do not apply to ground-truth attachment for this dataset.

A record where `label` and `type` disagree (for example `label = 0` with a non-`normal` `type`) is an ambiguous ground-truth mapping. It is retained in the discrepancy manifest but is not silently treated as malicious.

---

## 6.3 Edge-IIoTset

The secondary trace is Edge-IIoTset (Ferrag et al., "Edge-IIoTset: A New Comprehensive Realistic Cyber Security Dataset of IoT and IIoT Applications for Centralized and Federated Learning", IEEE Access, 2022), distributed via IEEE DataPort under DOI `10.21227/mbc1-1h68`.

The dataset is built from a real 7-layer IIoT/IoT testbed comprising more than 10 distinct physical IoT/IIoT devices (for example temperature/humidity sensor, ultrasonic sensor, water-level detection sensor, pH sensor, soil moisture sensor, heart-rate sensor, flame sensor, and others). Traffic is captured as packet-level pcap via Wireshark across the testbed nodes and converted to CSV. The protocol mix spans IT protocols (TCP/IP, UDP, ICMP, HTTP, ARP) and OT/IIoT protocols (MQTT, Modbus/TCP, CoAP, DNP3, AMQP).

From 1,176 originally extracted raw features, the released/commonly used CSV exposes 61 selected features plus two label columns: `Attack_label` (binary: 0 normal / 1 attack) and `Attack_type` (multi-class, 14 attack types across 5 categories: DDoS, information gathering, MITM, injection, malware; for example `DDoS_UDP`, `DDoS_ICMP`, `DDoS_TCP`, `DDoS_HTTP`, `SQL_injection`, `Uploading`, `Backdoor`, `Port_Scanning`, `Vulnerability_scanner`, `Password`, `XSS`, `Ransomware`, `Fingerprinting`, `MITM`).

Column names include the host/IP identity fields `ip.src_host` and `ip.dst_host` and the timestamp field `frame.time`, plus protocol-specific columns (`arp.*`, `http.*`, `tcp.*`, `udp.*`, `icmp.*`, `mqtt.*`, `mbtcp.*` for Modbus). These are the dataset's own literal column names and must not be normalized to Zeek/Bro-style naming.

These are documented expectations only; the observed raw manifest/release is authoritative for the exact file inventory, feature set, and record counts.

### Raw identity

The preprocessing identity records:

```text
release persistent identifier (DOI 10.21227/mbc1-1h68)
dataset/version label
every acquired file path
every acquired file SHA-256
every acquired file byte count
ground-truth source SHA-256
adapter material code fingerprint
adapter producer code commit for traceability
```

Checksum values published by the distributing repository may be recorded as external cross-checks, but SHA-256 computed over the actual local raw files is the execution identity.

### Secondary client definition

A client is physical IoT/IIoT device identity, distinguishable by the device's stable source-host field `ip.src_host` within the testbed. Edge-IIoTset comes from a fixed roster of physical devices, so device identity is a natural client definition with no cross-performer namespace collision concern; a composite-identity client definition is not required for this dataset.

### Client selection

Apply the same benign-only eligibility criteria as the primary trace to `ip.src_host` identities.

Sort by:

1. descending benign event count;
2. `ip.src_host`.

Select the configured target count when available.

If fewer than the target count but at least `datasets.secondary.minimum_eligible_client_count` remain, use all eligible clients.

If fewer than the minimum remain:

```text
Secondary Controlled-Trace Generalization = Not Tested
```

No replacement dataset may be selected after primary results are known.

### Benign/evaluation separation

Benign records are identified per-record from the explicit `Attack_label`/`Attack_type` columns (`Attack_label = 0`, `Attack_type = Normal`); all other records belong to the evaluation/scored material. This is a per-record determination rather than a phase-based archive split, and requires no chronological collection-phase inference.

If the adapter cannot determine this partition unambiguously from the observed release structure, preprocessing is Invalid.

### Ground truth

The event/epoch ground-truth adapter may use only:

* the explicit binary `Attack_label` column for malicious/benign determination;
* the explicit multi-class `Attack_type` column for attack-subclass identity.

It may not propagate labels by graph proximity, process ancestry, hostname similarity, IP proximity, or other heuristic expansion.

Ground truth is per-record: a flow record's `frame.time` places it in exactly one epoch under the epoch-index rule in this section, and that epoch inherits the record's label. This is a simpler mechanism than an interval-annotation scheme, since there is no separate annotation file whose intervals must be intersected against the trace; half-open interval semantics do not apply to ground-truth attachment for this dataset.

A record where `Attack_label` and `Attack_type` disagree (for example `Attack_label = 0` with a non-`Normal` `Attack_type`) is an ambiguous ground-truth mapping. It is retained in the discrepancy manifest but is not silently treated as malicious.

---

# 7. Real-data preprocessing

## 7.1 Duplicate handling

When an authoritative unique record identifier exists:

* identical identifiers represent duplicates;
* retain the chronologically first occurrence;
* if duplicate identifiers contain non-identical payloads, preprocessing is Invalid unless the release itself defines a deterministic resolution.

When no usable unique identifier exists:

* canonicalize the complete retained record representation;
* exact duplicates require identical dataset, client, timestamp, event type, and canonical payload;
* retain the first chronological instance.

Duplicate counts are recorded.

## 7.2 Invalid records

Exclude records with:

* unparseable timestamp;
* unusable host identity;
* structurally invalid event semantics that cannot produce a canonical event type.

Every excluded record receives a deterministic reason code.

Unknown but structurally valid event types are retained and hashed.

## 7.3 Epoch features

For each client/epoch:

1. count events in every configured hash bucket;
2. apply `log1p` to each count;
3. append total raw event count;
4. append Shannon entropy of the raw bucket-count distribution.

For total count $N\gt 0$,

$$
p_b=\frac{n_b}{N},
$$

$$
H=-\sum_{b:n_b\gt 0}p_b\log p_b.
$$

For $N=0$,

$$
H=0.
$$

An empty epoch therefore contains:

```text
hash-bucket log1p features = 0
total count = 0
entropy = 0
```

Empty epochs are never dropped.

## 7.4 Non-finite handling

Any non-finite generated feature is a preprocessing failure.

No NaN/Inf replacement is permitted.

No forward fill, backward fill, temporal interpolation, mean imputation, or attack-informed repair is permitted.

## 7.5 Robust local scaling

For every client/feature, using only `detector_fit`:

$$
x' =
\frac{
x-\mathrm{median}(x)
}{
\max
(
Q_{0.75}(x)-Q_{0.25}(x),
\texttt{datasets.preprocessing.robust＿scaling＿iqr＿floor}
)
}.
$$

Quantiles use the authoritative linear interpolation method.

The same fixed scaler is applied to every later partition.

## 7.6 Chronological benign partitions

After the common selected-client benign epoch interval is constructed, create the four partitions in the fixed order defined in the preprocessing specification, using the configured first-three partition fractions and assigning the chronological remainder to `heldout_benign`.

There is no shuffled benign split.

There is no random train/test split.

### Eligibility checks

Before real confirmatory execution:

* `threshold_and_policy_calibration` must provide at least the derived 59 non-overlapping complete horizons;
* `heldout_benign` must provide at least 59 non-overlapping complete horizons;
* every selected client must satisfy detector-fit sample requirements;
* real order-3 use is allowed to abstain where its coalition/context support is inadequate, but its claim depends on the configured coverage criterion.

If the actual observed release cannot satisfy these rules, the affected claim is Not Tested; the implementation may not silently shorten the horizon, lower the confidence level, overlap horizons for Clopper-Pearson inference, or merge benign partitions.

## 7.7 Benign horizon construction

Starting at the first epoch of a calibration or held-out split:

1. create consecutive non-overlapping blocks of exactly the configured horizon length;
2. discard a trailing incomplete block;
3. reset every sequential stopping state at the first epoch of each block;
4. retain model/context artifacts fixed from prior partitions.

Overlapping windows are forbidden for primary PFA inference.

---

# 8. Context variants and ablations

## 8.1 Exact exclusion

For coalition $A$:

```text
context members = A^c
time = t - context.outside_lag_epochs
```

This is the primary method.

## 8.2 Inclusive context

For coalition $A$:

```text
context members = all selected clients
time = t - context.outside_lag_epochs
```

This intentionally allows historical coalition information into the nuisance representation.

## 8.3 Leave-one-out insufficient exclusion

Let $a_1$ be the lexicographically first member of $A$.

```text
context members = all selected clients except a_1
time = t - lag
```

Other coalition members therefore remain in the nuisance representation.

## 8.4 Partial coalition exclusion

For a triple $a_1\lt a_2\lt a_3$:

```text
context members = all clients except a_1 and a_2
```

so $a_3$ remains included.

For a pair, partial exclusion equals leave-one-out insufficient exclusion.

## 8.5 Oracle outside latent context

Synthetic mechanism experiments only.

For the common-mode generator the true lagged outside latent state is assigned to four fixed normal-quartile cells.

The quartile boundaries are the $0.25$, $0.50$, and $0.75$ standard-normal quantiles.

No K-means is used.

## 8.6 No outside context

Use one global context cell.

Conditional ranks reduce to marginal-rank recalibration without any outside-state partition.

Proper-subset purification remains enabled.

## 8.7 Shuffled outside context

Within each split independently, lagged outside-context rows are permuted using a deterministic substream.

The permutation is fixed before outcomes are calculated.

Ranks, coalition scores, and attack labels are not shuffled.

## 8.8 Local-history-only context

For coalition $A$, the context histogram uses only lagged ranks of coalition members.

This deliberately violates exact exclusion and is a sensitivity diagnostic.

## 8.9 Forced no-abstention diagnostic

If a context cell lacks the required support, use the complete coalition-specific nuisance-fit reference pooled over all context cells.

The diagnostic therefore eliminates support-driven abstention without changing other method components.

It is never the primary configuration.

---

# 9. Local detector and local policy contract

## 9.1 Fitting

Local detectors are trained exclusively on `detector_fit`.

They never see:

* threshold/policy calibration labels;
* held-out benign data during fitting;
* attack-period observations;
* campaign identities;
* FedCampaign evidence.

## 9.2 Score orientation

Every detector is normalized conceptually so that:

```text
larger score = more suspicious
```

The exact detector score definitions are fixed in the Local detector configuration subsection under Scientific definitions, derivations, and fixed method rules.

## 9.3 Local policy threshold source

Candidate local score thresholds are computed from `nuisance_fit` detector scores.

Candidate policy PFA is evaluated only on the independent threshold/policy-calibration split.

## 9.4 Held-out local validation

The selected primary and strong local policies are also evaluated on held-out benign horizons.

Held-out local PFA is reported but never used to alter the selected policy.

## 9.5 Policy immutability

After calibration, detector, scaler, and local-policy artifacts are immutable for that semantic cell.

No local policy may inspect:

* global method identity;
* coalition evidence;
* global stopping state;
* attack label;
* campaign result.

---

# 10. Baseline and comparator contracts

All matched real-data comparisons share:

* dataset bytes;
* selected clients;
* preprocessing;
* local detector score streams where applicable;
* campaign registry;
* nuisance-fit/calibration/held-out partitions;
* calibrated finite-horizon horizon;
* PFA target;
* threshold-selection rule;
* campaign replay semantics;
* seeds;
* latency accounting.

Methods differ only in their declared evidence representation.

## 10.1 Fixed Local Policies

No global fusion.

Used only as the operational local reference.

## 10.2 Raw Mean Rank Fusion

$$
R_t=\frac1K\sum_iU^M_{i,t}.
$$

High score is anomalous.

The scalar receives the common nuisance-fit calibration and calibrated finite-horizon backend.

## 10.3 Raw Max Rank Fusion

$$
R_t=\max_iU^M_{i,t}.
$$

High score is anomalous.

## 10.4 Exclusion-Matched Order-One EMHI

Exact outside context.

Enabled order set:

```text
{1}
```

## 10.5 Exclusion-Matched Order-at-Most-Two EMHI

Exact outside context.

Enabled order set:

```text
{1,2}
```

Equal order weights are derived as $1/2,1/2$.

This is the primary lower-order causal predecessor.

## 10.6 Full FedCampaign-EMHI

Exact outside context.

Enabled order set:

```text
{1,2,3}
```

Proper-subset purification enabled.

Primary basis/context/ridge configuration.

## 10.7 Inclusive-Context Full Hierarchy

Same as Full FedCampaign-EMHI except Section 8.2 context.

## 10.8 Leave-One-Out Insufficient Exclusion

Same as Full FedCampaign-EMHI except Section 8.3 context.

## 10.9 Partial Coalition Exclusion

Same as Full FedCampaign-EMHI except Section 8.4 context.

## 10.10 No Proper-Subset Purification

Exact outside context.

The full tensor representation is centered/scaled directly without projection against proper subsets.

## 10.11 No-Outside-Context Full Hierarchy

Section 8.6 context.

All three orders and proper-subset purification remain enabled.

## 10.12 Exclusion-Matched Conditional HOFD

Uses the fixed exclusion-matched conditional HOFD procedure defined in the comparator specification above, with its numerical cutoff and ridge values from `comparators.exclusion_matched_conditional_hofd`.

This is an equivalence comparator, not the primary superiority comparator.

## 10.13 Conditional Pair Dependence

Uses the fixed conditional pair-dependence procedure defined above.

Maximum interaction order 2.

## 10.14 Exclusion-Matched Lancaster Triple

Uses the fixed Lancaster-moment triple reference defined above.

## 10.15 Connected Information Reference

Uses the fixed maximum-entropy lower-order reconstruction procedure defined above, with numerical fitting values from `comparators.connected_information`.

## 10.16 D-Vine Conditional Reference

Uses the fixed Gaussian D-vine procedure defined above.

## 10.17 Conditional Log-Linear Reference

Uses the fixed lower-order log-linear procedure defined above, with numerical fitting values from `comparators.conditional_log_linear`.

## 10.18 Global Factor Residual Reference

Uses the fixed PCA-residual procedure defined above, with rank candidates, variance target, and fallback rank from `comparators.global_factor_residual`.

## 10.19 Multistream CUSUM Reference

Uses the fixed multistream CUSUM procedure defined above, with its numerical recursion values from `comparators.multistream_cusum`.

## 10.20 FedAvg Autoencoder Reference

Uses the fixed unmatched ecological federated-learning procedure defined above, with FedAvg counts/fraction from `comparators.fedavg_autoencoder` and local autoencoder numerical hyperparameters from `detectors.autoencoder`.

It may be reported but does not determine the primary causal claim.

## 10.21 Strong Comparator Composition Selection

Candidates are defined by `experiments.strong_comparator_composition_challenge.candidates`.

Selection occurs before any real campaign outcome is inspected.

A candidate is eligible only if:

1. every required implementation invariant passes;
2. synthetic null calibrated finite-horizon calibration succeeds;
3. held-out synthetic null PFA satisfies the configured target.

The candidate's native target order is fixed as follows:

```text
Conditional Pair Dependence        -> order 2
Exclusion-Matched Lancaster Triple -> order 3
Connected Information Reference    -> order 3
D-Vine Conditional Reference       -> order 3
Conditional Log-Linear Reference   -> order 3
```

A candidate is scored only on the pure-polynomial reference generator at its declared native target order. This avoids inventing an unsupported order-specific extension for a method that was not defined at that order. The common reference effect is `generators.pure_polynomial.primary_reference_theta`; because the pure-polynomial target coordinate is orthonormal under the null, its population standardized target-order drift is exactly that theta value.

For each passing candidate, compute the standardized target-order estimation error exactly as defined in Section 13.5 and average it over `randomness.synthetic_development_roots`.

Select the candidate with the smallest mean error across development synthetic seeds.

If candidate errors differ by at most `experiments.strong_comparator_composition_challenge.error_tie_tolerance_standardized_units`, choose lower median compute time under the timing scope in Section 13.5.

If compute times differ by at most `experiments.strong_comparator_composition_challenge.runtime_tie_tolerance_seconds`, choose the lexicographically smaller method name.

The selected method identity and its native target order are written to `strongest-comparator-composition.json`. Downstream real-data use of `Selected Strong Comparator Composition` means exactly that selected method with its declared score, native maximum order, common calibrated finite-horizon backend, and no additional unselected component. Real outcomes are never inputs to this selection.


---

# 11. Metric registry

## 11.1 Strict ODI

$$
I_{ODI} =
\mathbf1
\left\lbrace
T_G\lt \min_iT_i
\right\rbrace.
$$

Range:

```text
0 or 1
```

## 11.2 Global stopping time

`global_stop_epoch` is the first global statistical stop after campaign start.

If no stop occurs within the horizon:

```text
raw value = null
censored_plot_value = horizon + evidence.no_stop_plot_offset_epochs
```

The censored value is never substituted into inferential stopping-time calculations.

## 11.3 Earliest local stopping time

$$
T_{\text{local,min}} =
\min_iT_i.
$$

Same no-stop semantics.

## 11.4 Statistical lead

$$
L_{stat} =
T_{\text{local,min}}-T_G.
$$

Defined only when both stops are finite.

## 11.5 Operational lead

$$
L_{op} =
T_{\text{local,min}} -
\left(
T_G+
\frac{\delta_{\text{seconds}}}
{\texttt{time.real＿data＿epoch＿seconds}}
\right).
$$

Defined only when both stops are finite.

## 11.6 Seed-level ODI rate

For seed $s$,

$$
R_{ODI,s} =
\frac1{|\mathcal C|}
\sum_{c\in\mathcal C}
I_{ODI,c,s}.
$$

The primary real inferential unit is the seed-level rate.

## 11.7 Campaign detection rate

$$
DR_s =
\frac{
\left\lvert\lbrace
c:T_{G,c,s}\le H
\rbrace\right\rvert
}{
|\mathcal C|
}.
$$

This is independent of ODI qualification.

## 11.8 Finite-horizon PFA

$$
\widehat{PFA}_{H} =
\frac1{N_0}
\sum_{h=1}^{N_0}
\mathbf1
{T_G^{(h)}\le H}.
$$

Report:

* point estimate;
* one-sided 95% exact upper bound.

## 11.9 False campaigns per 10,000 benign epochs

$$
10^4
\frac{
N_{\text{false declarations}}
}{
N_{\text{benign epochs}}
}.
$$

Descriptive only.

## 11.10 signed-theorem sequential ARL

Mean no-change stopping time.

Empirical simulation is a theorem-implementation diagnostic and does not replace the theoretical guarantee.

## 11.11 Self-explanation derivatives

Ordinary least squares over configured small perturbations produces:

$$
D_\eta =
\frac{dE[\eta]}{d\epsilon},
$$

$$
D_R =
\frac{dE[R]}{d\epsilon}.
$$

For Full FedCampaign-EMHI also report the signed target-atom coordinate derivative. Let $q^*$ denote the full-tensor basis coordinate whose every coalition member uses basis index 1, and let $\widetilde Z_{A,t,q^*}(\epsilon)$ be that calibrated standardized atom coordinate under perturbation $\epsilon$, before evidence clipping or norm aggregation. Using the same OLS-with-intercept procedure and the same post-settling epoch means as $D_\eta$ and $D_R$, define

\[
D_Z=\frac{d}{d\epsilon}\mathbb E[\widetilde Z_{A,q^*}].
\]

No alternate coordinate may be selected from observed derivative magnitude. $D_Z$ is descriptive mechanism evidence and is not substituted for the primary attenuation statistic.

### Self-explanation attenuation

For each context method $m$, define

$$
A_{\text{self}}^{(m)} =
1-
\frac{
|D_R^{(m)}|
}{
|D_{\text{direct}}|+
\texttt{numerics.metric＿denominator＿floor}
}.
$$

The primary material contrast for each seed is

$$
\Delta A_{\text{self}} =
A_{\text{self}}^{(\text{inclusive})} -
A_{\text{self}}^{(\text{exact})}.
$$

Positive values mean that inclusive context suppresses the direct perturbation response more strongly than exact exclusion. This is the sole attenuation statistic used for the primary materiality gate and primary directional hypothesis.

## 11.12 Mean log-evidence growth

For an attack interval,

$$
\kappa =
\frac1N
\sum_t\log e_{A,t}.
$$

## 11.13 Proper-subset drift

For proper subset $B$,

$$
\Delta_B =
\frac{
\left\|
\mu_{1,B}-\mu_{0,B}
\right\|_2
}{
\max
\left(
\sqrt{\mathrm{tr}(\Sigma_{0,B})},
\texttt{numerics.metric＿denominator＿floor}
\right)
}.
$$

Then

$$
D_{\lt A} =
\max_{B\subsetneq A}
\Delta_B.
$$

## 11.14 Target-order drift

For predeclared signed target coordinate $X_A$,

$$
D_A =
\frac{
E_1[X_A]-E_0[X_A]
}{
\max
(
SD_0(X_A),
\texttt{numerics.metric＿denominator＿floor}
)
}.
$$

## 11.15 Order-specific stopping probability

Fraction of seeded campaign trajectories for which an independently calibrated method using only the specified order stops inside the configured horizon.

## 11.16 Order evidence share

$$
R_r(t) =
\frac{
E_t^{(r)}
}{
\sum_{s\in\mathcal R}E_t^{(s)}
+
\texttt{numerics.metric＿denominator＿floor}
}.
$$

Descriptive only.

## 11.17 Decisive order

At a global stop epoch, consider enabled orders with

$$
E_t^{(r)}\gt 1.
$$

The decisive order is the order maximizing

$$
\log E_t^{(r)}.
$$

Ties within `numerics.deterministic_comparison_tolerance` choose the smaller order.

If no enabled order has $E_t^{(r)}\gt 1$, the value is `null`.

The metric never affects stopping.

## 11.18 Atom NRMSE

$$
NRMSE =
\frac{
\sqrt{
n^{-1}
\sum_t
|
Z_t^{EMHI}-Z_t^{HOFD}
|_2^2
}
}{
\sqrt{
n^{-1}
\sum_t
|
Z_t^{EMHI}
|_2^2
}
+
\texttt{numerics.metric＿denominator＿floor}
}.
$$

## 11.19 Atom cosine similarity

$$
\mathrm{cos} =
\frac{
\sum_t
\langle
Z_t^{EMHI},
Z_t^{HOFD}
\rangle
}{
\sqrt{
\sum_t
|Z_t^{EMHI}|_2^2
}
\sqrt{
\sum_t
|Z_t^{HOFD}|_2^2
}
+
\texttt{numerics.metric＿denominator＿floor}
}.
$$

## 11.20 Stopping-time difference

$$
\Delta T =
T_G^{EMHI}-T_G^{HOFD}.
$$

Only paired finite stops enter this continuous metric.

A companion paired detection-indicator difference must be reported so that missing finite pairs cannot hide differing non-detection behavior.

## 11.21 PFA difference

$$
\Delta PFA =
\widehat PFA^{EMHI} -
\widehat PFA^{comparison}.
$$

## 11.22 Conditional-rank MAE

Synthetic only:

$$
MAE =
\frac1n
\sum
|
\widehat U-U_{\text{truth}}
|.
$$

## 11.23 Projection NRMSE

Synthetic only. Let $P_t^\ast$ be the analytically known or independently generated high-precision population projection of $\Phi_{A,t}$ onto the proper-subset design, and let $\widehat P_t=\widehat M_{A,c}^\top X_{\lt A,t}$ be the fitted projection on an independent evaluation sample. Define

$$
NRMSE_{\text{proj}} =
\frac{
\sqrt{
n^{-1}\sum_t
\left\|
\widehat P_t-P_t^\ast
\right\|_2^2
}
}{
\sqrt{
n^{-1}\sum_t
\left\|
\Phi_{A,t}
\right\|_2^2
}
+
\texttt{numerics.metric＿denominator＿floor}
}.
$$

Normalization by the full tensor-representation RMS keeps the metric defined when the true proper-subset projection is exactly zero. Population truth and fitted estimates must be evaluated on the same independent sample rows.

## 11.24 Standardized null bias

$$
B_0 =
\frac{
|
\bar Z
|_2
}{
\max
\left(
\sqrt{\mathrm{tr}(\widehat\Sigma_Z)},
\texttt{numerics.metric＿denominator＿floor}
\right)
}.
$$

## 11.25 Context coverage

$$
\mathrm{coverage} =
\frac{
N_{\text{supported coalition-epochs}}
}{
N_{\text{eligible coalition-epochs}}
}.
$$

Eligibility means:

* coalition members available;
* minimum outside-client availability satisfied.

## 11.26 Abstention rate

$$
1-\mathrm{coverage}.
$$

## 11.27 Numerical failure rate

$$
\frac{
N_{\text{coalition/context fits failing a numerical invariant}}
}{
N_{\text{attempted coalition/context fits}}
}.
$$

Ordinary support-driven abstention is not a numerical failure.

## 11.28 Common-mode suppression

$$
1-
\frac{
PFA_{\text{EMHI}}
}{
PFA_{\text{RAW MEAN}}
+
\texttt{numerics.metric＿denominator＿floor}
}.
$$

## 11.29 Outside-conditioning power loss

$$
DR_{\text{NO OUTSIDE CONTEXT}} -
DR_{\text{EMHI}}.
$$

## 11.30 AUROC

Use the standard probability-of-ranking interpretation with malicious epoch as positive.

Ties contribute 0.5.

If only one class exists, result is:

```text
Not Defined
```

## 11.31 AUPRC

Average precision with malicious epoch positive.

If only one class exists:

```text
Not Defined
```

## 11.32 Coalition count

Derived as

$$
\sum_{r=1}^{R}
\binom Kr.
$$

For the primary method $R=3$.

## 11.33 Server compute latency

Time from availability of the final required client message in the reference harness to completion of:

```text
message decoding
→ context construction
→ coalition scoring
→ order aggregation
→ sequential state update
→ support predicate
→ decision
```

## 11.34 End-to-end reference-harness latency

Time from synthetic observation-epoch close to global decision completion, including:

```text
client detector inference
client marginal-rank lookup
local policy update
application-message packing
coordinator unpacking
server computation
```

Actual network transport and disk I/O are excluded.

The manuscript must call this a reference-harness computational latency, not real network end-to-end latency.

## 11.35 Application payload bytes

Each client message uses the fixed packed logical schema:

```text
client_ordinal: uint16
epoch_index: uint64
marginal_rank: float64
local_action_flag: uint8
availability_flag: uint8
```

The logical payload size is derived from the fixed field widths as 20 bytes per client per epoch. The federation payload is therefore $20K$ logical bytes per epoch. Transport headers are excluded from this application-payload quantity.

## 11.36 Throughput

$$
\frac{
\text{coalitions scored}
}{
\text{server compute seconds}
}.
$$

---

# 12. Campaign registry

For the evaluation portion of each real dataset:

1. mark every selected-client epoch containing at least one explicit malicious ground-truth event;
2. form the union of malicious epochs over selected clients;
3. identify contiguous malicious runs;
4. merge adjacent runs when the number of completely benign epochs between them is at most `campaign.merge_max_intervening_benign_epochs`;
5. collect all selected clients with explicit malicious activity in the merged episode;
6. require at least `distributed_support.minimum_clients` attacked clients;
7. compute each participating client's first malicious epoch;
8. require
$$
   \max_i t_i^{first} -
   \min_i t_i^{first}
   \le
   \texttt{campaign.distributed＿first＿activity＿window＿epochs};
$$
9. define the merged campaign duration as
$$
   \texttt{duration＿epochs}=\texttt{end＿epoch}-\texttt{start＿epoch}+1;
$$
   merged intervening benign epochs are part of the same campaign interval and therefore count toward this duration;
10. require
$$
   \texttt{duration＿epochs}\ge\texttt{campaign.minimum＿duration＿epochs};
$$
11. require the complete `campaign.prestart_warmup_epochs` pre-campaign warm-up with zero explicit malicious ground-truth epochs across selected clients.

Every eligible campaign is retained.

Weak, missed, late, and method-unfavorable campaigns are never removed.

Because an eligible campaign requires a complete clean warm-up, a later attack episode occurring within that clean-warm-up distance of a previous malicious episode is automatically ineligible as an independent campaign. This prevents overlapping attack episodes from being treated as independent clean-start campaigns.

The primary campaign key is semantic:

```text
dataset
start_epoch
end_epoch
sorted_participating_client_ids
```

A SHA-256 checksum of that tuple is stored only for integrity.

It is not the scientific campaign identity.

---

# 13. Experiment contracts

Every experiment below has a short descriptive scientific name. The public CLI uses the corresponding descriptive kebab-case slug; no opaque experiment code or numeric alias is part of the scientific contract.

Condition grids are part of the experiment registry and may not be supplied by an operator.

## 13.1 Synthetic Module Validation

**Classification:** validation  
**Seed:** `randomness.engineering_smoke_root`.

The smoke workflow uses the exact fixtures below. Expected values are part of the scientific implementation contract; tests may use smaller non-production configuration files only where the fixture explicitly depends on a configured value.

| Fixture | Exact input | Required expected result |
| --- | --- | --- |
| Midranks and ties | benign reference `[0.0, 0.5, 0.5, 1.0]`, query `0.5` | rank `(1 + 0.5*2 + 0.5)/5 = 0.5` |
| Rank clipping | raw ranks `0.0` and `1.0` | `context.rank_clip_epsilon` and `1-context.rank_clip_epsilon` |
| Histogram edges | configured 8 bins; ranks `[0.01, 0.13, 0.99]` | bin indices `[0,1,7]`; normalized histogram `[1/3,1/3,0,0,0,0,0,1/3]` |
| Context exclusion | selected clients `c1..c6`, coalition `{c1,c2,c3}` | exact context members `{c4,c5,c6}`; inclusive `{c1..c6}`; leave-one-out `{c2,c3,c4,c5,c6}`; partial triple exclusion `{c3,c4,c5,c6}` |
| Lag semantics | epoch `t=5`, lag `1` | all context features use epoch `4`; no epoch-5 coalition observation enters context |
| Deterministic K-means tie | centroids `(0,0)` and `(2,0)`, row `(1,0)` | centroid index `0` |
| Projection dimensions | basis size `L=3` | atom dimensions: order1 `3`, order2 `9`, order3 `27`; proper-subset design columns including intercept: order1 `1`, order2 `7`, order3 `37` |
| Ridge tie | two candidate lambdas `0.01` and `0.1` with validation-MSE difference no greater than `projection.selection_tie_tolerance_mse` | select `0.1` |
| Abstention | order-3 context support `399` then `400` | `399` abstains; `400` is supported |
| Blocked folds | ordered indices `0..10`, `k=5` | fold sizes `[3,2,2,2,2]` and folds `[0,1,2]`, `[3,4]`, `[5,6]`, `[7,8]`, `[9,10]` |
| Cross-fitted calibration | ordered indices `0..3`, `k=2` | held folds `[0,1]` and `[2,3]`; corresponding fit indices `[2,3]` and `[0,1]`; held-fold outputs concatenate back to original chronological order `[0,1,2,3]` |
| Signed evidence | `X=1`, `b=1`, `lambda=0.5`; and `X=-1` | factors `exp(0.375)` and `exp(-0.625)` respectively |
| Operational norm evidence | `||Z||_2=q_norm>projection.norm_reference_floor` | `X_norm=0` and factor `exp(-0.125)` |
| Distributed support | trailing-window materially active coalitions `{c1,c2}` and `{c2,c3}` | union `{c1,c2,c3}`; predicate true for configured minimum 2 |
| Finite-horizon threshold selection | `n=200`; false-stop counts for thresholds `2,3,5,10` equal `20,15,5,0` | threshold `5` fails because its one-sided 95% CP UCB is greater than `0.05`; threshold `10` qualifies and is selected as the smallest qualifying candidate |
| Local persistence | exceedance indicators `[1,0,1]` for a 2-of-3 rule | no trigger at epochs 1 or 2; trigger at epoch 3 |
| Strict ODI inequality | `T_G=4`, local stops `[5,8]` | ODI `1` |
| Same-epoch tie | `T_G=5`, local stops `[5,8]` | ODI `0` |
| Null no-stop storage | no global stop in a 60-epoch horizon | raw stop `null`; plotting value `61` |
| Semantic idempotency | material semantic record `{"dataset":"fixture","seed":999,"role":"score"}` canonicalized twice | identical RFC-8785 bytes, identical SHA-256 dependency fingerprint, identical semantic active path, and one active artifact identity rather than a second run identity |

Histogram binning uses

$$
B(u)=\min
\left(
\left\lfloor u\,\texttt{context.outside＿histogram＿bin＿count}\right\rfloor,
\texttt{context.outside＿histogram＿bin＿count}-1
\right),
$$

which is equivalent to equal-width left-closed/right-open bins on $[0,1]$ with the last bin closed at 1 before rank clipping.

Pass requires every exact fixture to match its expected result within the concept-specific exact/tolerance rule already defined by this roadmap. No approximate visual inspection constitutes a pass.

## 13.2 Self-Explanation Exclusion Validation

**Classification:** claim-bearing controlled mechanism.
**Configuration:** `experiments.self_explanation_exclusion_validation`.

The client-count grid is `robustness.scalability_client_counts`; coalition orders are all orders from 1 through `study.maximum_coalition_order`; persistent perturbations are `generators.self_explanation.perturbations`; and context methods are `experiments.self_explanation_exclusion_validation.context_methods`.

The nuisance transformations are the fixed linear, tanh, and softplus transformations defined in the self-explanation generator specification.

Each seed executes the complete grid.

Development seeds are `randomness.synthetic_development_roots`.

Confirmatory seeds are `randomness.synthetic_confirmatory_roots`.

Primary inferential condition is defined by `experiments.self_explanation_exclusion_validation.primary_condition`.

Primary requirements:

* exact nuisance derivative equivalent to zero within configured margin;
* inclusive-minus-exact material attenuation at least configured threshold;
* primary adjusted directional test passes.

Other K/order/nuisance combinations are predeclared generality diagnostics.

## 13.3 Pure-Order Separation Validation

**Classification:** claim-bearing controlled mechanism.
**Configuration:** `experiments.pure_order_separation_validation`.

Primary client count is `experiments.pure_order_separation_validation.primary_client_count`.

Generators are `experiments.pure_order_separation_validation.generators`. Effect grids are `generators.pure_polynomial.theta`, `generators.xor.strengths`, and the other generator-specific values defined in the Configuration YAML.

Methods are `experiments.pure_order_separation_validation.methods`.

Before a method is scored, the empirical generator-purity validator evaluates proper-subset distributions against high-precision generated truth.

A generator condition whose population-validation estimate violates its mathematical purity tolerance is Invalid and must be repaired rather than interpreted scientifically.

Primary inferential condition is defined by `experiments.pure_order_separation_validation.primary_condition`; its effect is `generators.pure_polynomial.primary_reference_theta`.

### Generator-purity validation

Purity is established from the declared generator law, not inferred from a finite Monte Carlo sample. The validator mechanically evaluates the following exact identities before method scoring:

* pure polynomial order-$r$: integrating the density over any nonempty omitted target coordinate yields the uniform density on every proper subset because each nonconstant basis coordinate has zero integral on $[0,1]$;
* XOR: exact enumeration of the eight binary states verifies Bernoulli(0.5) univariate marginals and independent pair marginals for every configured strength, while the independent jitter preserves uniform continuous marginals;
* context-dependent pure triple: the same pure-polynomial marginalization identity is checked separately for both latent states;
* mixed-order generators: the enabled-term set is treated as the exact population truth; a term declared absent must integrate to zero under the appropriate proper-subset marginalization, while enabled lower-order terms are not incorrectly required to vanish.

The implementation evaluates these identities symbolically where the generator is polynomial/discrete and by exact finite-state enumeration for XOR. A deterministic numerical check is permitted only as a secondary implementation check and must agree with the analytic result within `numerics.deterministic_comparison_tolerance`. A failed analytic identity or a negative/non-finite density makes the condition Invalid. Finite-sample empirical drift is reported as a sampling diagnostic but never decides generator validity.

## 13.4 Exclusion-Matched HOFD Equivalence

**Classification:** claim-bearing equivalence.  
**Configuration:** `experiments.exclusion_matched_hofd_equivalence`.

The population is the pure-polynomial family at primary client count `experiments.pure_order_separation_validation.primary_client_count`. For each coalition order $r=1,2,3$, the target coalition is the first $r$ lexicographic clients, the remaining clients follow the independent-uniform population-completion rule, and the target effect is `generators.pure_polynomial.primary_reference_theta`. The corresponding zero-effect population supplies null calibration data.

Support per context is `support_grids.hofd_equivalence_samples_per_context`. Exact-exclusion outside-field construction is retained, but this equivalence experiment uses `experiments.exclusion_matched_hofd_equivalence.context_cell_count` equal to one for both methods. The outside histogram and complement provenance are still computed and validated; all rows are assigned to the single comparison cell so the declared support is exact and the experiment isolates projection/orthogonalization differences rather than context-clustering error. This is not the No-Outside-Context ablation.

Methods are defined by `experiments.exclusion_matched_hofd_equivalence.methods` and use the same basis, proper-subset column space, nuisance sample rows, held-out rows, and finite-horizon calibration horizons.

Development seeds are `randomness.synthetic_development_roots`; confirmatory seeds are `randomness.synthetic_confirmatory_roots`.

For every support/order/seed condition:

1. generate the declared number of benign nuisance rows under the zero-effect population;
2. fit EMHI and conditional HOFD on exactly those shared null rows;
3. evaluate paired atom outputs on `synthetic.sample_sizes.hofd_equivalence_heldout_samples_per_context_seed` independent target-effect held-out rows;
4. independently calibrate each sequential route on null horizons generated from the zero-effect population;
5. evaluate paired 60-epoch effect trajectories generated from the target-effect population for stopping-time comparison.

Primary equivalence support levels are `experiments.exclusion_matched_hofd_equivalence.primary_support_levels`.

At each primary support level, both methods must satisfy the configured finite-horizon null-PFA requirement before stopping-time equivalence is interpreted. Equivalence then requires:

* the complete paired 95% BCa CI for seed-level atom NRMSE to lie below `claim_materiality.hofd_equivalence.atom_nrmse_upper_margin`;
* the mean seed-level atom cosine similarity to be at least `claim_materiality.hofd_equivalence.minimum_cosine_similarity`;
* the complete paired 95% BCa CI for seed-level mean finite-stop stopping-time difference to lie inside `claim_materiality.hofd_equivalence.stopping_time_difference_interval_epochs`;
* the paired detection-indicator difference to be reported alongside the finite-stop comparison.

Unexpected large superiority of either implementation triggers investigation and cannot be marketed as expected scientific superiority.

## 13.5 Strong Comparator Composition Challenge

**Classification:** pre-real comparator-selection validation.  
**Configuration:** `experiments.strong_comparator_composition_challenge`.

Candidates are defined by `experiments.strong_comparator_composition_challenge.candidates` and use the native target-order mapping in Section 10.21.

Data:

* pure order-2 reference effect using `generators.pure_polynomial.primary_reference_theta` with the first two clients as target;
* pure continuous order-3 reference effect using `generators.pure_polynomial.primary_reference_theta` with the first three clients as target;
* mixed-order conditions from `generators.mixed_order.enabled_term_sets` with `generators.mixed_order.term_coefficient`;
* zero-effect pure-polynomial null horizons for candidate finite-horizon calibration and held-out null PFA.

The population client count is `experiments.pure_order_separation_validation.primary_client_count`; non-target clients use the independent-uniform completion rule. Seeds are `randomness.synthetic_development_roots`. No real campaign outcome may be read before the selected identity exists.

For candidate $m$, let $r_m$ be its native target order. Fit the candidate on the same nuisance-fit rows used by every other candidate, evaluate it on the independent pure-polynomial reference rows for order $r_m$, orient the candidate so larger means more anomalous according to its declared comparator contract, and standardize its raw target-order score using only the corresponding zero-effect nuisance-fit score mean and standard deviation. If that null standard deviation is non-finite or no greater than `numerics.metric_denominator_floor`, the candidate is ineligible.

For seed $s$, let $D^m_s$ be the mean standardized candidate score on the target-effect reference rows. For the pure-polynomial family, the analytic population standardized drift of the orthonormal target coordinate is

\[
D^{truth}_{r_m}=\theta_{ref},
\qquad
\theta_{ref}=\texttt{generators.pure＿polynomial.primary＿reference＿theta}.
\]

The seed-level standardized target-order estimation error is

\[
e_{m,s}=\left|D^m_s-D^{truth}_{r_m}\right|,
\]

and the selection statistic is

\[
E_m=\frac{1}{|\mathcal S|}\sum_{s\in\mathcal S}e_{m,s},
\]

where $\mathcal S$ is `randomness.synthetic_development_roots`. Because both the candidate output and analytic target are expressed in null-standard-deviation units, $E_m$ is directly comparable across the declared order-2 and order-3 native targets.

Mixed-order rows are mandatory diagnostics and candidate validity checks but do not alter $E_m$. A mixed-order diagnostic is valid only when the candidate produces a finite score under its declared native-order contract; no unsupported higher- or lower-order extension is invented.

A candidate is eligible only if every required implementation invariant passes and its independently calibrated held-out null PFA one-sided UCB satisfies `evidence.calibrated_finite_horizon.target_pfa` using `synthetic.sample_sizes.finite_horizon_calibration_horizons_per_seed` calibration horizons and `synthetic.sample_sizes.finite_horizon_heldout_null_horizons_per_seed` held-out horizons per seed.

Select the eligible candidate with the smallest $E_m$. If two errors differ by no more than `experiments.strong_comparator_composition_challenge.error_tie_tolerance_standardized_units`, use median scoring runtime as the first tiebreak.

Runtime tiebreak scope is fixed: after fitting is complete, perform one unmeasured scoring pass and then time one scoring pass over exactly `synthetic.sample_sizes.pure_order_independent_evaluation_samples_per_condition_seed` held-out rows from that candidate's native pure-order reference condition. Disk I/O and fitting are excluded. Use a monotonic high-resolution clock in one process under the same observed runtime environment for all candidates; candidate runtime is the median elapsed scoring time across development seeds. If compute times differ by no more than `experiments.strong_comparator_composition_challenge.runtime_tie_tolerance_seconds`, choose the lexicographically smaller method name.

The selection artifact is written to `outputs/experiments/strong-comparator-composition-challenge/artifacts/derived/<artifact_filename>`, where `<artifact_filename>` is `experiments.strong_comparator_composition_challenge.artifact_filename`, and contains:

```text
selected_method
selected_native_order
eligible_candidates
candidate_native_orders
null_PFA_results
target_error_results
runtime_tiebreak_results
selection_rule_hash
source_artifact_hashes
```

The selected method identity is immutable for downstream real-data experiments under the same material dependency fingerprint. Re-selection occurs automatically only when a material dependency of the selection artifact changes; real outcomes are never a material input to selection.


## 13.6 Estimator Support and Context Feasibility

**Classification:** claim-bearing feasibility plus sensitivity.  
**Configuration:** `experiments.estimator_support_and_context_feasibility`.

This experiment uses the deterministic context-support generator implemented in `synthetic/feasibility.py`. It is not an additional scientific generator family; it is the fully specified support substrate for this existing feasibility experiment and is derived only from the requested context-cell count and the roadmap's existing rank/context definitions.

For a condition with requested context-cell count $C$:

1. use client count `experiments.pure_order_separation_validation.primary_client_count`;
2. use the first $r$ lexicographic clients as the target coalition for order (r in \lbrace1,2,3\rbrace);
3. define latent support-cell index $c_t=t \bmod C$;
4. for every non-target client at epoch $t$, set its outside marginal rank to the deterministic midpoint
   \[
   U^M_{j,t}=\frac{c_t+1/2}{C};
\]
5. draw every target-client rank independently as Uniform(0,1) from the seed/component substream;
6. use one initial unscored row so the one-epoch outside lag is defined, then cycle through all $C$ cells in order.

With `context.outside_histogram_bin_count=8` and every declared (C in \lbrace2,4,8\rbrace), these midpoint values map to distinct deterministic histogram locations. Therefore the requested K-means context cells are identifiable without using the latent label, while the estimator still receives only the roadmap-defined lagged outside histogram and K-means assignment. The latent support-cell index is used only to construct exact support counts and evaluate known truth.

For a requested support value $n$, generate exactly $nC+1$ rows and discard only the initial lag row. This yields exactly $n$ usable nuisance-fit observations in every latent support cell. No oversampling, truncation choice, or random cell balancing is left to the implementation.

Under the primary zero-effect law, target ranks are conditionally Uniform(0,1) in every support cell. Therefore:

* the exact conditional-rank truth is the target marginal rank itself;
* the population proper-subset projection of each orthonormal target tensor is zero;
* the population atom centering is zero and population null variance is one before the roadmap's fitted finite-sample standardization.

These analytic truths are the references for conditional-rank MAE, projection NRMSE, and standardized null bias. A development-only effect diagnostic may replace the target null law with the pure-polynomial target interaction at `generators.pure_polynomial.primary_reference_theta` while retaining the same context-support substrate; it cannot alter the feasibility decision.

Primary support sweep is `support_grids.estimator_samples_per_context`. Primary estimator settings use `basis.primary_size`, `context.primary_cell_count`, and ridge selection by the blocked cross-validation rule in Section 4.8.

Coalition orders are all orders from 1 through `study.maximum_coalition_order`.

One-factor sensitivity support levels are `support_grids.estimator_one_factor_sensitivity_samples_per_context`. Basis-size sensitivity uses `basis.sensitivity_sizes`; context-cell sensitivity uses `context.cell_count_sensitivity`; forced-ridge and forced-no-abstention values are under `experiments.estimator_support_and_context_feasibility.sensitivity`.

Development seeds are `randomness.synthetic_development_roots`. Confirmatory seeds are `randomness.synthetic_confirmatory_roots` and are used only for the primary order-three feasibility condition; sensitivity settings remain development-only.

Each fitted condition is evaluated on a fresh independent context-support sequence containing exactly `synthetic.sample_sizes.estimator_evaluation_samples_per_context_seed` usable rows per latent support cell, plus the single required initial lag row.

Metrics:

* conditional-rank MAE;
* projection NRMSE from Section 11.23;
* standardized null bias;
* context coverage;
* abstention;
* condition number;
* numerical failure.

Order-three feasibility is assessed at support `context.minimum_support_epochs.order_three`, with `basis.primary_size`, `context.primary_cell_count`, and ridge selection by the blocked cross-validation rule in Section 4.8.

Feasibility aggregation over confirmatory seeds is:

* mean seed-level coverage;
* mean seed-level projection NRMSE;
* mean seed-level standardized null bias;
* pooled numerical-failure rate, with numerator and denominator summed over confirmatory seeds before division.

The support condition is scientifically complete even when one or more criteria fail; failure downscopes the order-three claim according to Section 15.

Sensitivity settings cannot replace primary settings.


## 13.7 Sequential Evidence Validation

**Classification:** claim-bearing controlled validation.  
**Configuration:** `experiments.sequential_evidence_validation`.

Development seeds are `randomness.synthetic_development_roots`; confirmatory seeds are `randomness.synthetic_confirmatory_roots`.

### Signed-Theorem Sequential Route

The controlled theorem route validates the inherited bounded e-detector construction without confounding it with finite-sample nuisance/projection estimation. The target coalition is the first three clients and, under the null, its ranks are independent Uniform(0,1). Non-target clients follow the independent-uniform completion rule but do not enter the signed coordinate.

Let

\[
q_t=\phi_1(U_{1,t})\phi_1(U_{2,t})\phi_1(U_{3,t}),
\]

using the roadmap's first orthonormal shifted-Legendre basis coordinate. The theorem-route signed statistic supplied directly to Section 4.11 is

\[
X_t=\mathrm{clip}\!\left(q_t,-b,b\right),
\qquad
b=\texttt{evidence.clip＿bound}.
\]

The direction is fixed before sampling. Under the declared independent null, $q_t$ has a distribution symmetric about zero, clipping is an odd function, and each trajectory is independent over time; consequently

\[
\mathbb E[X_t\mid\mathcal F^G_{t-1}]=0.
\]

This population-known signed coordinate is used only for the theorem-route validation. It does not substitute for the fitted EMHI estimator in any real-data or finite-estimator experiment; finite-estimator behavior is tested separately in Section 13.6 and operational false-campaign behavior is tested by the calibrated finite-horizon route below.

For each seed, trajectory count and maximum length are defined by `experiments.sequential_evidence_validation.signed_theorem`. Stopping trajectories terminate at threshold crossing. A trajectory not stopping by the configured maximum is right-censored for descriptive stopping-time output.

For restricted-ARL computation define

\[
T^{RM}=\min(T,M),
\]

where $M$ is the configured maximum trajectory length and a non-stopping trajectory contributes exactly $M$. The seed-level restricted ARL is the arithmetic mean of $T^{RM}$ over that seed's trajectories. The one-sided 95% BCa lower confidence bound is computed across independent seed-level restricted-ARL values.

The theorem-assumption checker must mechanically verify:

* the signed coordinate and clipping bound are fixed before trajectory sampling;
* every generated $X_t$ is finite and lies in $[-b,b]$;
* the generator identity is the declared iid Uniform(0,1) target-rank null and therefore the analytic conditional mean above is exactly zero;
* the Section 4.11 compensator is exactly $\lambda^2(2b)^2/8$ with configured $b$ and $\lambda$;
* every one-step evidence factor is finite and nonnegative;
* the e-SR threshold is exactly `1 / evidence.signed_theorem_sequential.arl_alpha`;
* no attack data, held-out outcome, fitted nuisance object, local-policy state, or real-data artifact enters this route.

The nonasymptotic ARL interpretation follows the e-detector/e-process construction of Shin, Ramdas, and Rinaldo, *E-detectors: a nonparametric framework for sequential change detection*. The simulation diagnostic does not replace that theorem and does not establish real-data anytime validity.

The implementation diagnostic passes when all mechanical checks pass and the one-sided BCa lower bound of the confirmatory seed-level mean restricted ARL meets `experiments.sequential_evidence_validation.signed_theorem.restricted_arl_bootstrap_lower_bound_minimum_epochs`.

### Calibrated Finite-Horizon Route

The null population is the common-mode generator with client count `experiments.pure_order_separation_validation.primary_client_count`, all clients available, and all method orders from 1 through `study.maximum_coalition_order` enabled. This deliberately validates the operational route under benign cross-client dependence rather than an independent-null special case.

For every seed:

* generate `synthetic.sample_sizes.finite_horizon_calibration_horizons_per_seed` independent null calibration horizons;
* generate `synthetic.sample_sizes.finite_horizon_heldout_null_horizons_per_seed` independent held-out null horizons;
* each horizon contains the configured warm-up required for lagged context construction followed by exactly `campaign.evaluation_horizon_epochs` scored epochs;
* fit nuisance/context/projection/calibration artifacts only from independent nuisance-fit material generated under the same null law;
* execute the complete operational norm evidence path, equal-order aggregation, sequential recursion, and distributed-support predicate;
* select the finite-horizon threshold only from calibration horizons;
* evaluate held-out PFA without modifying the selected threshold.

The route passes when the held-out one-sided Clopper-Pearson PFA UCB meets `evidence.calibrated_finite_horizon.target_pfa` for every confirmatory seed with an available calibrated threshold. If calibration yields Operating Point Unavailable for any required confirmatory seed, the route remains a valid Completed outcome but the calibrated-route support statement is Not Supported.

## 13.8 Primary Strict ODI Evaluation

**Classification:** primary real confirmatory experiment.
**Configuration:** `experiments.primary_strict_odi_evaluation`.

The dataset is `datasets.primary.name`.

Methods are `experiments.primary_strict_odi_evaluation.methods`.

Development seeds are `randomness.real_development_roots`.

Confirmatory seeds are `randomness.real_confirmatory_roots`.

Every eligible campaign from the fixed registry is evaluated.

The primary paired causal comparator is Exclusion-Matched Order-at-Most-Two EMHI.

The HOFD implementation remains an equivalence comparator.

The FedAvg autoencoder remains unmatched ecological context.

### Full FedCampaign-EMHI support criteria

Held-out full-method PFA must satisfy the confidence and target configured under `evidence.calibrated_finite_horizon`.

Mean seed-level strict ODI must meet `claim_materiality.primary_real.minimum_strict_odi_rate`.

Mean paired ODI-rate advantage over order-at-most-two must meet `claim_materiality.primary_real.minimum_odi_rate_advantage_over_order_at_most_two`.

Median operational lead among strict-ODI successes must meet `claim_materiality.primary_real.minimum_median_operational_lead_epochs`.

Primary ODI advantage directional inference uses the fixed Holm correction defined in Sections 14.10–14.11 and `statistics.nominal_significance_alpha`.

Both Full FedCampaign-EMHI and the primary causal comparator must have an eligible matched calibrated finite-horizon operating point.

## 13.9 Exclusion Mechanism Ablation

**Configuration:** `experiments.exclusion_mechanism_ablation`.

The dataset is `datasets.primary.name`.

Methods are `experiments.exclusion_mechanism_ablation.methods`.

Development seeds are `randomness.real_development_roots`; confirmatory seeds are `randomness.real_confirmatory_roots`.

Primary metrics:

* PFA;
* detection rate;
* ODI rate;
* operational lead;
* context coverage;
* decisive order.

The three predeclared contrasts against Full FedCampaign-EMHI participate in the secondary Holm family.

## 13.10 Purification and Order Ablation

**Configuration:** `experiments.purification_and_order_ablation`.

The dataset is `datasets.primary.name`.

Methods are `experiments.purification_and_order_ablation.methods`.

Development seeds are `randomness.real_development_roots`; confirmatory seeds are `randomness.real_confirmatory_roots`.

Material order-3 contribution is

$$
R_{ODI,\text{full}} -
R_{ODI,\le2}.
$$

Order-Three Scope requires this mean paired difference to be at least the configured real-order-3 materiality threshold in addition to synthetic/estimator support.

## 13.11 Context and Estimator Sensitivity

**Classification:** development-only robustness.  
**Configuration:** `experiments.context_and_estimator_sensitivity`.

The dataset is `datasets.primary.name`. The base method is Full FedCampaign-EMHI under the primary configuration. Seeds are `randomness.real_development_roots` only. The selected clients, detector models, detector score streams, campaign registry, benign partitions, local policies, PFA target, and campaign horizon are exactly those of Primary Strict ODI Evaluation wherever their material dependencies match.

One-factor sensitivity changes exactly one of the following at a time while every other primary value remains unchanged:

* basis size to each value in `basis.sensitivity_sizes`;
* context cell count to each value in `context.cell_count_sensitivity`;
* ridge penalty forced to `experiments.context_and_estimator_sensitivity.forced_ridge`;
* Shuffled Outside Context;
* Local-History-Only Context;
* Forced No-Abstention.

For every sensitivity cell, recompute only estimator/context/calibration descendants whose material dependency changes. Primary metrics are held-out PFA, campaign detection rate, strict ODI rate, operational lead, context coverage, abstention rate, and numerical failure rate. Results are paired descriptively against the base Full FedCampaign-EMHI development seed with the same data/model artifacts.

No result from this experiment may replace a primary configuration value. No unadjusted sensitivity p-value creates a manuscript claim.

## 13.12 Benign Common-Mode Robustness

**Configuration:** `experiments.benign_common_mode_robustness`.

The dataset is `datasets.primary.name`. Development seeds are `randomness.real_development_roots`; confirmatory seeds are `randomness.real_confirmatory_roots`.

Methods are `experiments.benign_common_mode_robustness.methods`.

This experiment has one negative branch and one positive-power branch. The negative branch uses only `heldout_benign`; the positive-power branch reuses the same eligible real campaign registry, fixed global/local artifacts, and campaign replay semantics as Primary Strict ODI Evaluation. No campaign is created from held-out benign data and no held-out benign window is relabeled as an attack.

Negative conditions:

### Native non-overlapping benign horizons

The same horizons used for held-out PFA.

### Native high-volume stress windows

Create rolling windows over held-out benign data with length `campaign.evaluation_horizon_epochs` and stride `experiments.benign_common_mode_robustness.native_high_volume_window.stride_epochs`.

Rank windows by federation-wide total raw event count.

Select the top configured event-count fraction using `experiments.benign_common_mode_robustness.native_high_volume_window.top_event_count_fraction`; retain all percentile-boundary ties.

These overlapping windows are robustness diagnostics only and are never used for Clopper-Pearson PFA inference.

### Synthetic-on-real count stress

For each factor in `robustness.benign_count_multiplication_factors`:

* multiply every raw event-count bucket before `log1p`;
* multiply the total event-count feature by the same factor;
* preserve bucket proportions, so Shannon entropy is unchanged;
* do not round the synthetic multiplied counts.

Affected detector scores and downstream evidence are recomputed from the first changed feature layer. These stress rows remain benign and cannot enter campaign-power calculations.

### Positive-power branch

Campaign detection rate is evaluated on every eligible primary real campaign for Full FedCampaign-EMHI and No-Outside-Context Full Hierarchy using the same seed, detector streams, local policies, finite-horizon calibration target, campaign horizon, and campaign registry. The seed-level power-loss metric is exactly Section 11.29:

$$
DR_{\text{NO OUTSIDE CONTEXT},s} -
DR_{\text{EMHI},s}.
$$

The primary common-mode false-campaign hypothesis uses the native high-volume stress windows. For each seed, define the stress-window false-declaration rate for each method as the fraction of selected stress windows with a global stop. The directional primary test uses the paired seed-level difference

$$
FCR_{\text{RAW MEAN},s}-FCR_{\text{EMHI},s}.
$$

Support requires:

* mean seed-level common-mode suppression relative to Raw Mean Rank Fusion at least `claim_materiality.benign_common_mode.minimum_false_campaign_suppression`;
* mean seed-level positive-power loss relative to No-Outside-Context Full Hierarchy no greater than `claim_materiality.benign_common_mode.maximum_detection_rate_loss`;
* the adjusted primary directional p-value for false-campaign reduction below `statistics.nominal_significance_alpha`.

## 13.13 Strong Local Policy Challenge

The dataset is `datasets.primary.name`.

The global method is Full FedCampaign-EMHI.

The global artifacts are identical to the primary method.

Only the local reference changes to the independently calibrated strong-local policy.

Development seeds are `randomness.real_development_roots`; confirmatory seeds are `randomness.real_confirmatory_roots`.

Support requires:

* mean seed-level ODI rate at least configured minimum;
* adjusted primary one-sided test of
$$
  R_{ODI,s}-\texttt{claim＿materiality.strong＿local.minimum＿strict＿odi＿rate}
$$
  passing.

## 13.14 Secondary Controlled-Trace Generalization

**Configuration:** `experiments.secondary_controlled_trace_generalization`.

The dataset is `datasets.secondary.name`.

Eligibility follows Section 6.

Methods are `experiments.secondary_controlled_trace_generalization.methods`.

Development seeds are `randomness.real_development_roots`; confirmatory seeds are `randomness.real_confirmatory_roots`.

Interpretation is restricted to validation on a second controlled provenance trace.

## 13.15 Outside-Campaign Contamination Boundary

**Configuration values:** `generators.outside_contamination`.

Controlled context-dependent triple generator.

Conditions are `generators.outside_contamination.correlated_campaign_fractions`.

Target client count is `generators.outside_contamination.client_count`; the target coalition is the first three lexicographic clients; the target effect is `generators.outside_contamination.target_triple_theta`.

Development seeds are `randomness.synthetic_development_roots`; confirmatory seeds are `randomness.synthetic_confirmatory_roots`.

Metrics:

* target-order drift;
* detection rate;
* context coverage;
* abstention;
* null PFA.

This experiment identifies an over-conditioning boundary; it does not create robustness claims beyond its tested range.

## 13.16 Client Dropout and Context Sparsity Boundary

**Configuration values:** `robustness.scalability_client_counts` and `generators.client_dropout.unavailable_fractions`.

Controlled context-dependent triple generator.

Client counts are `robustness.scalability_client_counts`.

Dropout fractions are `generators.client_dropout.unavailable_fractions`.

Development synthetic seeds are `randomness.synthetic_development_roots`.

Metrics:

* coverage;
* abstention;
* standardized null bias;
* detection rate;
* latency.

This experiment remains a predeclared development-only failure-boundary study and does not create an independent manuscript support claim.

## 13.17 Coalition Scalability

**Configuration values:** `robustness.scalability_client_counts` and `scalability_timing`.

Client counts are `robustness.scalability_client_counts`. Development timing seeds are `randomness.real_development_roots`; confirmatory timing seeds are `randomness.real_confirmatory_roots`. Enabled orders are all orders from 1 through `study.maximum_coalition_order`.

### Reference-harness synthetic workload

Scalability uses a synthetic workload because the real datasets do not provide every configured client count. The workload preserves the production feature dimension, detector-family mix, EMHI orders, context construction, local-policy update, application message schema, and complete in-process decision path. It is timing evidence only and cannot be used as detector-accuracy or campaign-detection evidence.

Let

\[
d=\texttt{datasets.preprocessing.event＿type＿hash＿bucket＿count}+2.
\]

For each K/seed:

1. create K lexicographically named clients `client-000` through `client-(K-1)`;
2. generate exactly `synthetic.sample_sizes.generic_nuisance_fit_epochs` detector-fit rows per client in already-scaled model-input space. For epoch $t$, generate a stationary Gaussian AR(1) common factor
   \[
   Z_t=\rho Z_{t-1}+\sqrt{1-\rho^2}\,\xi_t,
   \qquad \xi_t\sim N(0,1),
\]
   with $\rho=`generators.common_mode.latent_ar_coefficient`$ and $Z_0\sim N(0,1)$. For client index $j$, derive loading
   \[
   \beta_j=\beta_{min}+\frac{j}{\max(K-1,1)}(\beta_{max}-\beta_{min}),
\]
   from the configured common-mode loading bounds. The first feature is
   \[
   X_{j,t,1}=\beta_j Z_t+\varepsilon_{j,t},
   \qquad \varepsilon_{j,t}\sim N(0,\sigma^2),
\]
   with `generators.common_mode.client_noise_standard_deviation` for $\sigma$. Features 2 through $d$ are iid $N(0,1)$, independent across client, feature, and epoch and independent of $Z_t$. All draws use deterministic component substreams;
3. assign detector families by the production modulo-three rule and fit them using these rows and the production detector hyperparameters. Artifact-fit wall time is recorded separately and excluded from per-epoch latency;
4. generate an independent nuisance/context stream of the same configured length under the identical law, score it with the fitted detectors, form marginal ranks, and fit complete Full FedCampaign-EMHI context/projection/cross-fit artifacts;
5. from independent synthetic benign horizons under the same law, construct candidate local policies using the production nuisance-threshold and threshold/policy-calibration rules for every client. If no primary local candidate qualifies for a client, retain the most stringent configured candidate solely to exercise the local-policy update path and mark the cell `Local Timing Operating Point Unavailable`; this timing-only fallback cannot support a local-PFA, ODI, or detection claim;
6. independently generate `synthetic.sample_sizes.finite_horizon_calibration_horizons_per_seed` null horizons and select the global operational threshold by the production calibrated finite-horizon rule. If no candidate qualifies, retain the largest configured global threshold solely to exercise the decision path and mark the cell `Global Timing Operating Point Unavailable`; this timing-only fallback cannot support PFA or detection claims;
7. generate the unmeasured warm-up and measured feature epochs from fresh deterministic substreams under the same benign law. All clients are available in this experiment.

No scaler is fitted in this timing-only feature generator because rows are explicitly defined in production model-input coordinates; timing therefore measures the declared detector/scoring/EMHI/decision path rather than dataset parsing or robust-scaler preprocessing.

### Measurement procedure

For each seed/K:

1. fit required artifacts and record artifact-fit wall time separately;
2. load all artifacts into memory before timing;
3. execute `scalability_timing.unmeasured_harness_warmup_epochs` unmeasured epochs;
4. run `scalability_timing.measured_repetitions_per_seed_client_count` measured repetitions;
5. each repetition contains `scalability_timing.measured_epochs_per_repetition` consecutive epochs;
6. reset global sequential state and local persistence windows at the start of each repetition while reusing fitted/calibration artifacts;
7. concurrency is exactly `scalability_timing.concurrent_experiment_cells`;
8. disk I/O, artifact loading, preprocessing, detector fitting, estimator fitting, and calibration are excluded from measured intervals;
9. the end-to-end interval begins at synthetic observation-epoch close and ends when client score/rank production, coalition-context construction, atom scoring, global evidence update, distributed-support check, global decision, and local-policy update for that epoch are complete, exactly as Section 11.34 defines;
10. server-only timing follows Section 11.33;
11. peak RSS is the maximum resident-set size observed from immediately after all artifacts are loaded through the end of the last measured repetition, excluding prior fit/calibration peaks.

Metrics:

* derived coalition count;
* artifact-fit time;
* median server latency;
* p95 server latency;
* median reference-harness end-to-end latency;
* p95 reference-harness end-to-end latency;
* peak RSS during the declared measurement scope;
* throughput;
* application payload bytes;
* numerical-failure rate;
* local/global timing operating-point state.

Scalability support is based on confirmatory timing seeds. For every configured K, pooled numerical failure rate must not exceed `claim_materiality.maximum_pooled_numerical_failure_rate` and the seed-level p95 reference-harness end-to-end latencies must aggregate by the configured `scalability_timing.result_quantile`; the resulting reported p95 must not exceed `claim_materiality.reference_harness.p95_latency_maximum_seconds`.

All claim-bearing K cells must execute under one common timing environment satisfying Section 19.3. Results are explicitly conditional on that recorded reference environment and do not imply real network latency or production deployment performance.


---

# 14. Statistical analysis protocol

## 14.1 Controlled experimental unit

The independent unit is the generator root seed.

Rows from:

* clients;
* coalitions;
* contexts;
* time points;
* perturbation values;
* effect-grid values

within the same seed are repeated measurements.

They are never treated as independent replicates.

## 14.2 Real experimental unit

For primary inference, the independent unit is the algorithm root seed after aggregation over the complete fixed campaign registry.

The ten seed-level values form the paired sample.

Campaign×seed rows are not treated as independent observations.

## 14.3 Pairing key

A real paired comparison requires identical:

```text
dataset identity
observed selected-client list
campaign registry
preprocessing artifact
seed
local detector family assignment
local detector artifacts when the comparison is designed to share them
local policy artifacts
campaign horizon
PFA target
```

Methods with intentionally unmatched information access are marked unmatched and excluded from the primary causal test.

## 14.4 Real exact sign-flip test

Let

$$
n=
\left|
\texttt{randomness.real＿confirmatory＿roots}
\right|.
$$

For the authoritative confirmatory seed sequence, $n=10$. Enumerate all $2^n$ sign assignments; therefore the authoritative grid yields $2^{10}=1024$ assignments.

### Two-sided

$$
p =
\frac{
\left\lvert\lbrace
|\bar d^\ast|
\ge
|\bar d|
\rbrace\right\rvert
}{
2^n
}.
$$

### One-sided positive alternative

$$
p =
\frac{
\left\lvert\lbrace
\bar d^\ast
\ge
\bar d
\rbrace\right\rvert
}{
2^n
}.
$$

Zeros remain zero and are never discarded.

## 14.5 Synthetic sign-flip test

For a synthetic paired sample of $n$ independent seed-level differences, use exact enumeration whenever

$$
2^n
\le
\texttt{statistics.synthetic＿sign＿flip＿replicates＿when＿not＿exact}.
$$

When this condition holds, enumerate all $2^n$ sign assignments exactly using the same one-/two-sided extremeness rule as Section 14.4.

Otherwise let

$$
B=
\texttt{statistics.synthetic＿sign＿flip＿replicates＿when＿not＿exact}.
$$

Generate exactly $B$ deterministic sign assignments from the RNG rooted at `randomness.statistical_analysis_base_seed`. The all-positive observed assignment is included exactly once. The Monte Carlo p-value uses the finite-simulation correction

$$
p =
\frac{
1+
\left\lvert\lbrace\text{simulated statistic as or more extreme}\rbrace\right\rvert
}{
1+B
}.
$$

Zeros remain zero and are never discarded.

## 14.6 BCa bootstrap

Primary paired continuous effects use paired BCa bootstrap with `statistics.bootstrap_replicates` resamples.

The resampling unit is the independent seed.

Method pairing is preserved.

If the bootstrap statistic is exactly degenerate and all finite resamples equal the observed statistic, report the degenerate interval:

$$
[\hat\theta,\hat\theta].
$$

If BCa cannot be evaluated for any other numerical reason, the statistical artifact is Invalid; no silent percentile fallback is allowed.

## 14.7 Hierarchical campaign bootstrap

Secondary descriptive real-data intervals may use:

1. sample campaigns with replacement;
2. sample seed indices with replacement;
3. preserve method pairing inside every selected campaign×seed cell;
4. recompute the aggregate.

These intervals never replace seed-level primary inference.

## 14.8 Hodges-Lehmann paired shift

For paired differences $d_1,\ldots,d_n$, compute every Walsh average

$$
\frac{d_i+d_j}{2},
\qquad i\le j,
$$

and report their median.

## 14.9 Equivalence

Equivalence requires the complete configured confidence interval to lie inside the configured equivalence region.

Nonsignificance is never interpreted as equivalence.

## 14.10 Predeclared directional hypothesis contracts

The primary Holm family contains exactly five one-sided positive-direction hypotheses. Materiality/equivalence gates remain separate from p-value testing.

| Hypothesis identifier | Independent paired seed-level statistic | Null boundary | Positive alternative |
| --- | --- | --- | --- |
| `Self-Explanation Material Attenuation` | `Delta A_self = A_self(inclusive) - A_self(exact)` at the primary self-explanation condition | mean paired difference `<= 0` | mean paired difference `> 0` |
| `Pure-Order Target Drift` | Full FedCampaign-EMHI `D_A` at the primary Pure Continuous Triple condition and primary reference theta | mean `D_A <= 0` | mean `D_A > 0` |
| `Primary ODI Advantage over Order-at-Most-Two EMHI` | `R_ODI,full - R_ODI,<=2` on TON_IoT Network | mean paired difference `<= 0` | mean paired difference `> 0` |
| `Common-Mode False-Campaign Reduction` | native-high-volume stress-window false-declaration rate of Raw Mean Rank Fusion minus Full FedCampaign-EMHI | mean paired difference `<= 0` | mean paired difference `> 0` |
| `Strong-Local ODI above Minimum` | `R_ODI,full,strong-local - claim_materiality.strong_local.minimum_strict_odi_rate` | mean shifted value `<= 0` | mean shifted value `> 0` |

Synthetic hypotheses use the synthetic sign-flip procedure in Section 14.5. Real hypotheses use exact ten-seed sign-flip inference from Section 14.4. The primary multiplicity artifact always contains exactly these five identifiers in this fixed family. When a hypothesis is scientifically Not Tested because its predeclared metric is undefined or its experiment is ineligible, its scientific raw p-value and adjusted p-value are stored as `null`, its scientific decision remains Not Tested, and a separate field `holm_input_p=1.0` is used only to retain the fixed family size during Holm adjustment of the other hypotheses. This value is a conservative multiplicity placeholder, not an imputed scientific test result, and it cannot make the Not Tested hypothesis Supported.

The secondary Holm family contains exactly six one-sided positive-direction ablation contrasts. In every row the statistic is the paired seed-level strict-ODI-rate difference `R_ODI,Full - R_ODI,Comparator` on TON_IoT Network:

```text
Full FedCampaign-EMHI vs Inclusive Context
Full FedCampaign-EMHI vs Leave-One-Out Context
Full FedCampaign-EMHI vs Partial Exclusion
Full FedCampaign-EMHI vs No Purification
Full FedCampaign-EMHI vs Order One
Full FedCampaign-EMHI vs Order at Most Two
```

Both methods in a secondary contrast must have eligible matched finite-horizon operating points for the corresponding seed-level ODI comparison. The secondary multiplicity artifact always contains exactly the six identifiers above. If a contrast is Not Tested, its scientific raw/adjusted p-values are `null` and its separate `holm_input_p` is 1.0 solely for fixed-family Holm bookkeeping; descriptive PFA/detection/coverage outputs remain reportable.

## 14.11 Holm correction

Sort raw p-values ascending.

Ties are ordered lexicographically by hypothesis identifier.

Apply the standard sequential Holm familywise correction.

The adjusted p-value attached to a hypothesis must be reproducible solely from the family artifact.

## 14.12 PFA inference

Candidate threshold selection uses the one-sided Clopper-Pearson UCB.

Held-out PFA reports:

* point estimate;
* one-sided exact 95% UCB.

A method failing the held-out PFA criterion remains a valid scientific result.

It is simply ineligible for a claim requiring matched PFA.

## 14.13 Binary descriptive intervals

Non-PFA binary proportions report two-sided equal-tail 95% Clopper-Pearson intervals.

## 14.14 Primary materiality aggregation

For Primary Strict ODI Evaluation, let

$$
n_s=
\left|
\texttt{randomness.real＿confirmatory＿roots}
\right|.
$$

### ODI rate

$$
\bar R_{ODI} =
\frac1{n_s}
\sum_s
R_{ODI,s}.
$$

### ODI advantage

$$
\frac1{n_s}
\sum_s
\left(
R^{full}_{ODI,s} -
R^{\le2}_{ODI,s}
\right).
$$

### Operational-lead criterion

Pool only campaign×seed cells satisfying strict ODI under Full FedCampaign-EMHI and report their median operational lead.

The inferential unit for method comparison nevertheless remains the seed.

## 14.15 Missing and failed cells

No confirmatory value is imputed.

A valid no-stop is a valid observation.

A valid unfavorable effect is a valid observation.

A scientific operating-point failure is a valid observation.

A technical cell that cannot complete after configured retries is Failed.

A provenance, leakage, schema, or mathematical-invariant violation is Invalid.

Claim-bearing synthesis requires zero missing required confirmatory cells.

---

# 15. Scientific support criteria and downscope rules

## 15.1 Order-3 estimator failure

If the confirmatory order-3 estimator feasibility condition fails:

* Order-Three Scope cannot be Supported;
* order-3 real results remain reportable as executed;
* the manuscript must state the observed feasibility limitation;
* the study may not retroactively increase support thresholds or remove difficult contexts to rescue the claim.

## 15.2 No real calibrated finite-horizon threshold

If Full FedCampaign-EMHI has no eligible primary calibrated finite-horizon threshold:

* Primary Strict ODI Evaluation is still scientifically complete;
* `Strict ODI on TON_IoT Network = Not Supported`;
* no alternative threshold grid is introduced after seeing this outcome.

If the primary order-$\le2$ comparator has no matched operating point:

* the primary ODI superiority comparison is Not Tested;
* full-method absolute ODI/PFA results remain reportable.

## 15.3 Secondary-data ineligibility

If the observed secondary release cannot meet its minimum client or benign-data requirements:

```text
CLAIM contribution does not expand
Secondary Controlled-Trace Generalization = Not Tested
```

No post-hoc dataset replacement is allowed.

## 15.4 Real order-3 null contribution

If pure-order and estimator evidence pass but real order-3 contribution is below the configured material threshold:

```text
Order-Three Scope = Mechanism Only
```

The manuscript may discuss mathematical/controlled order-3 behavior but not a material real order-3 advantage.

---

# 16. Repository and public CLI

The repository structure is fixed as follows:

```text
project/
│
├── README.md                                      # Project overview, environment setup, scientific workflows, and CLI usage.
├── pyproject.toml                                 # Package metadata, dependencies, build settings, Ruff, Pyright, pytest, Import Linter, and tool configuration.
├── uv.lock                                        # Fully locked dependency environment for reproducible installation.
├── noxfile.py                                     # Reproducible quality, typing, testing, build, and validation sessions.
├── Makefile                                       # Short aliases for common development, validation, preprocessing, and experiment workflows.
├── .gitignore                                     # Excludes environments, caches, large outputs, and other generated material from Git.
│
├── configs/
│   ├── fedcampaign-emhi.yaml                      # Single authoritative roadmap-defined production scientific configuration.
│   ├── tests.yml                                  # Reduced configuration values used only by automated tests.
│   └── smoke.yml                                  # Small representative configuration for fast end-to-end smoke execution.
│
├── data/
│   ├── raw -> /external/datasets                  # IMMUTABLE EXTERNAL SYMLINK containing the configured raw dataset releases.
│   └── external_checksums/                        # Roadmap-defined checksum references for validating immutable raw inputs.
│
├── outputs/                                       # Complete generated computational workspace; normally Git-ignored and authoritative for reusable computation.
│   │
│   ├── preprocessing/                             # Dataset-wide products created before scientific experiment execution.
│   │   ├── inventories/                           # Verified raw-file inventories, checksums, release identities, and source discovery records.
│   │   ├── validation/                            # Schema, chronology, eligibility, population, integrity, and leakage-validation artifacts.
│   │   ├── prepared/                              # Canonical deterministic epoch-level datasets ready for scientific computation.
│   │   ├── splits/                                # Detector-fit, nuisance-fit, calibration, held-out, client, campaign, and horizon partitions.
│   │   ├── features/                              # Deterministically constructed and scaled roadmap-defined feature representations.
│   │   └── metadata/                              # Client maps, campaign metadata, preprocessing identities, digests, and reusable preprocessing metadata.
│   │
│   ├── artifacts/                                 # Project-wide computational artifacts reusable across experiments only when scientifically valid.
│   │   ├── models/                                # Reusable fitted local detectors and federated model artifacts.
│   │   ├── scores/                                # Large reusable detector score streams and corresponding metadata.
│   │   ├── fitted/                                # Reusable contexts, projections, rank references, calibrators, and fitted scientific state.
│   │   ├── baselines/                             # Reusable fitted comparator and reference artifacts shared across experiments.
│   │   └── derived/                               # Other reusable derived computational objects and dependency products.
│   │
│   ├── experiments/                               # Experiment-owned computational material separated by descriptive experiment identity.
│   │   └── <descriptive-experiment-name>/
│   │       │
│   │       ├── artifacts/                         # Experiment-specific artifacts that are not scientifically reusable project-wide.
│   │       │   ├── fitted/                        # Experiment-owned estimator, context, projection, comparator, and calibration fits.
│   │       │   ├── predictions/                   # Large score, evidence, trajectory, prediction, or sequential-state streams.
│   │       │   └── derived/                       # Thresholds, support states, calibration products, and other derived experiment arrays.
│   │       │
│   │       ├── evaluations/                       # Raw scientific evaluation products consumed by metrics and statistical analysis.
│   │       │   ├── records/                       # Campaign, benign-horizon, synthetic, stopping-time, coverage, and latency records.
│   │       │   ├── comparisons/                   # Paired method, ablation, equivalence, robustness, and comparator evaluation records.
│   │       │   └── aggregates/                    # Computational aggregates derived from raw evaluation records.
│   │       │
│   │       ├── metrics/                           # Complete experiment metric workspace, including detailed computational evidence.
│   │       │   ├── per_seed/                      # Seed-level metrics preserving the roadmap-defined inferential unit.
│   │       │   ├── per_condition/                 # Metrics for experiment-grid conditions and method comparisons.
│   │       │   └── aggregate/                     # Experiment-level aggregate metrics consumed by statistical analysis and claim evaluation.
│   │       │
│   │       ├── statistics/                        # Complete statistical-analysis workspace including intermediate statistical material.
│   │       │   ├── tests/                         # Raw and adjusted predeclared statistical-test results.
│   │       │   ├── confidence_intervals/          # BCa, Clopper-Pearson, equivalence, and other roadmap-defined interval calculations.
│   │       │   ├── effects/                       # Effect sizes, paired shifts, operational-lead effects, and materiality calculations.
│   │       │   └── multiplicity/                  # Holm-family inputs, ordering, raw p-values, and adjusted inference artifacts.
│   │       │
│   │       ├── checkpoints/                       # Resumable technical state; checkpoints never constitute experiment-completion evidence.
│   │       │   ├── training/                      # Compatible model-training checkpoints for expensive training operations.
│   │       │   └── execution/                     # Checkpoints for other resumable long-running scientific computations.
│   │       │
│   │       ├── diagnostics/                       # Diagnostic material used to validate execution and characterize scientific boundaries.
│   │       │   ├── scientific/                    # Invariant, abstention, coverage, sensitivity, feasibility, and boundary diagnostics.
│   │       │   ├── numerical/                     # Conditioning, fitting failure, non-finite-value, tolerance, and numerical-stability diagnostics.
│   │       │   └── runtime/                       # Timing, CPU, RAM, GPU, VRAM, scalability, and reference-harness telemetry.
│   │       │
│   │       ├── logs/                              # Technical execution logs; logs are never treated as scientific evidence.
│   │       │   ├── execution/                     # Structured progress, reuse decisions, stages, coordinates, statuses, and elapsed-time logs.
│   │       │   └── failures/                      # Crash, retry, resource-exhaustion, and other technical-failure diagnostics.
│   │       │
│   │       └── provenance/                        # Full experiment provenance required for validation, reuse, staleness, and reproducibility.
│   │           ├── configuration/                 # Configuration slices, protocol identities, and deterministic configuration digests.
│   │           ├── data/                          # Dataset, preprocessing, split, client, campaign, and upstream-data identities.
│   │           ├── seeds/                         # Root seeds, deterministic substream identities, and stochastic-process ownership.
│   │           ├── code/                          # Source revision and material code fingerprints affecting scientific artifacts.
│   │           ├── environment/                   # Full software, dependency, hardware, CUDA, and runtime environment capture.
│   │           └── dependencies/                  # Upstream digests, dependency relationships, compatibility, and stale-descendant information.
│   │
│   └── cache/                                     # Non-authoritative recomputable workspace; cached content can never establish scientific validity.
│       ├── preprocessing/                         # Recomputable cache for deterministic raw-to-prepared transformations.
│       ├── models/
│       │   ├── __init__.py
│       │   ├── classical.py
│       │   └── autoencoder.py
│       ├── detection.py
│       ├── emhi/
│       │   ├── __init__.py
│       │   ├── structure.py
│       │   ├── contexts.py
│       │   ├── projection.py
│       │   ├── innovations.py
│       │   ├── calibration.py
│       │   ├── thresholds.py
│       │   ├── evidence.py
│       │   └── sequential.py
│       ├── comparators/
│       │   ├── __init__.py
│       │   ├── contracts.py
│       │   ├── dependence.py
│       │   ├── fusion.py
│       │   ├── sequential.py
│       │   ├── federated.py
│       │   └── runtime.py
│       ├── synthetic/
│       │   ├── __init__.py
│       │   ├── generators.py
│       │   ├── self_explanation.py
│       │   ├── pure_order.py
│       │   ├── feasibility.py
│       │   └── sequential.py
│       ├── experiments/
│       │   ├── __init__.py
│       │   ├── registry.py
│       │   ├── synthetic.py
│       │   ├── campaigns.py
│       │   ├── robustness.py
│       │   └── calibration.py
│       ├── evaluation/
│       │   ├── __init__.py
│       │   ├── records.py
│       │   ├── sequential.py
│       │   ├── metrics.py
│       │   ├── scalability.py
│       │   └── validation.py
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── statistics.py
│       │   └── results.py
│       ├── artifacts/
│       │   ├── __init__.py
│       │   ├── records.py
│       │   ├── storage.py
│       │   └── provenance.py
│       ├── execution/
│       │   ├── __init__.py
│       │   ├── preprocessing.py
│       │   ├── planning.py
│       │   ├── runner.py
│       │   └── status.py
│       ├── runtime.py
│       ├── reporting/
│       │   ├── __init__.py
│       │   ├── evidence.py
│       │   └── export.py
│       └── cli.py
│└── tests/
    ├── conftest.py
    │
    ├── architecture/
    │   ├── test_dependency_boundaries.py
    │   │   — Enforces allowed dependency directions between architectural layers and prevents architectural responsibility violations.
    │   │
    │   ├── test_public_type_boundaries.py
    │   │   — Ensures public, domain, and application APIs use explicit meaningful types rather than loosely typed interfaces or inappropriate raw primitives.
    │   │
    │   ├── test_no_any_dict_object.py
    │   │   — Rejects inappropriate use of Any, object, and anonymous dict-based domain/configuration/artifact payloads, except narrowly justified external-library boundaries.
    │   │
    │   ├── test_no_primitive_leaks.py
    │   │   — Detects inappropriate str/int/float/bool/list/dict primitives crossing domain or architectural boundaries, including primitive public inputs and outputs where meaningful domain types should be used.
    │   │
    │   ├── test_no_hardcoded_values.py
    │   │   — Detects hardcoded scientific, experimental, statistical, dataset, seed, threshold, algorithm, protocol, and other governed values outside their authoritative owner.
    │   │
    │   ├── test_configuration_ownership.py
    │   │   — Ensures configuration values have one authoritative owner and are not repeated or copied into constants, implementation code, CLI defaults, tests, or parallel configuration structures.
    │   │
    │   ├── test_no_duplicate_constants.py
    │   │   — Detects duplicate constants and equivalent independently maintained values across the repository.
    │   │
    │   ├── test_dead_code.py
    │   │   — Detects dead, unused, unreachable, obsolete, and superseded production modules, classes, functions, methods, constants, and other symbols.
    │   │
    │   ├── test_enum_integrity.py
    │   │   — Detects unused enums and ensures authoritative enums are actually used rather than being bypassed by equivalent free-form strings or duplicate identities.
    │   │
    │   ├── test_no_test_only_production_code.py
    │   │   — Detects production code that exists or is referenced only for tests and has no legitimate production use.
    │   │
    │   ├── test_no_redirects_shims_reexports.py
    │   │   — Rejects obsolete redirect modules, compatibility shims, legacy aliases, transitional wrappers, and unnecessary re-export-only modules.
    │   │
    │   ├── test_naming_policy.py
    │   │   — Enforces descriptive names for modules, classes, functions, methods, variables, and parameters; rejects vague, generic, strange, misleading, or unjustifiably short names and abbreviations.
    │   │
    │   ├── test_canonical_vocabulary.py
    │   │   — Enforces canonical project, scientific, algorithm, dataset, policy, experiment, artifact, and architectural terminology and rejects stale aliases, obsolete terminology, opaque names, and artificial version naming.
    │   │
    │   ├── test_no_comments_or_docstrings.py
    │   │   — Rejects Python source comments and module/class/function/method docstrings.
    │   │
    │   ├── test_no_todos_or_temporary_code.py
    │   │   — Rejects TODO, FIXME, HACK, XXX, commented-out implementations, temporary markers, unfinished code residue, and similar development leftovers.
    │   │
    │   ├── test_static_typing.py
    │   │   — Runs repository-wide strict Pyright across production and tests so Pyright/Pylance-visible typing violations fail the test suite.
    │   │
    │   ├── test_code_quality.py
    │   │   — Enforces Ruff formatting and linting so unformatted or lint-invalid Python code cannot remain in the repository.
    │   │
    │   └── test_dependency_hygiene.py
    │       — Enforces dependency hygiene and detects unused, missing, or incorrectly declared dependencies.
    │
    ├── unit/
    │   ├── domain/
    │   ├── config/
    │   ├── datasets/
    │   │   ├── ton_iot_network/
    │   │   └── edge_iiotset/
    │   ├── models/
    │   ├── detection/
    │   ├── emhi/
    │   ├── comparators/
    │   ├── synthetic/
    │   ├── experiments/
    │   ├── evaluation/
    │   ├── analysis/
    │   ├── artifacts/
    │   ├── execution/
    │   ├── runtime/
    │   ├── reporting/
    │   └── cli/
    │
    ├── scientific/
    │   ├── test_data_invariants.py
    │   ├── test_emii_exclusion_invariants.py
    │   ├── test_pure_order_invariants.py
    │   ├── test_projection_and_crossfit_invariants.py
    │   ├── test_sequential_evidence_contracts.py
    │   ├── test_odi_and_campaign_contracts.py
    │   ├── test_experiment_contracts.py
    │   └── test_claim_conditions.py
    │
    ├── integration/
    │   ├── preprocessing/
    │   │   ├── test_ton_iot_network_pipeline.py
    │   │   └── test_edge_iiotset_pipeline.py
    │   ├── detection/
    │   │   └── test_detector_score_policy_pipeline.py
    │   ├── scientific_pipeline/
    │   │   ├── test_emhi_fit_calibrate_evaluate.py
    │   │   ├── test_comparator_pipeline.py
    │   │   └── test_synthetic_validation_pipeline.py
    │   ├── execution/
    │   │   ├── test_artifact_reuse.py
    │   │   ├── test_selective_invalidation.py
    │   │   └── test_checkpoint_recovery.py
    │   ├── reporting/
    │   │   └── test_verified_evidence_materialization.py
    │   └── cli/
    │       └── test_command_ownership.py
    │
    ├── e2e/
    │   ├── test_preprocess_plan_smoke.py
    │   ├── test_run_status_report.py
    │   ├── test_reuse_recovery_and_overwrite.py
    │   └── test_confirmatory_execution.py
    │
    └── smoke/
        └── test_smoke.py
```

The package and directory responsibilities shown in this tree are part of the implementation architecture. Scientific behavior remains governed by the corresponding roadmap contracts; moving a responsibility across these boundaries is not permitted when it would change scientific behavior or artifact ownership.

The only public executable is:

```bash
fedcampaign
```

The complete public interface is:

```text
fedcampaign doctor

fedcampaign preprocess
fedcampaign preprocess <dataset-name>
fedcampaign preprocess --overwrite
fedcampaign preprocess <dataset-name> --overwrite

fedcampaign plan

fedcampaign smoke
fedcampaign smoke --overwrite

fedcampaign run <experiment-name>
fedcampaign run <experiment-name> --overwrite
fedcampaign run <experiment-name> --dry-run

fedcampaign status
fedcampaign status <experiment-name>

fedcampaign report
fedcampaign report <experiment-name>
fedcampaign report <experiment-name> --overwrite
```

The public CLI exposes execution controls only and exposes no scientific-configuration overrides. In particular, there is no public run ID, UUID-style experiment identity, lifecycle-step selector, seed override, method override, coalition-order override, basis/context override, threshold/PFA override, statistical override, or sensitivity override.

Every mutating command follows the same resume rule:

```text
validate required existing artifacts
→ reuse compatible ancestors
→ identify incompatible or incomplete artifacts
→ invalidate only their descendants
→ reconstruct the minimum required subgraph
→ atomically publish completed outputs
```

A command never retrains, rescores, recalibrates, or reanalyzes solely because the same computation is requested by another experiment. Shared artifacts are reused whenever their material dependency fingerprints match.

## 16.1 `doctor`

Read-only. Reports repository/environment readiness; raw dataset inventory and checksums; preprocessing and selected-client eligibility; benign partition and calibrated finite-horizon horizon feasibility; campaign-registry readiness; experiment/dependency status; compatible reusable artifacts; stale artifacts and their first mismatching dependency; affected descendants; confirmatory-cell completeness; and the next valid action. It never modifies artifacts.

Repository commit and full dependency-lock identity are displayed for traceability but are not, by themselves, reasons to mark every artifact stale.

## 16.2 `preprocess`

Without a positional dataset, preprocess every roadmap dataset; with `<dataset-name>`, preprocess only that dataset. It executes the dataset and preprocessing contracts in Sections 6–7, including raw discovery/inventory, canonicalization, deduplication, epoch/features, client eligibility/selection, benign/evaluation separation, benign partitions, campaign registry, discrepancies, hashes, and provenance.

For each requested dataset, the command first validates raw inventory, prepared data, deterministic split/client manifests, benign partitions, and campaign registry separately. Compatible layers are reused. If only a later preprocessing layer is stale, reconstruction starts from the nearest valid prepared ancestor rather than from raw ingestion.

`--overwrite` forces reconstruction of the requested preprocessing artifacts but does not force model training, scoring, analysis, or other downstream work. Downstream artifacts are invalidated only if the newly materialized preprocessing artifact has a different material identity from the artifact it replaces. Recomputing byte-equivalent or materially identical preprocessing must not invalidate compatible descendants.

## 16.3 `plan`

Read-only. Displays experiment order and dependencies, datasets, methods, seed namespaces, outer scientific-cell counts, condition grids, development and confirmatory obligations, blocked/ready cells, reusable artifact coverage, stale descendants, and the nearest valid resume boundary for each incomplete cell.

Expected scientific cells and execution counts are deterministically derived from the experiment registry, execution role, method set, seed sequence, and declared outer execution dimensions; they are never separately configured, manually entered, or guessed.

Default outer-cell granularity is:

```text
experiment × execution role × dataset/generator × independently fitted/scored method × seed × explicit timing repetition
```

An experiment contract may instead declare an immutable within-seed condition bundle. In particular:

* Self-Explanation Exclusion Validation: one seed bundle contains its complete K/order/epsilon/nuisance/context grid;
* Pure-Order Separation Validation: one seed bundle contains all generator/effect/method rows;
* Primary Strict ODI Evaluation: each method×seed is a separate semantic cell;
* Coalition Scalability: client-count×seed×timing-repetition is a separate timing cell after fitted artifacts are prepared.

## 16.4 `smoke`

Executes Synthetic Module Validation. A valid completed smoke result is reused; `--overwrite` reruns the same specification. Smoke reconstruction does not invalidate scientific experiment artifacts unless the smoke rerun reveals a genuine violated invariant in a material component they depend on.

## 16.5 `run`

`run <experiment-name>` resolves the authoritative experiment contract and its artifact dependency subgraph. For every requested cell it:

1. validates mandatory scientific prerequisites;
2. validates reusable prepared data, fitted artifacts, score streams, calibration artifacts, evaluations, and analyses independently;
3. reuses every compatible ancestor, including artifacts first produced for another experiment;
4. identifies the earliest stale or missing artifact on each dependency path;
5. removes stale descendants from active consideration;
6. resumes from the nearest valid artifact or compatible checkpoint;
7. executes only the missing subgraph;
8. computes the predefined metrics and statistics;
9. applies multiplicity, equivalence, and materiality rules;
10. validates scientific invariants and provenance; and
11. atomically publishes completion state.

`--dry-run` is read-only. It validates the requested experiment identity against the
authoritative configuration and reports its material digest and fixed resume sequence,
but never executes cells, creates artifacts, or mutates lifecycle state. It exists for
safe operator and CI validation and cannot alter a scientific setting.

A valid unfavorable scientific result completes successfully. When an experiment has both development and confirmatory cells, the command executes missing development cells first and then executes its missing confirmatory cells as soon as all roadmap-defined prerequisites for those cells are complete. Development outputs may not alter any roadmap-defined scientific value consumed by confirmatory cells. There is no public execution-role selector and no separate second-phase command contract; an interrupted invocation simply resumes its remaining dependency subgraph on the next identical command.

`--overwrite` forces recomputation of artifacts owned by the requested experiment's execution cells at the same semantic locations. It does not force compatible shared prerequisites such as prepared datasets, detector models, or score streams merely because they are consumed by the experiment. If forced recomputation regenerates an artifact with the same material identity, compatible downstream artifacts remain valid; if the material identity changes, only descendants of that artifact are invalidated.

## 16.6 `status`

Read-only. Project mode reports each experiment and its state/progress. Experiment mode reports expected development and confirmatory cells, completed/failed/invalid cells, Operating Point Unavailable outcomes, blocking dependencies, active semantic paths, reusable ancestors, stale artifacts, stale-descendant counts, and the nearest resume point.

## 16.7 `report`

Performs no new scientific computation or statistical analysis. It materializes verified evidence from active machine-readable scientific and statistical artifacts. A claim-bearing experiment is ineligible for claim-state materialization until every mandatory confirmatory cell required by its claim contract is complete and valid.

`--overwrite` replaces the same manuscript export rather than creating another scientific result. Reporting changes, figure cosmetics, table formatting, prose templates, or export-library changes may invalidate report artifacts but must not invalidate evaluation, scoring, fitting, or preprocessing artifacts.

## 16.8 CLI ownership and reuse boundaries

| Command                      | Artifacts it may create or replace                                                                            | Reusable inputs                                                                        | Must not implicitly regenerate                                                 |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `doctor`                     | none                                                                                                          | all active manifests and indexes                                                       | anything                                                                       |
| `preprocess`                 | inventory, prepared data, split/client manifests, benign partitions, campaign registry                        | compatible earlier preprocessing layers                                                | detector models, scores, experiment evaluations, statistics, reports           |
| `plan`                       | none                                                                                                          | manifests, dependency index, experiment registry                                       | anything                                                                       |
| `smoke`                      | smoke validation artifacts                                                                                    | compatible smoke fixtures/results                                                      | real-data scientific artifacts                                                 |
| `run <experiment-name>`      | experiment-owned fits/evaluations/analyses plus missing shared computational artifacts required by the target | any compatible prepared data, models, scores, fits, calibration, evaluations, analyses | compatible shared ancestors                                                    |
| `status`                     | none                                                                                                          | manifests and dependency index                                                         | anything                                                                       |
| `report [<experiment-name>]` | figures, tables, source-data exports, summaries, claim/report manifests                                       | completed evaluation and statistical artifacts                                         | preprocessing, fitting, scoring, calibration, evaluation, statistical analysis |

## 16.9 Operational command sequence

The authoritative sequence is:

```bash
fedcampaign doctor
fedcampaign preprocess
fedcampaign smoke
fedcampaign plan

fedcampaign run self-explanation-exclusion-validation
fedcampaign run pure-order-separation-validation
fedcampaign run exclusion-matched-hofd-equivalence
fedcampaign run strong-comparator-composition-challenge
fedcampaign run estimator-support-and-context-feasibility
fedcampaign run sequential-evidence-validation

fedcampaign run primary-strict-odi-evaluation
fedcampaign run exclusion-mechanism-ablation
fedcampaign run purification-and-order-ablation
fedcampaign run context-and-estimator-sensitivity
fedcampaign run benign-common-mode-robustness
fedcampaign run strong-local-policy-challenge
fedcampaign run secondary-controlled-trace-generalization

fedcampaign run outside-campaign-contamination-boundary
fedcampaign run client-dropout-and-context-sparsity-boundary
fedcampaign run coalition-scalability

fedcampaign doctor
fedcampaign plan
fedcampaign report
```

Each `run` command executes all missing roadmap-required development and confirmatory cells for that experiment in dependency order. If execution is interrupted, the same command resumes from the nearest valid artifact boundary. No experiment is rerun merely to create a second scientific result.

An ineligible secondary trace remains Not Tested; no substitute dataset is selected.

---

# 17. Execution lifecycle, identity, states, caches, and diagnostics

## 17.1 Semantic scientific identity

A scientific execution cell is identified only by:

```text
experiment_name
execution_role
dataset_or_generator
method_or_condition
seed
client_population_role
predeclared outer condition coordinates
```

Timestamps, UUIDs, hashes, attempt numbers, and run IDs never define scientific identity or statistical independence.

Experiment-owned active artifacts are rooted at:

```text
<artifacts.outputs_root>/experiments/<descriptive-experiment-name>/
```

Within that experiment root, each artifact is written only under the architecture-defined `artifacts/`, `evaluations/`, `metrics/`, `statistics/`, `checkpoints/`, `diagnostics/`, `logs/`, or `provenance/` subtree. Scientific-cell coordinates deterministically define filenames and any required nested condition directories within the owning subtree. The same scientific cell always resolves to the same active artifact locations.

Artifact identity is distinct from scientific-cell identity. A reusable artifact has a stable semantic role, a material dependency fingerprint, and a content identity. The same reusable artifact may be consumed by multiple scientific cells without being duplicated under each consumer.

## 17.2 Experiment execution and artifact dependency map

The table below defines the minimum dependency and reuse graph. Experiment contracts in Section 13 remain authoritative for their scientific grids, methods, seeds, metrics, and support criteria.

| Experiment                                   | Material inputs and prerequisites                                                                                                                                                                      | Main produced artifacts                                                                                                                                   | Principal reuse/downstream consumers                                                                                                                            |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Synthetic Module Validation                  | fixed synthetic fixtures; relevant scientific component code/config                                                                                                                                    | exact-fixture validation records and smoke manifest                                                                                                       | execution readiness; no manuscript evidence                                                                                                                     |
| Self-Explanation Exclusion Validation        | self-explanation generators; context variants; EMHI estimator components                                                                                                                               | generator realizations, compatible estimator fits, perturbation metrics, seed summaries, adjusted inference                                               | self-explanation claim, manuscript tables/curves; compatible synthetic estimator artifacts may be reused within the experiment grid                                  |
| Pure-Order Separation Validation             | pure/mixed generators; purity validator; comparator definitions                                                                                                                                        | validated generator realizations, method fits/scores, order-drift metrics, summaries/statistics                                                           | pure-order claim; reusable pure-order reference realizations for comparator challenge where dependency fingerprints match                                       |
| Exclusion-Matched HOFD Equivalence           | configured synthetic support grids; EMHI projection and HOFD definitions                                                                                                                               | paired atom outputs, NRMSE/cosine/stopping-time records, equivalence statistics                                                                           | equivalence claim and required manuscript figures/tables                                                                                                        |
| Strong Comparator Composition Challenge      | declared pure order-2/triple/mixed-order references; synthetic null calibrated finite-horizon horizons; candidate comparator implementations                                                           | candidate error/PFA/runtime records and `strongest-comparator-composition.json`                                                                           | Primary Strict ODI Evaluation, Secondary Controlled-Trace Generalization, downstream baseline registry                                                               |
| Estimator Support and Context Feasibility    | configured synthetic support generators; basis/context/ridge variants                                                                                                                                  | conditional-rank, projection, bias, coverage, abstention, condition-number and failure records; fitted estimator artifacts                                | order-three feasibility criterion; compatible estimator-fit reuse inside repeated metrics/timing only                                                           |
| Sequential Evidence Validation               | signed theorem generator; operational norm path; distributed-support predicate; independent calibrated finite-horizon calibration/held-out null horizons                                               | signed-theorem sequential trajectory records; calibrated finite-horizon threshold-calibration artifacts; held-out PFA records; route validation summaries | mandatory sequential-method validation before claim-bearing real execution                                                                                      |
| Primary Strict ODI Evaluation                | TON_IoT Network prepared data/splits/campaign registry; fixed detector models and score streams; compatible method fits; calibrated finite-horizon calibration; selected strong comparator composition | method×seed campaign evaluations, benign-horizon evaluations, ODI/lead/PFA summaries, statistics                                                          | primary claims; ablations sharing identical method components; strong-local challenge global path; project synthesis                                            |
| Exclusion Mechanism Ablation                 | same TON_IoT Network prepared data, detector models and score streams as primary where definitions match; context-specific alternative fits                                                             | ablation method fits only where required, evaluations, paired summaries/statistics                                                                        | mechanism-ablation evidence; full-EMHI artifacts are reused rather than regenerated                                                                             |
| Purification and Order Ablation              | same TON_IoT Network prepared data/models/scores; full and lower-order compatible fits                                                                                                                  | only missing purification/order-specific fits, evaluations and paired summaries/statistics                                                                | order-3 scope claim; full and order-at-most-two artifacts reuse primary-compatible results when fingerprints match                                              |
| Context and Estimator Sensitivity            | same prepared data/models/scores where applicable; one-factor altered estimator definitions                                                                                                            | sensitivity-specific fits/evaluations/summaries                                                                                                           | development robustness only; cannot replace primary settings                                                                                                    |
| Benign Common-Mode Robustness                | TON_IoT Network held-out benign prepared data; primary compatible models/fits; native windows; configured count-stress transformations                                                                  | native-window reuse records, stress-specific transformed features/scores where required, robustness evaluations/statistics                                | common-mode robustness evidence; unchanged native score streams are reused, transformed-count conditions are rescored only from the first changed feature layer |
| Strong Local Policy Challenge                | Primary Strict ODI Evaluation full-EMHI global evaluations and global stop artifacts; independently calibrated strong-local policy                                                                     | strong-local thresholds/stops, ODI recomputation against unchanged global stops, paired summaries/statistics                                              | strong-local claim; global EMHI fitting/scoring/stopping is not rerun                                                                                           |
| Secondary Controlled-Trace Generalization    | eligible Edge-IIoTset prepared data/splits/campaign registry; detector models/scores; compatible method fits; fixed selected strong comparator composition                                         | secondary-trace evaluations, PFA/ODI summaries/statistics                                                                                                 | controlled-trace generalization evidence and project synthesis                                                                                                  |
| Outside-Campaign Contamination Boundary      | context-dependent triple generator; contamination grid; EMHI estimator/sequential path                                                                                                                 | contamination-specific generator realizations, fits/evaluations, drift/detection/coverage/PFA summaries                                                   | failure-boundary evidence                                                                                                                                       |
| Client Dropout and Context Sparsity Boundary | context-dependent triple generator; client-count/dropout grid                                                                                                                                          | dropout-specific evaluations and coverage/abstention/bias/detection/latency summaries                                                                     | development failure-boundary evidence only                                                                                                                      |
| Coalition Scalability                        | full-sized valid EMHI fitted artifacts for each K/seed; common timing environment for confirmatory timing                                                                                                     | fit-time records, loaded-artifact identities, per-repetition timing traces, latency/RSS/throughput/payload summaries                                      | scalability claim and timing figures; compatible fitted artifacts are reused and fitting time is separately reported                                            |

No experiment name is itself a reason to duplicate an artifact. When two rows above require the same prepared dataset, detector model, score stream, full-EMHI fit, calibrated finite-horizon calibration object, or evaluation record under identical material dependencies, they refer to the same reusable artifact identity.

## 17.3 Material dependency fingerprints

Every reusable artifact has a deterministic material dependency fingerprint:

```text
dependency_fingerprint = SHA256(canonical(material_dependency_record))
```

After payload validation, its stable active identity is:

```text
artifact_identity = SHA256(semantic_role || semantic_coordinates || dependency_fingerprint || canonical(content_hashes))
```

Technical attempt IDs, timestamps, staging locations, and producer commit labels do not enter `artifact_identity`. Recomputing the same semantic artifact from the same material dependencies to the same validated content therefore preserves its identity.

The material dependency record contains only dependencies capable of changing the artifact's scientific or computational value. Depending on artifact type, these include:

* exact upstream artifact content identities;
* the relevant slice of the authoritative scientific configuration;
* dataset/source identities and deterministic split/client/campaign identities;
* preprocessing definition for prepared features;
* model architecture, training rule, model seed, and selected training data for fitted detectors;
* scoring function and score-orientation definition for score streams;
* context, basis, projection, cross-fitting, calibration, threshold, support, or local-policy definitions for downstream fitted artifacts;
* experiment condition coordinates that materially alter the computation;
* analysis method, multiplicity family, bootstrap/permutation settings, and analysis seed for statistical artifacts;
* relevant source-component fingerprints for the code paths that produce the artifact;
* versions of external libraries that materially participate in that computation when version changes can alter the produced value;
* runtime/hardware identity only for artifacts whose scientific quantity is runtime- or hardware-dependent, especially confirmatory timing/scalability evidence.

Relevant source-component fingerprints cover the scientific implementation components transitively executed by the artifact producer. They must not default to hashing the complete repository. The implementation must maintain an auditable mapping from each artifact family to its material code components so that changes to unrelated modules do not cause global invalidation.

The following are recorded for traceability but are not universal invalidators by themselves:

* repository commit hash;
* full dependency-lock hash;
* source files outside the producing artifact's material code path;
* tests that do not alter runtime behavior;
* comments, documentation, formatting, and type-only changes with no runtime effect;
* report templates and figure cosmetics for upstream scientific artifacts;
* log formatting;
* timestamps, attempt numbers, paths, and machine-local cache locations.

A repository commit change invalidates an artifact only when it changes one or more material code-component fingerprints for that artifact. A dependency-lock change invalidates an artifact only when a materially used dependency version or behavior relevant to that artifact changes.

## 17.4 Provenance compatibility, atomic completion, and reuse

A completed artifact is reusable only when:

1. its semantic role matches the requested role;
2. its material dependency fingerprint matches the current target;
3. every declared upstream artifact identity is active and valid;
4. content hashes and schemas verify;
5. scientific invariants for that artifact family pass; and
6. an atomic completion record confirms that publication finished successfully.

Expensive artifacts are written to a staging location first. The producer writes payloads, computes hashes, validates schemas/invariants, and only then atomically publishes the active artifact and its completion record. A crash before atomic publication leaves only staging/partial material, which is never considered reusable scientific output.

Directory existence, a `RUNNING` manifest, a log message, a partially written file, or a payload without its matching completion record is insufficient for reuse.

A required scientific cell is Completed only when its own outputs and all referenced reusable artifacts satisfy these rules; required outputs, metrics, statistics, machine-readable source records, and declared Not Defined values are present; forbidden non-finite values are absent; primary keys are valid; and successful completion is recorded.

## 17.5 Selective invalidation boundaries

Invalidation follows dependency edges, not repository-wide provenance equality.

| Artifact boundary                                                                         | Recompute when these material dependencies change                                                                                                                     | Changes that do not, by themselves, require recomputation                                 |
| ----------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| raw inventory                                                                             | raw file bytes/path identity required by the dataset contract; inventory parsing semantics                                                                            | model, estimator, analysis, report, plotting, unrelated code                              |
| prepared dataset / epoch features                                                         | raw identity; canonicalization/deduplication/feature definitions; epoch/timestamp/hash/scaling rules materially used                                                  | detector architecture; scoring; thresholds; analysis/report code                          |
| split/client/campaign manifests                                                           | prepared data identity; chronological partition, eligibility, client-selection, campaign/warm-up/horizon rules                                                        | detector/model implementation; estimator; reporting                                       |
| fitted local detector/checkpoint                                                          | training split identity; preprocessing/scaling identity; detector family/architecture; optimizer/loss/training rules; model seed; materially used ML-library behavior | scoring-only changes; threshold rules; evaluation metrics; statistics; figures/tables     |
| detector score stream                                                                     | fitted detector identity; scored prepared-data identity; score function/orientation and material numerical dependencies                                               | calibration/threshold logic; campaign metrics; statistics; reporting                      |
| nuisance/context/projection/cross-fit artifact                                            | score or synthetic input identity; coalition/context/basis/projection/cross-fitting definitions; relevant seed and support rules                                      | sequential threshold selection; downstream metrics; reporting                             |
| operational norm/local-policy/calibrated finite-horizon calibration or threshold artifact | upstream scores/fits; calibration split/horizons; calibration/threshold/support/local-policy definitions                                                              | held-out evaluation logic; statistics; figure/table formatting                            |
| campaign or benign-horizon evaluation                                                     | score/evidence streams; thresholds; campaign registry; local/global stopping definitions; evaluation horizon and metric definitions required at this layer            | statistical test implementation; bootstrap/permutation settings; figure/report formatting |
| seed summary / statistical analysis                                                       | completed evaluation/result records; statistical formulas; pairing keys; analysis seeds; multiplicity/equivalence/materiality rules                                   | plotting style; report prose/templates; unrelated experiment code                         |
| figure/table/verified-evidence export                                                     | source analysis identities; figure/table specification; formatting/rendering code                                                                                     | any upstream scientific artifact unless its own dependency changes                        |
| report/project summary                                                                    | verified figure/table/metric/statistical identities; claim-registry/report specification                                                                              | upstream fitting/scoring/evaluation merely because report code changed                    |
| timing/scalability measurements                                                           | loaded fitted-artifact identities; timing harness code; common timing environment/hardware/software fields required by Section 19.3                                   | report-only changes; unrelated scientific modules not executed in the harness             |

When a parent artifact changes material identity, every active descendant whose dependency record references the old parent identity becomes stale. Staleness is propagated transitively. Unrelated siblings and ancestors remain valid.

When a parent is recomputed but its material content identity and dependency fingerprint are unchanged, existing descendants remain compatible and must not be invalidated merely because the parent was produced in a new technical attempt or repository commit.

## 17.6 Experiment and cell states

Experiment-level states are:

```text
Not Started
BLOCKED
READY
RUNNING
Completed
Failed
Invalid
```

Cell-level states are:

```text
PLANNED
RUNNING
Completed
Failed
Invalid
```

Each cell additionally records its immutable `execution_role` as `development`, `confirmatory`, `validation`, or `development_only` according to the experiment contract. Execution role is a semantic coordinate, not a mutable state transition.

Staleness is a compatibility status attached to an artifact or completed cell, not a new scientific outcome. A stale completed cell is excluded from active synthesis until its invalidated dependency path is rebuilt and the cell is revalidated.

Operating Point Unavailable is a scientific result attribute of a valid completed cell, not a technical execution state.

Technical failures such as crashes, out-of-memory conditions, or corrupt temporary files are retried according to the configured retry contract; exhaustion yields Failed. Scientific/provenance violations such as wrong data, leakage, changed fixed client maps, impossible synthetic densities, forbidden non-finite claim-bearing calculations, schema failures, incompatible confirmatory scientific configuration, or failed scientific invariants yield Invalid.

Scientifically null or unfavorable outcomes—including no ODI, no attenuation, insufficient estimator accuracy, excessive latency, comparator superiority, or no calibrated finite-horizon threshold meeting the target—remain valid Completed outcomes when execution and validation are correct.

## 17.7 Failure recovery, repair, overwrite, and descendant cleanup

The mandatory recovery sequence for a requested cell is:

```text
validate active ancestors from oldest to newest
→ keep every compatible ancestor
→ locate the first missing/stale/corrupt artifact on each path
→ mark/remove only stale descendants from active consideration
→ resume from the nearest compatible artifact or checkpoint
→ atomically publish replacements
→ revalidate descendants that can remain compatible
→ execute only descendants that truly became stale
```

A failed experiment never invalidates a previously completed experiment simply because it ran earlier. Only a genuine changed dependency can do so.

A stale, partial, corrupt, failed, or invalid active cell is removed from active scientific consideration. Technical failure history remains only in the experiment-owned `logs/failures/` and provenance records, while the same semantic cell is reconstructed from immutable scientific inputs. Repair does not require `--overwrite`.

Stale descendants must not silently coexist as active artifacts after a parent changes. Before the replacement parent becomes eligible for downstream execution, the dependency index must mark every descendant that references the old parent identity as stale and either move it out of the active namespace or otherwise make it impossible for normal readers/reporting to select it.

`--overwrite` forces recomputation of otherwise valid work inside the command's target ownership boundary. It never changes seeds/configuration, creates duplicate result rows, or creates identities such as `run_2`. It does not recursively overwrite compatible ancestors. Descendants are recomputed only if the overwritten artifact's resulting material identity differs from the previously active one.

Internal technical attempts may carry timestamps or technical IDs only in experiment logs, `outputs/cache/staging/`, or provenance. Staging material never enters active status, statistical synthesis, reporting, or manuscript evidence.

## 17.8 Checkpoints and caches

Long-running fitting may checkpoint internally. A checkpoint is reusable only when its semantic role, upstream identities, scientific configuration slice, model/fitting definition, seed, and material code/dependency fingerprints match the requested continuation. Checkpoint recovery is automatic and is not a public CLI mode.

A later crash after scoring, calibration, evaluation, or analysis must resume from the latest compatible completed artifact at that boundary rather than returning to training.

Caches under `outputs/cache/` are non-authoritative implementation accelerators. Exact material dependency compatibility and integrity are required for reuse; stale caches are recomputed. Caches never define scientific identity, and deleting all caches must not change scientific results.

## 17.9 Logging and dependency index

Logs are diagnostic and must make technical failures diagnosable. They are not scientific evidence and are never parsed to obtain manuscript values. All scientific values come from structured machine-readable artifacts.

The implementation maintains the machine-readable artifact dependency index under `outputs/artifacts/derived/`, containing, for every active reusable artifact:

```text
artifact_semantic_role
artifact_semantic_path
producer_contract
producer_experiment_or_preprocess_scope
producer_cell nullable
dependency_fingerprint
upstream_artifact_identities
content_hashes
completion_record
active_state
stale_reason nullable
downstream_consumers
```

The dependency index is derived from manifests and may be rebuilt from them. It is not a separate scientific source of truth.

---

# 18. Artifacts, provenance, outputs, results, and reporting

## 18.1 Evidence boundary

Artifact roots are configured by `artifacts.outputs_root` and `artifacts.results_root`. `outputs/` is the complete generated computational workspace and the only generated root consumed by later scientific computation. `results/` is terminal compact verified manuscript-facing evidence and is never consumed as scientific input.

No stale, failed, invalid, partial, debug-only, or cache-only artifact may silently become manuscript evidence.

The active output namespace is fixed to the architecture-defined ownership roots:

```text
<artifacts.outputs_root>/
  preprocessing/
    inventories/
    validation/
    prepared/
    splits/
    features/
    metadata/
  artifacts/
    models/
    scores/
    fitted/
    baselines/
    derived/
  experiments/
    <descriptive-experiment-name>/
      artifacts/
        fitted/
        predictions/
        derived/
      evaluations/
        records/
        comparisons/
        aggregates/
      metrics/
        per_seed/
        per_condition/
        aggregate/
      statistics/
        tests/
        confidence_intervals/
        effects/
        multiplicity/
      checkpoints/
        training/
        execution/
      diagnostics/
        scientific/
        numerical/
        runtime/
      logs/
        execution/
        failures/
      provenance/
        configuration/
        data/
        seeds/
        code/
        environment/
        dependencies/
  cache/
    preprocessing/
    models/
    evaluation/
    analysis/
    staging/
```

Project-wide reusable artifacts live only under `<artifacts.outputs_root>/artifacts/` when their scientific identity is genuinely reusable across experiments. Experiment-owned material lives under `<artifacts.outputs_root>/experiments/<descriptive-experiment-name>/`. Dataset-wide preprocessing products live under `<artifacts.outputs_root>/preprocessing/`. Non-authoritative recomputable or atomic-write material lives only under `<artifacts.outputs_root>/cache/`.

The active artifact lifecycle is fixed as Staging → Validated → Active and Atomically Published. Staging occurs under `outputs/cache/staging/`. Only Active and Atomically Published artifacts with valid completion records may be consumed.

The results namespace is fixed to:

```text
<artifacts.results_root>/
  experiments/
    <descriptive-experiment-name>/
      figures/
        main/
        supplementary/
      tables/
        main/
        supplementary/
      metrics/
        primary/
        secondary/
        summary/
      statistics/
        tests/
        confidence_intervals/
        effects/
        multiplicity/
      source_data/
        figures/
        tables/
  project_summary/
    figures/
      main/
      supplementary/
    tables/
      main/
      supplementary/
    metrics/
      primary/
      summary/
    statistics/
      comparisons/
      confidence_intervals/
      effects/
      multiplicity/
    source_data/
      figures/
      tables/
    reproducibility/
      configuration/
      datasets/
      seeds/
      software/
      execution/
```

Cross-experiment evidence is materialized only under `<artifacts.results_root>/project_summary/`. Machine-readable scientific sources remain in verified `outputs/`; compact export trace records live inside the existing results metric, statistical, and reproducibility subtrees.

## 18.2 Artifact ownership and lifecycle

Every reusable artifact has exactly one producer contract even when several experiments consume it. The first command that needs a missing artifact may execute that producer contract; later experiments reuse the same active identity.

| Artifact family                             | Producer contract                          | Typical consumers                                                            | Lifecycle rule                                                    |
| ------------------------------------------- | ------------------------------------------ | ---------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| dataset inventory                           | `preprocess` raw-inventory step            | prepared data, `doctor`, reproducibility export                              | immutable for a raw-content identity                              |
| prepared epoch data                         | `preprocess` canonicalization/feature step | splits, detector fitting, stress transformations                             | shared across all compatible experiments                          |
| split/client/benign-partition manifests     | `preprocess` partition step                | detector fit, calibration, held-out evaluation                               | shared until split semantics or prepared data changes             |
| campaign registry                           | `preprocess` campaign step                 | real campaign evaluation and reporting                                       | shared across all compatible real experiments                     |
| local detector model/checkpoint             | detector-fit producer invoked by `run`     | score generation across primary, ablation, robustness, secondary experiments | fit once per material training identity                           |
| detector score stream                       | scoring producer invoked by `run`          | estimator fitting, calibration, evaluation, ablations                        | score once per model×data×scoring identity                        |
| context/projection/cross-fit fit            | method-fit producer invoked by `run`       | evidence generation, sequential evaluation, scalability                      | reused wherever method/config/input identity matches              |
| threshold/calibration/local-policy artifact | calibration producer invoked by `run`      | benign and campaign evaluation                                               | reused across evaluations with identical calibration dependencies |
| evaluation record                           | evaluation producer invoked by `run`       | summaries and statistical analysis                                           | immutable for its evaluation dependency identity                  |
| seed summary/statistical record             | analysis producer invoked by `run`         | claim registry, tables, figures, project synthesis                           | recomputed only when source evaluations or analysis rules change  |
| figure/table/verified-evidence package      | `report`                                   | manuscript/project summary                                                   | report-only descendant; never an upstream scientific dependency   |

Artifact ownership is by producer contract, not by the first experiment that happens to request the artifact. A manifest still records the requesting/producing experiment cell for traceability.

## 18.3 Dataset and preprocessing provenance

Dataset inventory primary key:

```text
(dataset_name, source_file_path)
```

Required fields:

```text
dataset_name
documented_expected_role
source_file_path
sha256
bytes
record_count nullable
time_start_utc nullable
time_end_utc nullable
observed_structure_status
discrepancy_reason nullable
```

Each preprocessing manifest records at minimum:

```text
dataset_name
dataset_source_identity
preprocessing_semantic_path
preprocessing_hash
dependency_fingerprint
material_code_fingerprints
material_dependency_versions
content_hashes
completion_record
observed_raw_file_count
epoch_seconds
event_hash_bucket_count
derived_feature_dimension
selected_client_ids
detector_fit_start_epoch
detector_fit_end_epoch
nuisance_fit_start_epoch
nuisance_fit_end_epoch
threshold_calibration_start_epoch
threshold_calibration_end_epoch
heldout_start_epoch
heldout_end_epoch
calibration_nonoverlap_horizon_count
heldout_nonoverlap_horizon_count
excluded_record_count
duplicate_record_count
nonfinite_feature_count
ground_truth_discrepancy_count
```

## 18.4 Campaign registry

Primary key:

```text
(dataset_name, start_epoch, end_epoch, participating_clients)
```

Required fields:

```text
dataset_name
start_epoch
end_epoch
duration_epochs
participating_clients
participating_client_count
warmup_epochs
evaluation_horizon_epochs
eligibility_status
ineligibility_reason nullable
integrity_checksum
dependency_fingerprint
completion_record
```

## 18.5 Scientific-cell manifest

Every active cell records:

```text
experiment_name
execution_role
semantic_cell_path
dataset_or_generator
method_name
outer_condition_coordinates
seed
state
authoritative_configuration_hash_trace_only
material_scientific_configuration_hash
dataset_hashes
preprocessing_hash nullable
selected_client_ids
campaign_registry_checksum nullable
upstream_artifact_identities
fitted_artifact_paths
fitted_artifact_hashes
dependency_fingerprint
material_code_fingerprints
material_dependency_versions
producer_code_commit
full_dependency_lock_hash_trace_only
runtime_environment_identity
warnings
abstention_count
numerical_failure_count
runtime_seconds
peak_rss_bytes
application_payload_bytes
mandatory_output_paths
mandatory_output_hashes
completion_record
```

`producer_code_commit` and `full_dependency_lock_hash_trace_only` preserve reproducibility context. Compatibility is determined by the material dependency fingerprint and declared upstream identities, not by requiring global equality of those trace-only fields.

The runtime-environment identity retains the observed Python/OS/CPU/RAM and GPU/driver/CUDA fields where applicable. It participates in validity only for computations whose declared scientific quantity depends on that environment, especially timing/scalability evidence or a dependency whose numerical behavior is proven material. Technical timestamps may be recorded but are not keys.

## 18.6 Scientific result and analysis records

Per-campaign records are keyed by experiment, execution role, dataset, method, seed, campaign interval, and participating clients, and contain at minimum:

```text
global_stop_epoch nullable
local_min_stop_epoch nullable
strict_odi
statistical_lead_epochs nullable
operational_lead_epochs nullable
global_detected_within_horizon
local_detected_within_horizon
decisive_order nullable
context_coverage
abstention_rate
server_latency_seconds
end_to_end_latency_seconds
```

Benign-horizon records are keyed by experiment, execution role, dataset, method, seed, benign split role, and horizon index, and contain threshold, false-campaign status, first stop if any, context coverage, and abstention rate.

Seed-level summaries record experiment/lifecycle-step/dataset/comparison/seed, the compared methods, metric, both values, paired difference, campaign count, source-evaluation identities, dependency fingerprint, and content hash.

Statistical records retain the claim/hypothesis/comparison/metric identity; test or CI/effect-size method; alternative or equivalence margins where applicable; number of independent units; statistic/estimate; raw and Holm-adjusted p-values where applicable; confidence level and bounds where applicable; bootstrap/permutation count where applicable; analysis seed; decision; source-result identities; analysis dependency fingerprint; and content hash. These records must preserve every rule in Section 14.

A statistical-code change invalidates only the statistical records whose material analysis component changed and their report descendants. It does not invalidate the source evaluation records unless evaluation logic also changed.

## 18.7 Figure/table sources and claim registry artifacts

Every manuscript table or figure has exactly one machine-readable source artifact in verified `outputs/`. The source record contains:

```text
source_analysis_hash
report_dependency_fingerprint
confirmatory_execution_manifest_hash nullable
source_scientific_cell_paths
source_artifact_hashes
```

Manuscript figures/tables never read diagnostic logs directly and no console value is manually copied into manuscript evidence. Reporting may export compact selected metrics or statistics into the corresponding `results/experiments/<descriptive-experiment-name>/metrics/` or `statistics/` subtree, but those exports are terminal descendants and never become scientific inputs.

The machine-readable claim registry records, for each claim:

```text
claim_identifier
exact_claim
supporting_experiments
primary_metric
secondary_metrics
statistical_rule
materiality_gate
failure_condition
valid_scope
forbidden_extrapolation
supporting_table
supporting_figure
state
state_reason
source_artifact_hashes
```

The project-level claim registry is materialized as a machine-readable summary artifact under `results/project_summary/metrics/summary/`. It is a reporting descendant of verified outputs and is never consumed by scientific execution.

A reporting or visualization change may regenerate figure/table/metric-summary artifacts without changing the fixed scientific result or analysis identities they cite.

## 18.8 Reporting and reproducibility export

For every eligible completed experiment, `report` writes its manuscript artifacts under `<artifacts.results_root>/experiments/<descriptive-experiment-name>/`. Compact export-trace metadata is stored with that experiment's `metrics/summary/` evidence and traces execution roles, confirmatory-execution manifest hash where applicable, analysis hashes, producer code/dependency trace identities, material dependency fingerprints, dataset/preprocessing hashes, selected clients, campaign-registry checksum, source semantic cells, and source artifact hashes.

Project-wide `report` materializes reproducibility evidence under:

```text
<artifacts.results_root>/project_summary/reproducibility/
  configuration/
  datasets/
  seeds/
  software/
  execution/
```

The exact public CLI sequence, resolved experiment-plan snapshot, semantic-cell index, artifact dependency index, environment/hardware/runtime metadata, and completion/confirmatory execution metadata are stored under `execution/`; dataset checksum, release, preprocessing, and client-map identities under `datasets/`; seed identities under `seeds/`; dependency-lock copy and source-revision identities under `software/`; and the authoritative scientific configuration plus its material configuration digest under `configuration/`. The claim registry is stored as a machine-readable summary artifact under `results/project_summary/metrics/summary/`.

The reproducibility export may contain multiple producer commits when a scientifically unchanged campaign was resumed after implementation fixes. Each scientific artifact remains traceable to the exact code and material dependency fingerprint that produced it; the existence of multiple commits does not imply that unaffected artifacts were recomputed.

---

# 19. Confirmatory execution and synthesis

## 19.1 Execution-role contract

The scientific configuration, experiment grids, claim thresholds, statistical families, and seed sequences are fixed by this roadmap itself. There is no additional scientific state transition that changes those values.

Claim-bearing experiments use independent confirmatory roots so that development roots are not reused as the inferential sample. Development outputs may be used to diagnose implementation defects and verify predeclared prerequisites, but they may not change a configured scientific value, comparator-selection rule, effect grid, metric, claim threshold, statistical direction, or multiplicity family consumed by confirmatory cells.

A confirmatory cell is eligible to execute when:

1. its roadmap-defined validation and experiment prerequisites are Completed and current;
2. every reusable input has a matching material dependency fingerprint;
3. the selected strong comparator identity exists when the experiment consumes it;
4. the relevant raw-data/preprocessing/campaign identities are current for real-data cells;
5. the production configuration validates with no unknown or missing field; and
6. no required upstream cell is Failed, Invalid, or Not Tested in a way that makes the downstream quantity mathematically undefined.

`run` executes eligible confirmatory cells automatically after their development prerequisites in the same experiment contract. The independent confirmatory seed role is part of the cell identity and does not create a second result namespace.

## 19.2 Confirmatory cell obligations

The required confirmatory obligations are exactly:

| Experiment | Confirmatory obligation |
| --- | --- |
| Self-Explanation Exclusion Validation | complete primary inferential condition for every `randomness.synthetic_confirmatory_roots` seed; other grid rows remain development generality diagnostics |
| Pure-Order Separation Validation | complete the predeclared primary condition and required purity/materiality rows for every `randomness.synthetic_confirmatory_roots` seed |
| Exclusion-Matched HOFD Equivalence | complete all primary support levels and orders for every `randomness.synthetic_confirmatory_roots` seed |
| Strong Comparator Composition Challenge | development-only selection; no confirmatory re-selection |
| Estimator Support and Context Feasibility | complete only the primary order-3 feasibility condition for every `randomness.synthetic_confirmatory_roots` seed; sensitivities remain development-only |
| Sequential Evidence Validation | complete both signed-theorem and calibrated finite-horizon routes for every `randomness.synthetic_confirmatory_roots` seed |
| Primary Strict ODI Evaluation | complete every declared method for every `randomness.real_confirmatory_roots` seed on the complete eligible primary campaign registry and held-out benign horizons |
| Exclusion Mechanism Ablation | complete all declared ablation methods for every `randomness.real_confirmatory_roots` seed |
| Purification and Order Ablation | complete all declared methods for every `randomness.real_confirmatory_roots` seed |
| Context and Estimator Sensitivity | development-only |
| Benign Common-Mode Robustness | complete the primary native-high-volume negative branch and positive-power branch for every `randomness.real_confirmatory_roots` seed; count-multiplication stress factors remain reportable robustness rows |
| Strong Local Policy Challenge | complete every `randomness.real_confirmatory_roots` seed |
| Secondary Controlled-Trace Generalization | if dataset-eligible, complete all declared methods for every `randomness.real_confirmatory_roots` seed; otherwise Not Tested |
| Outside-Campaign Contamination Boundary | complete configured fractions for every `randomness.synthetic_confirmatory_roots` seed as confirmatory boundary evidence |
| Client Dropout and Context Sparsity Boundary | development-only |
| Coalition Scalability | complete every K for every `randomness.real_confirmatory_roots` seed under one common timing environment |

A required confirmatory cell tolerance of `runtime.required_confirmatory_missing_cell_tolerance` applies to claim-bearing synthesis. With the authoritative value zero, no required confirmatory cell may be missing. A valid Not Tested outcome caused by a predeclared eligibility rule is not converted into a missing technical cell; its dependent claim follows the explicit Not Tested/downscope rule.

## 19.3 Common reference timing environment

Claim-bearing scalability results are valid only when all confirmatory K cells are measured under one common observed environment identity. No particular hardware model is scientifically privileged, but environment equality is mandatory across the compared K cells.

The timing environment record must contain at minimum:

```text
operating_system
kernel_or_build
machine_architecture
python_version
cpu_model
physical_core_count
logical_core_count
installed_ram_bytes
blas_lapack_vendor
blas_thread_count
openmp_thread_count
pytorch_version
scikit_learn_version
numpy_version
gpu_present
gpu_model nullable
gpu_driver_version nullable
cuda_runtime_version nullable
cudnn_version nullable
power_or_performance_mode_if_exposed nullable
```

Before timing begins, `doctor` records the environment and `run coalition-scalability` verifies exact equality of these fields against the first active confirmatory timing cell. A mismatch makes the affected timing cell Invalid for the cross-K claim; it does not invalidate non-timing scientific artifacts.

Timing uses one concurrent experiment cell, in-process transport, disk-I/O exclusion, the monotonic high-resolution clock, and GPU synchronization rules already defined under Scalability timing configuration. CPU/BLAS/OpenMP thread settings are recorded and must remain constant across K. Background operating-system activity is not claimed to be eliminated; measured repetitions and p95 aggregation quantify the observed reference harness under the recorded environment.

The latency acceptance statement must always name or cite the recorded environment and must remain restricted to reference-harness computation.

## 19.4 Statistical synthesis completeness

Claim-state synthesis reads only current confirmatory statistical/evaluation artifacts and the explicitly permitted development-only selection/diagnostic artifacts named by a claim contract.

Before project claim materialization, the analysis layer verifies:

```text
all mandatory confirmatory cells accounted for
all source artifacts current and provenance-valid
all primary and secondary Holm families complete for their eligible hypotheses
all required BCa and exact-binomial intervals present
all materiality/equivalence gates evaluable or explicitly Not Tested
all claim-state rules from Section 21 evaluated mechanically
no results/ artifact used as computational input
```

A reporting command cannot repair a missing statistical or evaluation artifact. It must stop with a precise missing dependency instead.

---

# 20. Manuscript evidence materialization

## 20.1 Source-data rule

Every manuscript table and figure is generated from a compact machine-readable source-data export beneath the corresponding `results/.../source_data/` subtree. Source-data exports contain only verified rows derived from current `outputs/` artifacts. `report` may select, sort, reshape, label, and round for presentation; it may not recompute a scientific metric, confidence interval, p-value, materiality/equivalence decision, or claim state.

Every source-data file records:

```text
artifact_name
source_artifact_hashes
source_analysis_hash nullable
report_dependency_fingerprint
row_count
column_schema
```

Machine-readable values retain full precision. Display rounding follows `reporting.precision`.

## 20.2 Dataset and evidence roles table

Rows:

```text
controlled generator suite
TON_IoT Network
Edge-IIoTset
```

Columns:

```text
dataset
scientific_role
documented_expected_structure
observed_raw_structure
client_definition
observed_client_count
epoch_seconds
benign_reference_source
campaign_ground_truth
allowed_claims
forbidden_claims
dataset_hash
```

Source: `results/project_summary/source_data/tables/dataset-and-evidence-roles.csv`.

Rendered table: `results/project_summary/tables/main/dataset-and-evidence-roles.csv`.

Observed values are populated from the validated raw/preprocessing manifests rather than literature counts.

## 20.3 Authoritative numerical protocol table

Generated directly from the Authoritative Configuration Contract with:

```text
parameter
authority_type
value
unit
primary_or_sensitivity
scientific_role
```

Source: `results/project_summary/source_data/tables/numerical-protocol.csv`.

Rendered table: `results/project_summary/tables/main/numerical-protocol.csv`.

No manually duplicated numerical registry is maintained elsewhere.

## 20.4 Local detector and policy configuration table

Rows:

```text
Isolation Forest
One-Class SVM
Autoencoder
primary local policy
strong local policy
```

Columns:

```text
method_or_policy
fit_partition
algorithm_or_architecture
fixed_settings
score_orientation
threshold_source
calibration_source
PFA_target
selection_rule
```

Source: `results/project_summary/source_data/tables/local-detector-policy-configuration.csv`.

Rendered table: `results/project_summary/tables/main/local-detector-policy-configuration.csv`.

## 20.5 Baseline fairness contract table

Rows: every method reported from Primary Strict ODI Evaluation plus every publication-critical synthetic comparator.

Columns:

```text
method
information_access
outside_exclusion
maximum_order
proper_subset_purification
collaborative_training
score_calibration_source
sequential_backend
PFA_calibration
matched_status
```

Source: `results/project_summary/source_data/tables/baseline-fairness-contract.csv`.

Rendered table: `results/project_summary/tables/main/baseline-fairness-contract.csv`.

The selected-comparator challenge additionally exports `results/experiments/strong-comparator-composition-challenge/source_data/tables/strong-comparator-selection.csv` and rendered `results/experiments/strong-comparator-composition-challenge/tables/supplementary/strong-comparator-selection.csv` with candidate, native order, eligibility, held-out PFA/UCB, target error, runtime tiebreak value, and selected indicator.

## 20.6 Self-explanation results table

Rows:

```text
client_count
coalition_order
nuisance_family
context_method
```

Columns:

```text
nuisance_derivative
innovation_residual_derivative
atom_derivative_if_applicable
attenuation
paired_primary_effect_if_applicable
95%_CI
Holm_raw_p_if_applicable
Holm_adjusted_p_if_applicable
equivalence_state
```

Source: `results/experiments/self-explanation-exclusion-validation/source_data/tables/self-explanation-results.csv`.

Rendered table: `results/experiments/self-explanation-exclusion-validation/tables/main/self-explanation-results.csv`.

## 20.7 Pure-order and HOFD results table

Rows:

```text
experiment
generator
effect
support_per_context
order
method
```

Columns as applicable:

```text
maximum_proper_subset_drift
target_order_drift
order_specific_stopping_probability
purity_state
projection_or_atom_NRMSE
projection_or_atom_NRMSE_95%_CI
HOFD_cosine_similarity_if_applicable
stopping_time_difference
stopping_time_difference_95%_CI
heldout_PFA
heldout_PFA_95%_upper
Holm_adjusted_p_if_applicable
```

Experiment-local sources and rendered tables are:

```text
results/experiments/pure-order-separation-validation/source_data/tables/pure-order-separation.csv
results/experiments/pure-order-separation-validation/tables/main/pure-order-separation.csv
results/experiments/exclusion-matched-hofd-equivalence/source_data/tables/hofd-equivalence.csv
results/experiments/exclusion-matched-hofd-equivalence/tables/main/hofd-equivalence.csv
```

Project-summary source: `results/project_summary/source_data/tables/pure-order-and-hofd-results.csv`, built only from those current completed experiment exports.

Rendered project-summary table: `results/project_summary/tables/main/pure-order-and-hofd-results.csv`.

## 20.8 Estimator feasibility and sequential validation tables

Estimator table source: `results/experiments/estimator-support-and-context-feasibility/source_data/tables/order-three-feasibility.csv`.

Rendered estimator table: `results/experiments/estimator-support-and-context-feasibility/tables/main/order-three-feasibility.csv`.

Columns:

```text
support_per_context
order
basis_size
context_cell_count
ridge
coverage
projection_NRMSE
standardized_null_bias
numerical_failure_rate
criterion_state
```

Sequential table source: `results/experiments/sequential-evidence-validation/source_data/tables/sequential-validation.csv`.

Rendered sequential table: `results/experiments/sequential-evidence-validation/tables/main/sequential-validation.csv`.

Columns as applicable:

```text
route
seed_role
threshold_semantics
restricted_ARL
restricted_ARL_95%_lower
assumption_check_state
calibration_horizon_count
heldout_horizon_count
heldout_PFA
heldout_PFA_95%_upper
route_state
```

## 20.9 Primary strict-ODI results table

Rows use the exact method order in `experiments.primary_strict_odi_evaluation.methods`.

Columns:

```text
heldout_PFA
heldout_PFA_95%_upper
mean_ODI_success_rate
ODI_rate_95%_CI
campaign_detection_rate
median_global_stop_epoch
median_local_min_stop_epoch
median_statistical_lead
median_operational_lead
context_coverage
abstention_rate
paired_ODI_difference_vs_order_at_most_two
paired_difference_95%_CI
Holm_adjusted_p
matched_status
operating_point_state
```

Source: `results/experiments/primary-strict-odi-evaluation/source_data/tables/primary-strict-odi-results.csv`.

Rendered table: `results/experiments/primary-strict-odi-evaluation/tables/main/primary-strict-odi-results.csv`.

## 20.10 Ablation, robustness, generalization, and boundary tables

### Exclusion and order ablations

Experiment-local sources and rendered tables are:

```text
results/experiments/exclusion-mechanism-ablation/source_data/tables/exclusion-ablation.csv
results/experiments/exclusion-mechanism-ablation/tables/main/exclusion-ablation.csv
results/experiments/purification-and-order-ablation/source_data/tables/purification-order-ablation.csv
results/experiments/purification-and-order-ablation/tables/main/purification-order-ablation.csv
```

Project-summary source: `results/project_summary/source_data/tables/ablation-results.csv`.

Rendered project-summary table: `results/project_summary/tables/main/ablation-results.csv`.

Rows: Full FedCampaign-EMHI plus every predeclared exclusion, purification, and lower-order ablation.

Columns:

```text
experiment
method
heldout_PFA
heldout_PFA_95%_upper
ODI_rate
campaign_detection_rate
operational_lead
context_coverage
paired_ODI_difference_vs_full
Holm_adjusted_p
```

### Context and estimator sensitivity

Source: `results/experiments/context-and-estimator-sensitivity/source_data/tables/context-estimator-sensitivity.csv`.

Rendered table: `results/experiments/context-and-estimator-sensitivity/tables/supplementary/context-estimator-sensitivity.csv`.

Columns:

```text
changed_factor
changed_value
seed
heldout_PFA
campaign_detection_rate
ODI_rate
operational_lead
context_coverage
abstention_rate
numerical_failure_rate
```

### Benign common-mode robustness

Source: `results/experiments/benign-common-mode-robustness/source_data/tables/benign-common-mode-results.csv`.

Rendered table: `results/experiments/benign-common-mode-robustness/tables/main/benign-common-mode-results.csv`.

Columns:

```text
condition
method
false_campaign_rate
common_mode_suppression
campaign_detection_rate
power_loss
context_coverage
Holm_adjusted_p_if_applicable
support_state
```

### Strong-local and secondary controlled trace

Experiment-local sources and rendered tables are:

```text
results/experiments/strong-local-policy-challenge/source_data/tables/strong-local-challenge.csv
results/experiments/strong-local-policy-challenge/tables/main/strong-local-challenge.csv
results/experiments/secondary-controlled-trace-generalization/source_data/tables/secondary-controlled-trace.csv
results/experiments/secondary-controlled-trace-generalization/tables/supplementary/secondary-controlled-trace.csv
```

Project-summary source: `results/project_summary/source_data/tables/generalization-and-strong-local-results.csv`.

Rendered project-summary table: `results/project_summary/tables/main/generalization-and-strong-local-results.csv`.

Rows:

```text
TON_IoT Network primary local policy
TON_IoT Network strong local policy
Edge-IIoTset
```

Columns:

```text
observed_client_count
campaign_count
heldout_PFA
heldout_PFA_95%_upper
ODI_rate
campaign_detection_rate
operational_lead
coverage
claim_state
```

### Failure boundaries and scalability

Experiment-local sources and rendered tables are:

```text
results/experiments/outside-campaign-contamination-boundary/source_data/tables/outside-contamination-boundary.csv
results/experiments/outside-campaign-contamination-boundary/tables/supplementary/outside-contamination-boundary.csv
results/experiments/client-dropout-and-context-sparsity-boundary/source_data/tables/dropout-context-boundary.csv
results/experiments/client-dropout-and-context-sparsity-boundary/tables/supplementary/dropout-context-boundary.csv
results/experiments/coalition-scalability/source_data/tables/scalability.csv
results/experiments/coalition-scalability/tables/main/scalability.csv
```

Project-summary source: `results/project_summary/source_data/tables/failure-boundaries-and-scalability.csv`.

Rendered project-summary table: `results/project_summary/tables/main/failure-boundaries-and-scalability.csv`.

Columns as applicable:

```text
client_count
dropout_fraction
outside_contamination_fraction
coalition_count
coverage
abstention_rate
numerical_failure_rate
campaign_detection_rate
median_server_latency
p95_server_latency
median_reference_harness_latency
p95_reference_harness_latency
peak_RSS
throughput
payload_bytes
timing_operating_point_state
environment_identity
```

## 20.11 Self-explanation derivative curves

* x: perturbation;
* y: nuisance, innovation-residual, or atom mean as identified in the source data;
* group: context method;
* facets: order and nuisance family;
* uncertainty: 95% seed-level CI.

Source: `results/experiments/self-explanation-exclusion-validation/source_data/figures/self-explanation-derivatives.csv`.

Rendered figures: `results/experiments/self-explanation-exclusion-validation/figures/main/self-explanation-derivatives.{pdf,svg,png}`.

## 20.12 Pure-order separation figure

* x: legal generator effect;
* y: standardized drift;
* groups: proper-subset maximum and target order;
* facets: continuous triple, XOR, context-dependent triple;
* reference lines: configured proper-subset and target-order criteria.

Source: `results/experiments/pure-order-separation-validation/source_data/figures/pure-order-drift.csv`.

Rendered figures: `results/experiments/pure-order-separation-validation/figures/main/pure-order-drift.{pdf,svg,png}`.

## 20.13 EMHI-HOFD atom equivalence figures

Primary figure:

* x: benign support per context, log2 scale;
* y: atom NRMSE;
* uncertainty: paired 95% CI;
* reference: configured NRMSE equivalence margin.

A separate figure reports cosine similarity with its configured reference line.

Source: `results/experiments/exclusion-matched-hofd-equivalence/source_data/figures/hofd-equivalence.csv`.

Rendered figures: `results/experiments/exclusion-matched-hofd-equivalence/figures/main/hofd-atom-nrmse.{pdf,svg,png}` and `results/experiments/exclusion-matched-hofd-equivalence/figures/main/hofd-cosine-similarity.{pdf,svg,png}`.

## 20.14 Primary ODI paired seed effects

* x: method;
* y: seed-level ODI rate;
* one point per confirmatory real seed;
* paired lines by seed;
* method ordering: `experiments.primary_strict_odi_evaluation.methods`.

Source: `results/experiments/primary-strict-odi-evaluation/source_data/figures/odi-seed-rates.csv`.

Rendered figures: `results/experiments/primary-strict-odi-evaluation/figures/main/odi-seed-rates.{pdf,svg,png}`.

## 20.15 Operational lead ECDF

Methods:

```text
Full FedCampaign-EMHI
Exclusion-Matched Order-at-Most-Two EMHI
Exclusion-Matched Conditional HOFD
Selected Strong Comparator Composition
```

Include only finite strict-ODI operational-lead values and display the denominator for every method.

Source: `results/experiments/primary-strict-odi-evaluation/source_data/figures/operational-lead-ecdf.csv`.

Rendered figures: `results/experiments/primary-strict-odi-evaluation/figures/main/operational-lead-ecdf.{pdf,svg,png}`.

## 20.16 Benign common-mode robustness figure

* x: benign stress condition;
* y: false-campaign rate;
* groups: configured common-mode methods;
* uncertainty: seed-level interval from existing statistical artifacts.

Source: `results/experiments/benign-common-mode-robustness/source_data/figures/common-mode-pfa.csv`.

Rendered figures: `results/experiments/benign-common-mode-robustness/figures/main/common-mode-pfa.{pdf,svg,png}`.

## 20.17 Outside-contamination boundary figures

Primary figure:

* x: configured outside-contamination fraction;
* y: detection rate.

Separate figure: context coverage on the y-axis.

Source: `results/experiments/outside-campaign-contamination-boundary/source_data/figures/outside-contamination-boundary.csv`.

Rendered figures: `results/experiments/outside-campaign-contamination-boundary/figures/supplementary/outside-contamination-detection.{pdf,svg,png}` and `results/experiments/outside-campaign-contamination-boundary/figures/supplementary/outside-contamination-coverage.{pdf,svg,png}`.

## 20.18 Scalability figures

Primary figure:

* x: client count;
* y: p95 reference-harness latency;
* annotate derived coalition count;
* reference line: configured latency maximum.

Separate figure: peak RSS versus client count.

Source: `results/experiments/coalition-scalability/source_data/figures/scalability.csv`.

Rendered figures: `results/experiments/coalition-scalability/figures/main/scalability-latency.{pdf,svg,png}` and `results/experiments/coalition-scalability/figures/main/scalability-peak-rss.{pdf,svg,png}`.

Manuscript vector figures are generated as PDF and SVG; PNG previews may also be emitted. PDF/SVG values must be sourced from the same source-data export and may not differ numerically.

## 20.19 Project-summary evidence

Project-wide reporting creates:

```text
results/project_summary/tables/main/claim-summary.csv
results/project_summary/tables/main/primary-evidence.csv
results/project_summary/source_data/tables/claim-summary-source.csv
results/project_summary/source_data/tables/primary-evidence-source.csv
results/project_summary/metrics/summary/claim-registry.json
```

`claim-summary.csv` contains exactly one row per Section 21 claim with claim identifier, exact permitted claim, state, state reason, primary metric result, materiality/equivalence result, adjusted p-value where applicable, and supporting table/figure paths.

`primary-evidence.csv` contains only the central claim-bearing quantities required by Section 21 and creates no new aggregate statistic.

The claim registry JSON is the machine-readable authority for manuscript claim state. Manuscript prose may not exceed the exact permitted claim, valid scope, or forbidden-extrapolation boundary recorded there.

---

# 21. Claim and evidence registry

Allowed states:

```text
SUPPORTED
PARTIALLY_SUPPORTED
MECHANISM_ONLY
CONDITIONAL
NULL_RESULT
NOT_SUPPORTED
NOT_TESTED
```

A claim state is computed only from current verified artifacts. A technical/provenance defect blocks the affected result until repaired; it is not converted into a scientific claim state. `NOT_TESTED` is reserved for a predeclared scientific/data eligibility condition that makes required evidence unavailable without changing this roadmap. A valid unfavorable result is retained and receives the state defined below.

| Claim identifier | Exact permitted claim | Mandatory evidence |
| --- | --- | --- |
| `CLAIM_EMII_ADMISSIBLE_INFORMATION` | Coalition $A$ is scored using nuisance information restricted to predictable information generated by $A^c$. | mathematical specification, provenance validator, exact-exclusion implementation tests, exclusion mechanism evidence |
| `CLAIM_SELF_EXPLANATION` | Persistent coalition perturbations may feed back into inclusive or insufficiently excluded nuisance representations, whereas exact complement exclusion removes the direct coalition contribution. | analytic derivative fixture, Self-Explanation Exclusion Validation, primary Holm result |
| `CLAIM_PURE_ORDER_SEPARATION` | There exist nonempty order-$r$ alternative families that preserve every proper-subset distribution while producing nonzero order-$r$ interaction. | generator proof, generator-purity validator, Pure-Order Separation Validation, primary Holm result |
| `CLAIM_SEQUENTIAL_CONSEQUENCE` | When the bounded signed innovation satisfies the declared conditional-null contract, inherited e-detector machinery yields its published average-run-length semantics. | theorem-assumption audit, Signed-Theorem Sequential Route |
| `CLAIM_STRICT_ODI` | On eligible TON_IoT Network campaigns, Full FedCampaign-EMHI exhibits material strict ODI relative to the exclusion-matched order-at-most-two predecessor at independently calibrated matched finite-horizon false-campaign operating points under fixed local policies. | Primary Strict ODI Evaluation, matched PFA evidence, operational lead, primary Holm result |
| `CLAIM_ORDER_THREE_SCOPE` | Order 3 is a scientifically separable and empirically estimable interaction order within the declared support regime and materially contributes to the primary real-data result only when its predeclared real contribution criterion passes. | pure-order evidence, estimator feasibility, purification/order ablation |
| `CLAIM_OPERATIONAL_FEASIBILITY` | At the tested client counts, the complete in-process reference harness satisfies the declared numerical-failure and computational-latency criteria; practical early-warning wording additionally requires positive protocol-adjusted operational lead on the primary trace. | Coalition Scalability, common timing-environment provenance, Primary Strict ODI operational-lead evidence |

The numerical support, materiality, equivalence, PFA, and latency values are those in the Authoritative Configuration Contract and Sections 3, 13–15; this registry does not redefine them.

## 21.1 `CLAIM_EMII_ADMISSIBLE_INFORMATION`

`SUPPORTED` when all of the following are true:

* the Section 4 admissibility specification and exact-complement identity tests pass;
* provenance for every claim-bearing exact-exclusion artifact records context membership exactly equal to the selected-client complement of the coalition;
* no current-epoch target-coalition observation enters exact-exclusion nuisance/context construction;
* the exact-exclusion smoke fixtures pass;
* the real Exclusion Mechanism Ablation is eligible and at least one of the predeclared insufficient-exclusion contrasts shows a positive seed-level ODI advantage for Full FedCampaign-EMHI with its secondary Holm-adjusted p-value below `statistics.nominal_significance_alpha`.

`MECHANISM_ONLY` when the mathematical/provenance/controlled-mechanism requirements pass but either no predeclared real insufficient-exclusion contrast meets that directional operational criterion or the primary real trace is scientifically ineligible under Section 6 and the real exclusion-ablation consequence therefore cannot be evaluated.

`NOT_SUPPORTED` when a valid implementation/theory result contradicts the stated complement restriction.

## 21.2 `CLAIM_SELF_EXPLANATION`

At the primary self-explanation condition, define the exact-exclusion nuisance-derivative equivalence half-width

\[
m=\texttt{claim＿materiality.self＿explanation.exact＿exclusion＿nuisance＿derivative＿equivalence＿fraction＿of＿direct}\,|D_{direct}|.
\]

`SUPPORTED` when:

* the analytic direct-response fixture passes;
* the complete 95% BCa CI for exact-exclusion seed-level $D_\eta$ lies inside $[-m,m]$;
* mean confirmatory $\Delta A_{self}=A_{self,inclusive}-A_{self,exact}$ is at least `claim_materiality.self_explanation.minimum_attenuation_difference`;
* the primary Holm-adjusted `Self-Explanation Material Attenuation` p-value is below `statistics.nominal_significance_alpha`.

`NULL_RESULT` when the experiment is valid and the analytic exact-exclusion identity is not contradicted but the material attenuation criterion and/or directional inference does not pass.

`NOT_SUPPORTED` when the exact-exclusion analytic mechanism is contradicted by a valid controlled implementation, including failure of the exact derivative identity beyond its equivalence region for reasons other than a technical defect.

## 21.3 `CLAIM_PURE_ORDER_SEPARATION`

`SUPPORTED` when, for the primary Pure Continuous Triple condition at `generators.pure_polynomial.primary_reference_theta` over confirmatory synthetic seeds:

* analytic generator-purity invariants pass;
* mean maximum proper-subset standardized drift is no greater than `claim_materiality.pure_order.maximum_proper_subset_standardized_drift`;
* mean target-order standardized drift is at least `claim_materiality.pure_order.minimum_target_order_standardized_drift`;
* the primary Holm-adjusted `Pure-Order Target Drift` p-value is below `statistics.nominal_significance_alpha`.

`MECHANISM_ONLY` when the pure-order conditions above pass but the Section 13.6 order-3 estimator feasibility criterion does not pass; the existence/separation mechanism is retained while practical order-3 use is downscoped.

`NOT_SUPPORTED` when a mathematically valid declared pure-order generator fails the target-order movement criterion or violates the proper-subset invariance criterion after technical defects have been excluded.

Other generator/effect rows remain scope and failure-boundary evidence and cannot replace the primary condition.

## 21.4 `CLAIM_SEQUENTIAL_CONSEQUENCE`

`CONDITIONAL` when:

* every Signed-Theorem Sequential Route assumption check in Section 13.7 passes;
* the implemented e-factor, e-SR recursion, and threshold exactly match Sections 4.11 and 4.17;
* the confirmatory one-sided BCa lower bound for restricted ARL meets `experiments.sequential_evidence_validation.signed_theorem.restricted_arl_bootstrap_lower_bound_minimum_epochs`.

`NOT_SUPPORTED` when a valid controlled execution contradicts a required theorem assumption or the inherited sequential implementation contract.

This roadmap does not provide a theorem-quality real-data conditional-null argument, so the claim cannot be promoted here to an unconditional real-data `SUPPORTED` statement. Empirical benign averages and the separate finite-horizon PFA experiment are insufficient for that promotion.

## 21.5 `CLAIM_STRICT_ODI`

Let the primary paired comparison be Full FedCampaign-EMHI minus Exclusion-Matched Order-at-Most-Two EMHI on `randomness.real_confirmatory_roots`.

`SUPPORTED` only when all are true:

1. both methods have eligible calibrated finite-horizon operating points and held-out PFA one-sided UCB no greater than `evidence.calibrated_finite_horizon.target_pfa`;
2. mean Full FedCampaign-EMHI seed-level strict-ODI rate is at least `claim_materiality.primary_real.minimum_strict_odi_rate`;
3. mean paired ODI-rate advantage is at least `claim_materiality.primary_real.minimum_odi_rate_advantage_over_order_at_most_two`;
4. pooled median operational lead among finite Full FedCampaign-EMHI strict-ODI successes is at least `claim_materiality.primary_real.minimum_median_operational_lead_epochs`;
5. the primary Holm-adjusted `Primary ODI Advantage over Order-at-Most-Two EMHI` p-value is below `statistics.nominal_significance_alpha`.

`PARTIALLY_SUPPORTED` when both methods satisfy the matched held-out PFA requirement and Full FedCampaign-EMHI meets the minimum strict-ODI-rate criterion, but one or more of the paired-advantage, operational-lead, or adjusted-inference criteria does not pass. The manuscript must then state exactly which materiality component did not pass and may not use the full permitted claim wording.

`NULL_RESULT` when both methods satisfy the matched held-out PFA requirement but Full FedCampaign-EMHI mean strict-ODI rate is below `claim_materiality.primary_real.minimum_strict_odi_rate`.

`NOT_SUPPORTED` when Full FedCampaign-EMHI has no eligible calibrated operating point or its held-out PFA UCB exceeds the target.

`NOT_TESTED` when the observed TON_IoT Network release is scientifically ineligible under Section 6 or the primary comparator cannot supply a matched operating point; absolute Full FedCampaign-EMHI results remain reportable when they exist.

## 21.6 `CLAIM_ORDER_THREE_SCOPE`

Define the confirmatory real order-3 contribution as the mean paired difference

\[
\frac{1}{|\mathcal S|}\sum_{s\in\mathcal S}
\left(R_{ODI,full,s}-R_{ODI,\le2,s}\right),
\qquad
\mathcal S=\texttt{randomness.real＿confirmatory＿roots}.
\]

`SUPPORTED` when:

* `CLAIM_PURE_ORDER_SEPARATION` is `SUPPORTED`;
* the Section 13.6 order-3 estimator feasibility criterion passes;
* the real order-3 contribution is at least `claim_materiality.order_three_real.minimum_material_odi_contribution`.

`MECHANISM_ONLY` when controlled pure-order separation and estimator feasibility pass but the valid real contribution is below the configured materiality threshold.

`NOT_SUPPORTED` when pure order-3 separation fails or order-3 estimator feasibility fails.

`NOT_TESTED` when the primary real experiment is scientifically Not Tested in a way that prevents calculating the contribution.

The claim is restricted to order 3; no behavior above `study.maximum_coalition_order` is implied.

## 21.7 `CLAIM_OPERATIONAL_FEASIBILITY`

For every K in `robustness.scalability_client_counts`, compute the pooled numerical-failure rate and the reported p95 reference-harness latency exactly as Section 13.17 defines. Separately use the Primary Strict ODI Evaluation operational-lead metric without recomputing it.

`SUPPORTED` when:

* every required K/confirmatory timing cell is valid under one common Section 19.3 environment identity;
* pooled numerical-failure rate at every K is no greater than `claim_materiality.maximum_pooled_numerical_failure_rate`;
* reported p95 reference-harness latency at every K is no greater than `claim_materiality.reference_harness.p95_latency_maximum_seconds`;
* every K uses valid primary local and global timing operating points rather than timing-only fallbacks;
* the primary pooled median operational lead among finite Full FedCampaign-EMHI strict-ODI successes is at least `claim_materiality.primary_real.minimum_median_operational_lead_epochs`.

`CONDITIONAL` when the numerical-failure and latency criteria pass at every K under one common valid environment but the practical lead requirement is campaign-dependent, below its configured criterion, or one or more K cells require a timing-only local/global operating-point fallback. In that state the manuscript may report the measured computational feasibility within the tested harness, but may not make an unqualified practical early-warning statement.

`NOT_SUPPORTED` when an observed valid K cell exceeds either numerical-failure or latency criterion.

`NOT_TESTED` when a common valid timing environment, a required K cell, or the primary real operational-lead evidence is scientifically unavailable without changing the roadmap.

The claim is restricted to the tested client-count grid and the recorded in-process reference environment. It does not imply real network latency, production-SOC throughput, or universal scalability.

---

# 22. Research grounding

The primary TON_IoT Network acquisition rule is grounded in the IEEE DataPort / UNSW Research "The TON_IoT Datasets" project release (Network flow variant), created by UNSW Canberra Cyber and mirrored on Kaggle. The release documents a Zeek/Bro-generated flow-record schema of approximately 44 features and the `label`/`type` ground-truth columns described in Section 6.2. Those file inventories, feature counts, and record counts are documented expectations only: implementation inventories, hashes, parses, and validates the actual mounted raw bytes and records any discrepancy before preprocessing.

The TON_IoT Network scientific role and expected client/flow/label semantics are additionally grounded in the UNSW Canberra Cyber publications describing the ToN_IoT dataset family. Literature feature counts, client counts, schema summaries, and label-distribution descriptions never override the observed raw release.

The secondary-trace protocol is grounded in the official Edge-IIoTset release documentation on IEEE DataPort, DOI `10.21227/mbc1-1h68`, and the Ferrag et al. (2022) publication. The release identifies the 61-feature selected CSV schema, the `Attack_label`/`Attack_type` ground-truth columns, and the `ip.src_host`/`ip.dst_host`/`frame.time` identity and timestamp fields described in Section 6.3. These define expected semantics; actual files, device identifiers, schemas, timestamps, and usable records remain subject to raw-release validation under Section 6.

The signed sequential claim is intentionally limited to the declared conditional-null setting. Shin, Ramdas, and Rinaldo, *E-detectors: a nonparametric framework for sequential change detection* (arXiv:2203.03532; published in the New England Journal of Statistics in Data Science), establish nonasymptotic average-run-length false-alarm semantics for the e-detector framework. This roadmap therefore separates that controlled theorem route from its independently calibrated 60-epoch operational PFA route.

The exclusion-matched HOFD comparator is grounded in the generalized Hoeffding-Sobol / hierarchical orthogonal functional decomposition literature for dependent inputs. The roadmap's novelty claim remains the exact coalition-exclusion information restriction and its operational consequences, not a new HOFD decomposition.

Connected-information and pair-copula references are grounded respectively in established maximum-entropy connected-correlation methodology and pair-copula/vine constructions. Their concrete implementations are fixed comparator adaptations defined by this roadmap; the study does not claim to reproduce every variant in those literatures.

Deterministic scientific hashing and component-seed derivation use RFC 8785, JSON Canonicalization Scheme (JCS), as specified in the Canonical serialization subsection. Dataset strings are normalized only where the dataset adapter explicitly requires it; JCS itself does not introduce additional Unicode normalization.

---

# 23. Implementation readiness

Implementation may begin only when the production configuration validates, required raw-data inventory checks can execute, the fixed smoke/theory/baseline validators are implementable from this roadmap, and no mandatory scientific or architectural choice remains unspecified.

Dataset facts that depend on the acquired release are resolved by the deterministic raw-validation/adaptation rules in Section 6 rather than by inventing literature-derived constants. A discrepancy between expected documentation and observed raw bytes is surfaced in provenance and handled by the predeclared eligibility or Invalid rules; it is never silently repaired to match an expected count/schema.

A scientifically unfavorable result, unavailable operating point, abstention boundary, or dataset ineligibility is an executable roadmap outcome and must not be treated as an implementation defect. Technical, provenance, leakage, schema, mathematical-invariant, or dependency-fingerprint failures must be repaired before dependent scientific evidence is interpreted.
