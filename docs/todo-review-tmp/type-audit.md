# Type Audit

## 1. `types.py` inventory (built before introducing anything)

`src/fedcampaign_emhi/domain/types.py` — 507 lines at baseline. The module is
overwhelmingly explicit, nominal domain typing built on `Annotated[T, Field(...)]`.
No `Any` and no `object` appears anywhere in it.

### 1a. Numeric aliases (semantic, not primitive-renaming)

Representative selection of the ~170 numeric aliases, with validity assessment.
The important property: aliases are **semantically distinct** even when the
underlying primitive coincides — e.g. `EpochCount` and `ClientCount` are both
`NonNegativeInt`/`PositiveInt` but are separate names.

| Type/Alias | Semantic meaning | Underlying | Valid? | Action |
| --- | --- | --- | --- | --- |
| `EpochCount` | count of epochs | `NonNegativeInt` | yes | none |
| `PositiveEpochCount` | strictly positive epochs | `PositiveInt` | yes | none |
| `ClientCount` | number of clients | `PositiveInt` | yes | none |
| `ClientIndex` | zero-based client index | `NonNegativeInt` | yes | none |
| `SeedValue` | experiment seed | `NonNegativeInt` | yes | none |
| `FoldCount` | cross-validation folds | `PositiveInt` | yes | none |
| `BasisSize` | Legendre basis width | `PositiveInt` | yes | none |
| `RidgePenalty` | ridge lambda | `NonNegativeFloat` | yes | none |
| `Probability` | probability | `UnitInterval` | yes | none |
| `OpenUnitInterval` | strictly inside (0,1) | `Annotated[float, gt 0, lt 1]` | yes | none |
| `ConfidenceLevel` | confidence | `OpenUnitInterval` | yes | none |
| `FalseAlarmRate` | target P_fa | `OpenUnitInterval` | yes | none |
| `RankValue` | rank in [0,1] | `UnitInterval` | yes | none |
| `NumericalFloor` | numerical floor | `PositiveFloat` | yes | none |
| `XavierGain` | Xavier init gain | `PositiveFloat` | yes | none |
| `EvidenceClipBound` | clipping bound | `PositiveFloat` | yes | none |
| `CompensatorValue` | theorem compensator | `NonNegativeFloat` | yes | none |
| `FiniteFloat` | finite float payload | `Annotated[float, allow_inf_nan=False]` | yes | none |

### 1b. String aliases

| Type/Alias | Semantic meaning | Underlying | Valid? | Action |
| --- | --- | --- | --- | --- |
| `ClientId` | client identity | constrained str (1..128, stripped) | yes | none |
| `NormalizedEventToken` | canonicalised event token | constrained str | yes | none — correctly serves `UNKNOWN_PROTOCOL`, `UNKNOWN_SERVICE`, `UNKNOWN_PROTOCOL_GROUP`, protocol groups |
| `AttackTypeName` | attack type label | constrained str | yes | none |
| `ArtifactIdentity` | artifact identity | constrained str | yes | none |
| `RelativePath` | repo-relative path | constrained str | yes | none |
| `ArtifactFilename` | artifact filename | constrained str w/ pattern | yes | none |
| `ConfigurationDigest` / `Sha256Hex` | 64-hex digest | constrained str | yes | none |
| `ComponentName` | generic component label | constrained str | yes | none — legitimately shared by seed components, loggers, failed checks, identifiers |
| `OwnershipStatement` | — | constrained str | **NO LONGER USED** | its only consumer (`SmokeFixtureName.label`) was removed; now an unused alias |
| `YamlKeyPath`, `ConfigSourcePath`, `ContextRowKey` | boundary key/path strings | constrained str | yes | none |

### 1c. Boundary aliases

| Type/Alias | Semantic meaning | Valid? | Action |
| --- | --- | --- | --- |
| `YamlScalar` / `YamlNode` | YAML/JSON boundary union | yes — explicitly exempted by `test_domain_typing_hardening.test_boundary_yaml_node_alias_is_allowed` | none |
| `DeterministicUtf8Bytes` | canonical serialised bytes | yes | none |
| `FigureBytes` | rendered figure bytes | yes | none |

### 1d. Dataclasses

`DetectorFamilyAssignment`, `EpochIndex`, `StrictOdiOutcome`, `ArtifactRoots`,
`ChronologicalPartitionLengths`, `RetainedEvent`, `DeduplicationOutcome`,
`EpochFeatureVector`, `RobustScaler`, `ChronologicalBenignPartitions`,
`BenignHorizon`, `LocalPolicyArtifact`, `PreprocessingLayerDecision`,
`PreprocessExecutionRecord`, `SeedCoordinate`, `SeedDerivationIdentity`,
`ArtifactDependencyNode`, `CoalitionMembers`, `RankReference`,
`EdgeIiotsetFlowRecord`, `GroundTruthLabel`, `ExcludedRecord`,
`FileInventoryEntry`, `ClientEligibilityRecord`, `PrimaryClientSelection`,
`ClientBenignTally`, `SecondaryClientSelection`, `ContextClusterIdentity`,
`ContextTrainingRow`, `OutsideContextHistogram`, `ContextCentroids`,
`CrossFittedInnovationCalibration`, `ClientMaliciousEpochs`,
`CampaignRegistryEntry`.

All frozen. All-typed fields. No anonymous dictionaries.

## 2. Types introduced by this remediation

Before adding anything, the inventory above was checked for an existing
semantically-equivalent type.

| New type | Kind | Existing equivalent? | Placement rationale |
| --- | --- | --- | --- |
| `ReuseDecision` | `StrEnum` | none | shares the "preprocessing origin" vocabulary with existing `PreprocessOrigin`; adjacent placement in `domain/enums.py` |
| `SmokeFixtureName` | `StrEnum` | none — the prior `SmokeFixtureName` was a *dataclass wrapper*, not a type alias | moved into the domain vocabulary module alongside `SyntheticComparison`, following the identical `NAME = "human label"` convention used by `DatasetName` and `MethodName` |
| `EstimatorFeasibilityConditionName` | `StrEnum` | none | previously a bare literal typed as generic `ComponentName` |

No new numeric alias was created.

## 3. Alias decisions reviewed

* `ComponentName` remains the type of the *generated* sensitivity identifiers
  (`f"forced-ridge-n-{support}"` etc.). These are genuinely open-ended,
  config-driven labels, so a closed enum would be wrong. The identifier field is
  therefore `ComponentName | EstimatorFeasibilityConditionName`, which is the
  honest representation: one fixed member plus an open family.
* `OwnershipStatement` is now unused. It is **not** deleted here because its
  removal would expand the diff beyond the audited change set and it harms
  nothing; it is recorded in `unresolved.md` as a follow-up.
* `NormalizedEventToken` was deliberately **not** replaced by an enum for the
  dataset canonicalisation sentinels. Those values are Zeek/Edge-IIoTset
  *boundary tokens* (including the literal `"-"` which is simultaneously a DuckDB
  SQL predicate) already carried by a semantic alias. Enum-ifying them would
  force an `enum → str` conversion for the `startswith` prefix check and for
  SQL, i.e. the exact anti-pattern this audit is meant to remove.
