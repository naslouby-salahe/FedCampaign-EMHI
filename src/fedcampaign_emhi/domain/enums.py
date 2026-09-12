from enum import IntEnum, StrEnum


class DatasetName(StrEnum):
    TON_IOT_NETWORK = "TON_IoT Network"
    EDGE_IIOTSET = "Edge-IIoTset"


class ExperimentName(StrEnum):
    SYNTHETIC_MODULE_VALIDATION = "synthetic-module-validation"
    SELF_EXPLANATION_EXCLUSION_VALIDATION = "self-explanation-exclusion-validation"
    PURE_ORDER_SEPARATION_VALIDATION = "pure-order-separation-validation"
    EXCLUSION_MATCHED_HOFD_EQUIVALENCE = "exclusion-matched-hofd-equivalence"
    STRONG_COMPARATOR_COMPOSITION_CHALLENGE = "strong-comparator-composition-challenge"
    ESTIMATOR_SUPPORT_AND_CONTEXT_FEASIBILITY = "estimator-support-and-context-feasibility"
    SEQUENTIAL_EVIDENCE_VALIDATION = "sequential-evidence-validation"
    PRIMARY_STRICT_ODI_EVALUATION = "primary-strict-odi-evaluation"
    EXCLUSION_MECHANISM_ABLATION = "exclusion-mechanism-ablation"
    PURIFICATION_AND_ORDER_ABLATION = "purification-and-order-ablation"
    CONTEXT_AND_ESTIMATOR_SENSITIVITY = "context-and-estimator-sensitivity"
    BENIGN_COMMON_MODE_ROBUSTNESS = "benign-common-mode-robustness"
    STRONG_LOCAL_POLICY_CHALLENGE = "strong-local-policy-challenge"
    SECONDARY_CONTROLLED_TRACE_GENERALIZATION = "secondary-controlled-trace-generalization"
    OUTSIDE_CAMPAIGN_CONTAMINATION_BOUNDARY = "outside-campaign-contamination-boundary"
    CLIENT_DROPOUT_AND_CONTEXT_SPARSITY_BOUNDARY = "client-dropout-and-context-sparsity-boundary"
    COALITION_SCALABILITY = "coalition-scalability"


class MethodName(StrEnum):
    FULL_FEDCAMPAIGN_EMHI = "Full FedCampaign-EMHI"
    EXCLUSION_MATCHED_ORDER_ONE_EMHI = "Exclusion-Matched Order-One EMHI"
    EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI = "Exclusion-Matched Order-at-Most-Two EMHI"
    EXCLUSION_MATCHED_CONDITIONAL_HOFD = "Exclusion-Matched Conditional HOFD"
    INCLUSIVE_CONTEXT_FULL_HIERARCHY = "Inclusive-Context Full Hierarchy"
    LEAVE_ONE_OUT_INSUFFICIENT_EXCLUSION = "Leave-One-Out Insufficient Exclusion"
    PARTIAL_COALITION_EXCLUSION = "Partial Coalition Exclusion"
    NO_PROPER_SUBSET_PURIFICATION = "No Proper-Subset Purification"
    NO_OUTSIDE_CONTEXT_FULL_HIERARCHY = "No-Outside-Context Full Hierarchy"
    RAW_MEAN_RANK_FUSION = "Raw Mean Rank Fusion"
    RAW_MAX_RANK_FUSION = "Raw Max Rank Fusion"
    CONDITIONAL_PAIR_DEPENDENCE = "Conditional Pair Dependence"
    EXCLUSION_MATCHED_LANCASTER_TRIPLE = "Exclusion-Matched Lancaster Triple"
    CONNECTED_INFORMATION_REFERENCE = "Connected Information Reference"
    CONDITIONAL_LOG_LINEAR_REFERENCE = "Conditional Log-Linear Reference"
    D_VINE_CONDITIONAL_REFERENCE = "D-Vine Conditional Reference"
    GLOBAL_FACTOR_RESIDUAL_REFERENCE = "Global Factor Residual Reference"
    MULTISTREAM_CUSUM_REFERENCE = "Multistream CUSUM Reference"
    FEDAVG_AUTOENCODER_REFERENCE = "FedAvg Autoencoder Reference"
    SELECTED_STRONG_COMPARATOR_COMPOSITION = "Selected Strong Comparator Composition"


class ContextMethodName(StrEnum):
    INCLUSIVE_CONTEXT = "Inclusive Context"
    LEAVE_ONE_OUT_INSUFFICIENT_EXCLUSION = "Leave-One-Out Insufficient Exclusion"
    PARTIAL_COALITION_EXCLUSION = "Partial Coalition Exclusion"
    EXACT_COALITION_EXCLUSION = "Exact Coalition Exclusion"
    ORACLE_OUTSIDE_LATENT_CONTEXT = "Oracle Outside Latent Context"
    NO_OUTSIDE_CONTEXT = "No Outside Context"
    SHUFFLED_OUTSIDE_CONTEXT = "Shuffled Outside Context"
    LOCAL_HISTORY_ONLY_CONTEXT = "Local-History-Only Context"
    FORCED_NO_ABSTENTION = "Forced No-Abstention"


class GeneratorName(StrEnum):
    PURE_ORDER_ONE = "Pure Order One"
    PURE_ORDER_TWO = "Pure Order Two"
    PURE_CONTINUOUS_TRIPLE = "Pure Continuous Triple"
    XOR_PARITY_TRIPLE = "XOR Parity Triple"
    CONTEXT_DEPENDENT_PURE_TRIPLE = "Context-Dependent Pure Triple"
    MIXED_ORDER_ONE_PLUS_TWO = "Mixed Order One Plus Two"
    MIXED_ORDER_ONE_PLUS_THREE = "Mixed Order One Plus Three"
    MIXED_ORDER_TWO_PLUS_THREE = "Mixed Order Two Plus Three"
    MIXED_ORDER_ONE_PLUS_TWO_PLUS_THREE = "Mixed Order One Plus Two Plus Three"


class NuisanceTransformName(StrEnum):
    LINEAR = "linear"
    TANH = "tanh"
    SOFTPLUS = "softplus"


class DetectorFamily(StrEnum):
    ISOLATION_FOREST = "Isolation Forest"
    ONE_CLASS_SVM = "One-Class SVM"
    AUTOENCODER = "Autoencoder"


class PartitionRole(StrEnum):
    DETECTOR_FIT = "detector_fit"
    NUISANCE_FIT = "nuisance_fit"
    THRESHOLD_AND_POLICY_CALIBRATION = "threshold_and_policy_calibration"
    HELDOUT_BENIGN = "heldout_benign"


class ExecutionRole(StrEnum):
    DEVELOPMENT = "development"
    CONFIRMATORY = "confirmatory"
    VALIDATION = "validation"
    DEVELOPMENT_ONLY = "development_only"


class ExperimentState(StrEnum):
    NOT_STARTED = "Not Started"
    BLOCKED = "BLOCKED"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "Completed"
    FAILED = "Failed"
    INVALID = "Invalid"


class FitStatus(StrEnum):
    FITTED = "FITTED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class PrimaryHolmHypothesis(StrEnum):
    SELF_EXPLANATION_MATERIAL_ATTENUATION = "Self-Explanation Material Attenuation"
    PURE_ORDER_TARGET_DRIFT = "Pure-Order Target Drift"
    PRIMARY_ODI_ADVANTAGE_OVER_ORDER_AT_MOST_TWO_EMHI = (
        "Primary ODI Advantage over Order-at-Most-Two EMHI"
    )
    COMMON_MODE_FALSE_CAMPAIGN_REDUCTION = "Common-Mode False-Campaign Reduction"
    STRONG_LOCAL_ODI_ABOVE_MINIMUM = "Strong-Local ODI above Minimum"


class SecondaryHolmHypothesis(StrEnum):
    FULL_VERSUS_INCLUSIVE_CONTEXT = "Full FedCampaign-EMHI vs Inclusive Context"
    FULL_VERSUS_LEAVE_ONE_OUT_CONTEXT = "Full FedCampaign-EMHI vs Leave-One-Out Context"
    FULL_VERSUS_PARTIAL_EXCLUSION = "Full FedCampaign-EMHI vs Partial Exclusion"
    FULL_VERSUS_NO_PURIFICATION = "Full FedCampaign-EMHI vs No Purification"
    FULL_VERSUS_ORDER_ONE = "Full FedCampaign-EMHI vs Order One"
    FULL_VERSUS_ORDER_AT_MOST_TWO = "Full FedCampaign-EMHI vs Order at Most Two"


class ConfigurationProfile(StrEnum):
    PRODUCTION = "production"
    TESTS = "tests"
    SMOKE = "smoke"


class CommandName(StrEnum):
    DOCTOR = "doctor"
    PREPROCESS = "preprocess"
    PLAN = "plan"
    SMOKE = "smoke"
    RUN = "run"
    STATUS = "status"
    REPORT = "report"


class RepositoryFileName(StrEnum):
    PROJECT_MANIFEST = "pyproject.toml"
    LOCKFILE = "uv.lock"


class ConfigurationFilePath(StrEnum):
    PRODUCTION = "configs/fedcampaign-emhi.yaml"
    TESTS = "configs/tests.yml"
    SMOKE = "configs/smoke.yml"


class PreprocessOrigin(StrEnum):
    REUSE_ALL = "reuse_all"


class ResumeStep(StrEnum):
    VALIDATE_REQUIRED_ARTIFACTS = "validate required existing artifacts"
    REUSE_COMPATIBLE_ANCESTORS = "reuse compatible ancestors"
    IDENTIFY_INCOMPATIBLE_ARTIFACTS = "identify incompatible or incomplete artifacts"
    INVALIDATE_DESCENDANTS = "invalidate only their descendants"
    RECONSTRUCT_MINIMUM_SUBGRAPH = "reconstruct the minimum required subgraph"
    ATOMICALLY_PUBLISH_OUTPUTS = "atomically publish completed outputs"


class SeedCoordinateName(StrEnum):
    ROUND_INDEX = "round_index"
    RESTART_INDEX = "restart_index"
    TRAINING_EPOCH = "training_epoch"
    CLIENT_COUNT = "client-count"
    CLIENT_INDEX = "client-index"
    COALITION_ORDER = "coalition_order"
    SUPPORT_PER_CONTEXT = "support_per_context"
    BASIS_SIZE = "basis_size"
    CONTEXT_CELL_COUNT = "context_cell_count"
    HORIZON = "horizon"


class FederatedConfigKey(StrEnum):
    SERVER_ROUND = "server_round"
    CLIENT_INDEX = "client_index"


class FederatedSeedComponent(StrEnum):
    AUTOENCODER_PARTICIPATION = "fedavg_autoencoder_participation"


class RuntimeStage(StrEnum):
    DETECTION = "detection"


class DerivedConfigurationKey(StrEnum):
    HELDOUT_BENIGN = "heldout_benign"
    MODEL_INPUT_DIMENSION = "model_input_dimension"
    LOCAL_HORIZON_EPOCHS = "local_horizon_epochs"
    HISTOGRAM_EDGES = "histogram_edges"
    SEED_COUNT = "seed_count"
    SYNTHETIC_CAMPAIGN_HORIZON_EPOCHS = "synthetic_campaign_horizon_epochs"
    SYNTHETIC_CAMPAIGN_WARMUP_EPOCHS = "synthetic_campaign_warmup_epochs"
    SIGNED_THEOREM_E_SR_THRESHOLD = "signed_theorem_e_sr_threshold"
    SIGNED_THEOREM_COMPENSATOR = "signed_theorem_compensator"
    MINIMUM_NONOVERLAPPING_HORIZONS_FOR_ZERO_FALSE_STOP = (
        "minimum_nonoverlapping_horizons_for_zero_false_stop"
    )
    EXACT_REAL_SIGN_FLIP_ASSIGNMENT_COUNT = "exact_real_sign_flip_assignment_count"
    PRIMARY_ODI_TABLE_METHOD_ORDER = "primary_odi_table_method_order"
    DERIVED_FEATURE_DIMENSION = "derived_feature_dimension"
    EQUAL_ORDER_WEIGHTS = "equal_order_weights"


class MetricName(StrEnum):
    PRIMARY_ATTENUATION_CONTRAST = "primary_attenuation_contrast"
    TARGET_ORDER_STANDARDIZED_DRIFT = "target_order_standardized_drift"
    ATOM_NRMSE_COSINE_STOPPING_TIME = "atom_nrmse_cosine_stopping_time"
    RESTRICTED_ARL = "restricted_arl"
    STRICT_ODI_RATE = "strict_odi_rate"
    STRONG_LOCAL_STRICT_ODI_RATE = "strong_local_strict_odi_rate"
    FALSE_CAMPAIGN_REDUCTION = "false_campaign_reduction"


class ArtifactMetadataKey(StrEnum):
    COMPARISON = "comparison"
    PRODUCER = "producer"
    IMPLEMENTATION_STATE = "implementation_state"
    SCORING_STATE = "scoring_state"
    METRIC_NAME = "metric_name"
    METHOD_NAME = "method_name"
    HYPOTHESIS_IDENTIFIER = "hypothesis_identifier"
    SCIENTIFIC_OUTCOME = "scientific_outcome"
    REASON = "reason"
    COMPONENT = "component"


class ArtifactProducer(StrEnum):
    PURE_ORDER = "pure-order-artifact"
    CLIENT_DROPOUT_SPARSE_RANKS = "client-dropout-sparsity-filtered-ranks"
    COALITION_SCALABILITY_TIMING_CELL = "coalition-scalability-timing-cell"
    FEDAVG_AUTOENCODER_SCORES = "fedavg-autoencoder-scores"


class ArtifactImplementationState(StrEnum):
    NATIVE_ORDER_SCORE_COMPLETE = "native_order_score_complete"
    EXECUTION_LAYER_GRID = "execution-layer-grid"


class ArtifactScoringState(StrEnum):
    EXECUTION_LAYER_FITTED_GRID = "execution-layer-fitted-grid"


class ScientificOutcome(StrEnum):
    NOT_TESTED = "Not Tested"


class ScientificOutcomeReason(StrEnum):
    NO_ELIGIBLE_RAW_RECORDS = (
        "no eligible raw records were available after deterministic preprocessing"
    )


class ExperimentHypothesis(StrEnum):
    EXCLUSION_MATCHED_HOFD_EQUIVALENCE = "Exclusion-Matched HOFD Equivalence"
    SIGNED_THEOREM_RESTRICTED_ARL = "Signed-Theorem Restricted ARL"


class ResultMethodName(StrEnum):
    EXACT_COMPLEMENT_EXCLUSION = "Exact Complement Exclusion"
    SIGNED_THEOREM_SEQUENTIAL_ROUTE = "Signed-Theorem Sequential Route"


class SyntheticComparison(StrEnum):
    EXCLUSION_MATCHED_HOFD = "paired exclusion-matched EMHI and HOFD atoms and sequential routes"


class AutoencoderSeedComponent(StrEnum):
    BATCH_PERMUTATION = "autoencoder_batch_permutation"


class SelfExplanationSeedComponent(StrEnum):
    LATENT = "latent"
    NOISE = "noise"


class RunOutputColumn(StrEnum):
    ROLE = "role"
    SEED = "seed"
    METHOD = "method"
    STATE = "state"
    RUNTIME_SECONDS = "runtime_seconds"
    PEAK_RSS_BYTES = "peak_rss_bytes"
    DIAGNOSTIC = "diagnostic"


class RuntimeFigureLabel(StrEnum):
    X_AXIS = "execution cell"
    Y_AXIS = "runtime (seconds)"
    TITLE = "Fresh run cell execution evidence"


class ArtifactNamespace(StrEnum):
    OUTPUTS = "outputs"
    RESULTS = "results"


class ArtifactPathSegment(StrEnum):
    OUTPUTS = "outputs"
    PREPROCESSING = "preprocessing"
    INVENTORIES = "inventories"
    VALIDATION = "validation"
    PREPARED = "prepared"
    SPLITS = "splits"
    FEATURES = "features"
    METADATA = "metadata"
    ARTIFACTS = "artifacts"
    SCORES = "scores"
    FITTED = "fitted"
    MODELS = "models"
    BASELINES = "baselines"
    DERIVED = "derived"
    CACHE = "cache"
    EVALUATION = "evaluation"
    ANALYSIS = "analysis"
    STAGING = "staging"
    EXPERIMENTS = "experiments"
    PROJECT_SUMMARY = "project_summary"
    PREDICTIONS = "predictions"
    EVALUATIONS = "evaluations"
    RECORDS = "records"
    COMPARISONS = "comparisons"
    AGGREGATES = "aggregates"
    METRICS = "metrics"
    PER_SEED = "per_seed"
    PER_CONDITION = "per_condition"
    AGGREGATE = "aggregate"
    STATISTICS = "statistics"
    TESTS = "tests"
    CONFIDENCE_INTERVALS = "confidence_intervals"
    EFFECTS = "effects"
    MULTIPLICITY = "multiplicity"
    CHECKPOINTS = "checkpoints"
    TRAINING = "training"
    EXECUTION = "execution"
    DIAGNOSTICS = "diagnostics"
    SCIENTIFIC = "scientific"
    NUMERICAL = "numerical"
    RUNTIME = "runtime"
    LOGS = "logs"
    FAILURES = "failures"
    FIGURES = "figures"
    MAIN = "main"
    SUPPLEMENTARY = "supplementary"
    TABLES = "tables"
    SOURCE_DATA = "source_data"
    PROVENANCE = "provenance"
    CONFIGURATION = "configuration"
    DATA = "data"
    SEEDS = "seeds"
    ENVIRONMENT = "environment"
    DEPENDENCIES = "dependencies"
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUMMARY = "summary"
    REPRODUCIBILITY = "reproducibility"
    DATASETS = "datasets"
    SOFTWARE = "software"
    RAW = "raw"
    SEED_SUMMARIES = "seed-summaries"
    COUNT_STRESS = "count-stress"
    POSITIVE_POWER = "positive-power"
    SENSITIVITY = "sensitivity"


class ArtifactFileSuffix(StrEnum):
    JSON = ".json"
    MANIFEST_JSON = ".manifest.json"
    JSON_GLOB = "*.json"


class KnownArtifactOutputFilename(StrEnum):
    PRIMARY_HOLM = "primary-holm.json"
    SECONDARY_HOLM = "secondary-holm.json"
    RUN_RECORD = "run-record.json"
    CELL_EVIDENCE = "cell-evidence.csv"
    CELL_RUNTIME = "cell-runtime.png"
    RUN_OUTPUT_INDEX = "run-output-index.json"
    SCIENTIFIC_CONFIGURATION = "scientific-configuration.json"
    DATASET_CONFIGURATION = "dataset-configuration.json"
    SEED_CONFIGURATION = "seed-configuration.json"
    SOFTWARE_IDENTITY = "software-identity.json"
    COMPLETED_EXPERIMENTS = "completed-experiments.json"
    ENVIRONMENT_IDENTITY = "environment-identity.json"
    PLAN_SNAPSHOT = "plan-snapshot.json"
    EXPERIMENT_COMPLETION_METADATA = "experiment-completion-metadata.json"
    PREPROCESSING_IDENTITY = "preprocessing-identity.json"
    SYNTHETIC_VALIDATION = "synthetic-validation.json"
    CELL_VALIDATION = "cell-validation.json"
    SELF_EXPLANATION_MATERIAL_ATTENUATION = "self-explanation-material-attenuation.json"
    PURE_ORDER_TARGET_DRIFT = "pure-order-target-drift.json"
    EXCLUSION_MATCHED_HOFD_EQUIVALENCE = "exclusion-matched-hofd-equivalence.json"
    ESTIMATOR_ORDER_THREE_FEASIBILITY = "estimator-order-three-feasibility.json"
    SIGNED_THEOREM_RESTRICTED_ARL = "signed-theorem-restricted-arl.json"
    CALIBRATED_FINITE_HORIZON_PFA = "calibrated-finite-horizon-pfa.json"
    PRIMARY_HOLM_NOT_TESTED = "primary-holm-not-tested.json"
    ORDER_THREE_SCOPE = "order-three-scope.json"
    PRIMARY_STRICT_ODI_SUPPORT = "primary-strict-odi-support.json"
    STRONG_LOCAL_ODI_ABOVE_MINIMUM = "strong-local-odi-above-minimum.json"
    COMMON_MODE_FALSE_CAMPAIGN_REDUCTION = "common-mode-false-campaign-reduction.json"
    TIMING_ENVIRONMENT = "timing-environment.json"
    MEASUREMENT = "measurement.json"
    STRONGEST_COMPARATOR_COMPOSITION = "strongest-comparator-composition.json"
    EVIDENCE_SOURCE = "evidence-source.json"
    SEED_SUMMARY = "seed-summary.csv"
    PAIRED_DIFFERENCES = "paired-differences.png"
    DROPOUT_BOUNDARY_TABLE = "dropout-boundary.csv"
    DROPOUT_BOUNDARY_FIGURE = "dropout-boundary.png"
    COMPARATOR_COMPOSITION_TABLE = "comparator-composition.csv"
    COMPARATOR_COMPOSITION_FIGURE = "comparator-composition-error.png"
    STRONG_LOCAL_ODI_TABLE = "strong-local-odi.csv"
    STRONG_LOCAL_ODI_FIGURE = "strong-local-odi.png"
    SENSITIVITY_SUMMARY = "sensitivity-summary.csv"
    SENSITIVITY_DETECTION = "sensitivity-detection.png"
    SCALABILITY_SUMMARY = "scalability-summary.csv"


class ArtifactIdentityKind(StrEnum):
    PREPROCESS = "preprocess"
    DETECTOR_SCORES = "detector-scores"
    MARGINAL_RANKS = "marginal-ranks"
    EMHI_FIT = "emhi-fit"


class ArtifactFilenamePattern(StrEnum):
    SEEDED_JSON = "seed-{seed}.json"
    SEEDED_MARGINAL_RANKS_JSON = "seed-{seed}-marginal-ranks.json"
    SEEDED_DIRECTORY = "seed-{seed}"
    METHOD_JSON = "{method}.json"
    CELL_ROLE_METHOD_SEED = "cell-{role}-{method}-seed-{seed}.json"
    WORKER_ROLE_METHOD_SEED = "worker-{role}-{method}-seed-{seed}.json"
    PREPROCESS_LAYER_MANIFEST = "{dataset}-{layer}-manifest.json"
    DATASET_JSON = "{dataset}.json"
    BENIGN_PARTITIONS = "{dataset}-benign-partitions.json"
    CAMPAIGN_REGISTRY = "{dataset}-campaign-registry.json"
    HYPOTHESIS_JSON = "{hypothesis}.json"
    METHOD_METRIC_JSON = "{method}-{metric}.json"
    COALITION_ORDER_MEMBERS = "order-{order}-{members}.json"
    FACTOR_SEED = "factor-{factor}/seed-{seed}.json"
    SCALABILITY_SEED = "k-{client_count}-seed-{seed}.json"
    SCALABILITY_CLIENT_COUNT = "k-{client_count}.json"
    SCALABILITY_CELL = "cell-confirmatory-k-{client_count}-seed-{seed}.json"
    SENSITIVITY_DIAGNOSTIC = "seed-{seed}/{slug}.json"
    SENSITIVITY_CELL = "cell-{slug}-seed-{seed}.json"


class OverwritePolicy(StrEnum):
    REUSE_COMPATIBLE = "reuse_compatible"
    OVERWRITE = "overwrite"


class PreprocessingLayer(StrEnum):
    INVENTORY = "inventory"
    PREPARED = "prepared"
    SPLITS = "splits"
    PARTITIONS = "partitions"
    CAMPAIGN_REGISTRY = "campaign_registry"


class DownstreamArtifactKind(StrEnum):
    DETECTOR_MODELS = "detector models"
    SCORES = "scores"
    EXPERIMENT_EVALUATIONS = "experiment evaluations"
    STATISTICS = "statistics"
    REPORTS = "reports"


class ArtifactLifecycleState(StrEnum):
    MISSING = "missing"
    VALID = "valid"
    STALE = "stale"
    MALFORMED = "malformed"
    INCOMPLETE = "incomplete"
    FAILED = "failed"
    BLOCKED = "blocked"


class RecordExclusionReason(StrEnum):
    UNPARSEABLE_TIMESTAMP = "unparseable_timestamp"
    UNUSABLE_HOST_IDENTITY = "unusable_host_identity"
    STRUCTURALLY_INVALID_EVENT = "structurally_invalid_event"
    MISSING_FIELD_VALUE = "missing_field_value"


class GroundTruthClass(StrEnum):
    BENIGN = "benign"
    MALICIOUS = "malicious"
    AMBIGUOUS = "ambiguous"


class CoalitionOrder(IntEnum):
    ONE = 1
    TWO = 2
    THREE = 3


class SignFlipDirection(IntEnum):
    NEGATIVE = -1
    POSITIVE = 1


class LatentMarkovState(IntEnum):
    NEGATIVE = -1
    POSITIVE = 1


class DetectorFamilyRemainder(IntEnum):
    ISOLATION_FOREST = 0
    ONE_CLASS_SVM = 1
    AUTOENCODER = 2
