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


class EvidencePath(StrEnum):
    SIGNED_THEOREM = "signed_theorem"
    OPERATIONAL_NORM = "operational_norm"


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


class CellState(StrEnum):
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    COMPLETED = "Completed"
    FAILED = "Failed"
    INVALID = "Invalid"


class OperatingPointState(StrEnum):
    AVAILABLE = "Available"
    UNAVAILABLE = "Operating Point Unavailable"


class ClaimState(StrEnum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    MECHANISM_ONLY = "MECHANISM_ONLY"
    CONDITIONAL = "CONDITIONAL"
    NULL_RESULT = "NULL_RESULT"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    NOT_TESTED = "NOT_TESTED"


class ScientificOutcomeKind(StrEnum):
    COMPLETED_UNFAVORABLE = "Completed"
    OPERATING_POINT_UNAVAILABLE = "Operating Point Unavailable"
    NOT_TESTED = "Not Tested"
    FAILED_TECHNICAL = "Failed"
    INVALID_PROVENANCE = "Invalid"


class ClaimIdentifier(StrEnum):
    CLAIM_EMII_ADMISSIBLE_INFORMATION = "CLAIM_EMII_ADMISSIBLE_INFORMATION"
    CLAIM_SELF_EXPLANATION = "CLAIM_SELF_EXPLANATION"
    CLAIM_PURE_ORDER_SEPARATION = "CLAIM_PURE_ORDER_SEPARATION"
    CLAIM_SEQUENTIAL_CONSEQUENCE = "CLAIM_SEQUENTIAL_CONSEQUENCE"
    CLAIM_STRICT_ODI = "CLAIM_STRICT_ODI"
    CLAIM_ORDER_THREE_SCOPE = "CLAIM_ORDER_THREE_SCOPE"
    CLAIM_OPERATIONAL_FEASIBILITY = "CLAIM_OPERATIONAL_FEASIBILITY"


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


class ArtifactNamespace(StrEnum):
    OUTPUTS = "outputs"
    RESULTS = "results"


class ExperimentalUnitKind(StrEnum):
    GENERATOR_ROOT_SEED = "generator_root_seed"
    ALGORITHM_ROOT_SEED = "algorithm_root_seed"


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


class DuplicateResolution(StrEnum):
    RETAIN_FIRST_CHRONOLOGICAL = "retain_first_chronological"


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


class DetectorFamilyRemainder(IntEnum):
    ISOLATION_FOREST = 0
    ONE_CLASS_SVM = 1
    AUTOENCODER = 2
