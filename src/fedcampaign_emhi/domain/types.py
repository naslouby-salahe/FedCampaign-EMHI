import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from pydantic import Field, StringConstraints

from fedcampaign_emhi.domain.enums import (
    ArtifactNamespace,
    CoalitionOrder,
    ContextMethodName,
    DatasetName,
    DetectorFamily,
    ExperimentState,
    GroundTruthClass,
    PreprocessingLayer,
    RecordExclusionReason,
)

NonNegativeInt = Annotated[int, Field(ge=0)]
PositiveInt = Annotated[int, Field(gt=0)]
NonNegativeFloat = Annotated[float, Field(ge=0.0)]
PositiveFloat = Annotated[float, Field(gt=0.0, allow_inf_nan=False)]
UnitInterval = Annotated[float, Field(ge=0.0, le=1.0)]
OpenUnitInterval = Annotated[float, Field(gt=0.0, lt=1.0)]
FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]
SignedInt = Annotated[int, Field()]

EpochCount = NonNegativeInt
PositiveEpochCount = PositiveInt
EpochSeconds = PositiveInt
UnixTimestampSeconds = FiniteFloat
EpochIndexValue = SignedInt
ClientCount = PositiveInt
ClientIndex = NonNegativeInt
SeedValue = NonNegativeInt
SeedCount = NonNegativeInt
SignFlipAssignmentCount = PositiveInt
FoldCount = PositiveInt
BinCount = PositiveInt
CellCount = PositiveInt
BasisSize = PositiveInt
RidgePenalty = NonNegativeFloat
NumericalTolerance = PositiveFloat
NumericalFloor = PositiveFloat
ConditionNumberLimit = PositiveFloat
Quantile = UnitInterval
Probability = UnitInterval
ConfidenceLevel = OpenUnitInterval
FalseAlarmRate = OpenUnitInterval
LearningRate = PositiveFloat
BatchSize = PositiveInt
TreeCount = PositiveInt
SampleCap = PositiveInt
WorkerCount = PositiveInt
MemoryMib = PositiveInt
SolverIterationLimit = SignedInt
FeatureFraction = UnitInterval
LayerWidth = PositiveInt
FeatureDimension = PositiveInt
DecimalPlaces = NonNegativeInt
BootstrapReplicateCount = PositiveInt
RetryCount = NonNegativeInt
MissingCellTolerance = NonNegativeInt
CoalitionCount = NonNegativeInt
DesignColumnCount = PositiveInt
TensorDimension = PositiveInt
RecordCount = NonNegativeInt
HashBucketCount = PositiveInt
HashBucketIndex = NonNegativeInt
PermutationIndex = NonNegativeInt
BinaryClassLabel = Annotated[int, Field(ge=0, le=1)]
OdiIndicator = Annotated[int, Field(ge=0, le=1)]
GlobalDetectionIndicator = Annotated[int, Field(ge=0, le=1)]
BinIndex = NonNegativeInt
ScientificChoiceCount = NonNegativeInt
DeterministicUtf8Bytes = Annotated[bytes, Field()]
FigureBytes = Annotated[bytes, Field()]
Boolean = Annotated[bool, Field()]
ResumeStep = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
YamlKeyPath = Annotated[str, StringConstraints(min_length=1)]
ScoreShift = FiniteFloat
Correlation = Annotated[float, Field(ge=-1.0, le=1.0)]
LatentAutoregressiveCoefficient = UnitInterval
StandardDeviation = PositiveFloat
EffectCoefficient = FiniteFloat
InteractionStrength = UnitInterval
RankValue = UnitInterval
EvidenceFactor = NonNegativeFloat
ThresholdValue = PositiveFloat
LatencySeconds = NonNegativeFloat
RuntimeSeconds = NonNegativeFloat
CompensatorValue = NonNegativeFloat
GlobalEvidenceState = NonNegativeFloat
ESrThreshold = PositiveFloat
GramConditionNumber = NonNegativeFloat
Percentile = UnitInterval
MinimumNonoverlappingHorizonCount = PositiveInt
KmeansInitializationCount = PositiveInt
KmeansFitRowLimit = PositiveInt
EvidenceClipBound = PositiveFloat
BettingLambda = PositiveFloat
RequiredExceedanceCount = PositiveInt
FactorRank = PositiveInt
FederatedRoundCount = PositiveInt
SvmCoefficientZero = FiniteFloat
AutoencoderBeta = UnitInterval
WeightDecay = FiniteFloat
FiniteHorizonCalibrationCount = PositiveInt
FiniteHorizonHeldoutNullCount = PositiveInt
PureOrderEvaluationSampleCount = PositiveInt
HofdEquivalenceSampleCount = PositiveInt
EstimatorEvaluationSampleCount = PositiveInt
ClientLoading = FiniteFloat
MixedOrderTermIndex = PositiveInt
JeffreysPseudocount = PositiveFloat
IpfIterationLimit = PositiveInt
CusumDriftSubtraction = PositiveFloat
CusumInitialState = FiniteFloat
AttenuationDifference = FiniteFloat
StandardizedDrift = FiniteFloat
ProjectionNrmse = FiniteFloat
StandardizedNullBias = FiniteFloat
CosineSimilarity = UnitInterval
StoppingTimeDifferenceEpochs = FiniteFloat
OdiRateAdvantage = FiniteFloat
OperationalLeadEpochs = FiniteFloat
DetectionRateLoss = FiniteFloat
MaterialOdiContribution = FiniteFloat
EstimatorSupportLevel = PositiveInt
RobustnessCountMultiplier = PositiveFloat
TrajectoryCount = PositiveInt
ScalabilityRepetitionCount = PositiveInt
ConcurrentExperimentCellCount = PositiveInt
EvidenceStatistic = FiniteFloat
StandardizedAtomCoordinate = FiniteFloat
OperationalNormReference = FiniteFloat
SignedDirectionCoordinate = FiniteFloat
CusumIncrement = FiniteFloat
CusumState = NonNegativeFloat
CusumScore = NonNegativeFloat
ModelParameter = FiniteFloat
LatentState = FiniteFloat
DetectorScore = FiniteFloat
FractionalClientCount = NonNegativeFloat
FeatureValue = FiniteFloat
AnomalyScore = FiniteFloat
XavierGain = PositiveFloat
StandardizedError = FiniteFloat
PairedDifference = FiniteFloat
StatisticValue = FiniteFloat
BootstrapBiasCorrection = FiniteFloat
BootstrapAcceleration = FiniteFloat
EquivalenceBoundary = FiniteFloat
NuisanceCoefficient = FiniteFloat
InnovationCoordinate = FiniteFloat
InnovationMean = FiniteFloat
InnovationDeviation = FiniteFloat
CommonModeSuppression = FiniteFloat
BasisCoordinate = FiniteFloat
ProjectionMeanSquaredError = FiniteFloat
GaussianCoordinate = FiniteFloat
HistogramBinMass = UnitInterval
KmeansInertia = NonNegativeFloat
MetricRate = FiniteFloat
Attenuation = FiniteFloat
LogEvidenceGrowth = FiniteFloat
EvidenceShare = FiniteFloat
StoppingTimeDifference = FiniteFloat
RankEstimationError = FiniteFloat
ThroughputPerSecond = PositiveFloat
RestrictedAverageRunLength = FiniteFloat
SignedTheoremCoordinate = FiniteFloat
ContextCoverage = UnitInterval
PolynomialDensity = FiniteFloat
XorInteractionStrength = UnitInterval
StressBucketCount = NonNegativeFloat
ProbabilityMass = UnitInterval
DependenceMoment = FiniteFloat
LogDensity = FiniteFloat
NonconformityScore = NonNegativeFloat
SingularValue = NonNegativeFloat

ClientId = Annotated[
    str,
    StringConstraints(min_length=1, max_length=128, strip_whitespace=True),
]
RelativePath = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
ArtifactFilename = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=128,
        strip_whitespace=True,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
    ),
]
ConfigurationDigest = Annotated[
    str,
    StringConstraints(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$"),
]
MaterialDependencyFingerprint = ConfigurationDigest
OwnershipStatement = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
ConfigSourcePath = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
ComponentName = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
NormalizedEventToken = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
AttackTypeName = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
SeedCoordinateName = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
ArtifactIdentity = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
ByteCount = NonNegativeInt
Sha256Hex = ConfigurationDigest
ThirtyTwoBitSeed = Annotated[int, Field(ge=0, lt=4_294_967_296)]
LoopbackPortNumber = Annotated[int, Field(ge=1, le=65_535)]


@dataclass(frozen=True)
class DetectorFamilyAssignment:
    client_id: ClientId
    zero_based_index: ClientIndex
    family: DetectorFamily


@dataclass(frozen=True)
class EpochIndex:
    unix_timestamp_seconds: UnixTimestampSeconds
    epoch_seconds: EpochSeconds
    index: EpochIndexValue


@dataclass(frozen=True)
class StrictOdiOutcome:
    global_stop_epoch: EpochIndexValue | None
    earliest_local_stop_epoch: EpochIndexValue | None
    indicator: OdiIndicator
    global_detection_indicator: GlobalDetectionIndicator


@dataclass(frozen=True)
class ArtifactRoots:
    outputs_root: Path
    results_root: Path

    def namespace_root(self, namespace: ArtifactNamespace) -> Path:
        if namespace is ArtifactNamespace.OUTPUTS:
            return self.outputs_root
        return self.results_root


@dataclass(frozen=True)
class ChronologicalPartitionLengths:
    detector_fit: EpochCount
    nuisance_fit: EpochCount
    threshold_and_policy_calibration: EpochCount
    heldout_benign: EpochCount


@dataclass(frozen=True)
class RetainedEvent:
    dataset_name: DatasetName
    client_id: ClientId
    timestamp_seconds: UnixTimestampSeconds
    event_type: NormalizedEventToken
    payload: NormalizedEventToken
    unique_identifier: NormalizedEventToken | None
    original_order: RecordCount


@dataclass(frozen=True)
class DeduplicationOutcome:
    retained_events: tuple[RetainedEvent, ...]
    duplicate_count: RecordCount
    experiment_state: ExperimentState


@dataclass(frozen=True)
class EpochFeatureVector:
    log1p_bucket_counts: tuple[FiniteFloat, ...]
    total_raw_event_count: RecordCount
    shannon_entropy: FiniteFloat


@dataclass(frozen=True)
class RobustScaler:
    median: FiniteFloat
    iqr: FiniteFloat
    iqr_floor: NumericalFloor


@dataclass(frozen=True)
class ChronologicalBenignPartitions:
    detector_fit: tuple[EpochIndexValue, ...]
    nuisance_fit: tuple[EpochIndexValue, ...]
    threshold_and_policy_calibration: tuple[EpochIndexValue, ...]
    heldout_benign: tuple[EpochIndexValue, ...]


@dataclass(frozen=True)
class BenignHorizon:
    start_epoch: EpochIndexValue
    epoch_indexes: tuple[EpochIndexValue, ...]


@dataclass(frozen=True)
class LocalPolicyArtifact:
    threshold: ThresholdValue
    required_exceedances: RequiredExceedanceCount
    window_epochs: EpochCount


@dataclass(frozen=True)
class PreprocessingLayerDecision:
    dataset_name: DatasetName
    layer: PreprocessingLayer
    reused: Boolean
    reconstructed: Boolean
    previous_fingerprint: MaterialDependencyFingerprint | None
    current_fingerprint: MaterialDependencyFingerprint
    invalidated_descendant_ids: tuple[ArtifactIdentity, ...]


@dataclass(frozen=True)
class PreprocessExecutionRecord:
    decisions: tuple[PreprocessingLayerDecision, ...]
    requested_datasets: tuple[DatasetName, ...]
    reconstruct_from: tuple[tuple[DatasetName, PreprocessingLayer | None], ...]


@dataclass(frozen=True)
class SeedCoordinate:
    name: SeedCoordinateName
    scalar: FiniteFloat | SeedValue | NormalizedEventToken | Boolean | None


@dataclass(frozen=True)
class SeedDerivationIdentity:
    base_seed: SeedValue
    component_name: ComponentName
    dataset: DatasetName | None
    client_ids: tuple[ClientId, ...]
    coalition_ids: tuple[ClientId, ...]
    condition_coordinates: tuple[SeedCoordinate, ...]


@dataclass(frozen=True)
class ArtifactDependencyNode:
    artifact_id: ArtifactIdentity
    material_fingerprint: MaterialDependencyFingerprint
    upstream_ids: tuple[ArtifactIdentity, ...]


@dataclass(frozen=True)
class CoalitionMembers:
    client_ids: tuple[ClientId, ...]
    order: CoalitionOrder


@dataclass(frozen=True)
class RankReference:
    scores: tuple[FiniteFloat, ...]


@dataclass(frozen=True)
class EdgeIiotsetFlowRecord:
    timestamp_seconds: UnixTimestampSeconds
    source_host: ClientId
    protocol_group: NormalizedEventToken
    binary_label: BinaryClassLabel
    attack_type: AttackTypeName


@dataclass(frozen=True)
class GroundTruthLabel:
    classification: GroundTruthClass
    attack_type: AttackTypeName | None
    is_ambiguous: Boolean


@dataclass(frozen=True)
class ExcludedRecord:
    reason: RecordExclusionReason


@dataclass(frozen=True)
class FileInventoryEntry:
    relative_path: RelativePath
    sha256: Sha256Hex
    byte_count: ByteCount


@dataclass(frozen=True)
class ClientEligibilityRecord:
    client_id: ClientId
    benign_event_count: RecordCount
    benign_nonempty_epoch_count: EpochCount
    is_eligible: Boolean


@dataclass(frozen=True)
class PrimaryClientSelection:
    selected_client_ids: tuple[ClientId, ...]
    eligible_client_ids: tuple[ClientId, ...]
    eligibility: tuple[ClientEligibilityRecord, ...]
    has_sufficient_clients: Boolean


@dataclass(frozen=True)
class ClientBenignTally:
    client_id: ClientId
    benign_event_count: RecordCount
    observed_epoch_indexes: tuple[EpochIndexValue, ...]


@dataclass(frozen=True)
class SecondaryClientSelection:
    selected_client_ids: tuple[ClientId, ...]
    eligible_client_ids: tuple[ClientId, ...]
    eligibility: tuple[ClientEligibilityRecord, ...]
    has_sufficient_clients: Boolean


@dataclass(frozen=True)
class ContextClusterIdentity:
    dataset: DatasetName
    coalition_order: CoalitionOrder
    context_method: ContextMethodName
    experiment_seed: SeedValue | None


@dataclass(frozen=True)
class ContextTrainingRow:
    dataset: DatasetName
    coalition_order: CoalitionOrder
    coalition_client_ids: tuple[ClientId, ...]
    epoch_index: EpochIndexValue
    histogram: tuple[FiniteFloat, ...]


@dataclass(frozen=True)
class OutsideContextHistogram:
    bin_mass: tuple[FiniteFloat, ...]
    available_client_ids: tuple[ClientId, ...]
    abstained: Boolean


@dataclass(frozen=True)
class ContextCentroids:
    identity: ContextClusterIdentity
    centroids: tuple[tuple[FiniteFloat, ...], ...]


@dataclass(frozen=True)
class CrossFittedInnovationCalibration:
    held_fold_innovations: tuple[tuple[FiniteFloat, ...], ...]
    coordinate_means: tuple[FiniteFloat, ...]
    coordinate_deviations: tuple[FiniteFloat, ...]
    standardized_held_fold_innovations: tuple[tuple[FiniteFloat, ...], ...]
    complete_nuisance_coefficients: tuple[tuple[FiniteFloat, ...], ...]
    selected_ridge_penalty: RidgePenalty


MetricValue = FiniteFloat
CensoredPlotEpoch = PositiveEpochCount


def deterministic_registry_payload(
    registry_entry: "CampaignRegistryEntry",
) -> DeterministicUtf8Bytes:
    fields = (
        registry_entry.dataset.value,
        str(registry_entry.start_epoch),
        str(registry_entry.end_epoch),
        ",".join(registry_entry.sorted_participating_client_ids),
    )
    return "\n".join(fields).encode("utf-8")


def registry_entry_integrity_checksum(
    registry_entry: "CampaignRegistryEntry",
) -> Sha256Hex:
    return hashlib.sha256(deterministic_registry_payload(registry_entry)).hexdigest()


@dataclass(frozen=True)
class ClientMaliciousEpochs:
    client_id: ClientId
    malicious_epochs: tuple[EpochIndexValue, ...]


@dataclass(frozen=True)
class CampaignRegistryEntry:
    dataset: DatasetName
    start_epoch: EpochIndexValue
    end_epoch: EpochIndexValue
    sorted_participating_client_ids: tuple[ClientId, ...]

    @property
    def duration_epochs(self) -> EpochCount:
        return self.end_epoch - self.start_epoch + 1

    @property
    def integrity_checksum(self) -> Sha256Hex:
        return registry_entry_integrity_checksum(self)
