from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from pydantic import Field, StringConstraints

from fedcampaign_emhi.domain.enums import (
    ArtifactNamespace,
    ClaimIdentifier,
    ClaimState,
    CoalitionOrder,
    DetectorFamily,
    ExperimentName,
    ExperimentState,
    MethodName,
    OperatingPointState,
    ScientificOutcomeKind,
)

NonNegativeInt = Annotated[int, Field(ge=0)]
PositiveInt = Annotated[int, Field(gt=0)]
NonNegativeFloat = Annotated[float, Field(ge=0.0)]
PositiveFloat = Annotated[float, Field(gt=0.0)]
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
OdiIndicator = Annotated[int, Field(ge=0, le=1)]
BinIndex = NonNegativeInt
ScientificChoiceCount = NonNegativeInt
CanonicalUtf8Bytes = Annotated[bytes, Field()]
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
ESrThreshold = PositiveFloat
GramConditionNumber = NonNegativeFloat
Percentile = UnitInterval

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
ModuleName = Annotated[
    str,
    StringConstraints(
        min_length=1,
        strip_whitespace=True,
        pattern=r"^fedcampaign_emhi(\.[A-Za-z_][A-Za-z0-9_]*)+$",
    ),
]
OwnershipStatement = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
ConfigSourcePath = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]


@dataclass(frozen=True)
class ModuleContract:
    module_name: ModuleName
    ownership: OwnershipStatement


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


@dataclass(frozen=True)
class ScientificOutcome:
    kind: ScientificOutcomeKind
    operating_point_state: OperatingPointState
    experiment_state: ExperimentState
    is_implementation_error: bool


@dataclass(frozen=True)
class ClaimEvaluation:
    identifier: ClaimIdentifier
    state: ClaimState


@dataclass(frozen=True)
class ArtifactRoots:
    outputs_root: Path
    results_root: Path

    def namespace_root(self, namespace: ArtifactNamespace) -> Path:
        if namespace is ArtifactNamespace.OUTPUTS:
            return self.outputs_root
        return self.results_root


@dataclass(frozen=True)
class ExperimentIdentity:
    experiment_name: ExperimentName
    descriptive_slug: ArtifactFilename


@dataclass(frozen=True)
class MethodIdentity:
    method_name: MethodName


@dataclass(frozen=True)
class ProperSubsetDesignShape:
    coalition_order: CoalitionOrder
    basis_size: BasisSize
    tensor_dimension: TensorDimension
    design_column_count: DesignColumnCount


@dataclass(frozen=True)
class ChronologicalPartitionLengths:
    detector_fit: EpochCount
    nuisance_fit: EpochCount
    threshold_and_policy_calibration: EpochCount
    heldout_benign: EpochCount
