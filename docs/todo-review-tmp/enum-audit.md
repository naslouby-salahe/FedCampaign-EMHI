# Enum Audit

## 1. Existing enums inventoried before creating any new one

`src/fedcampaign_emhi/domain/enums.py` — 526 lines at baseline, ~60 enum classes.
Grouped by family:

* **Identity/name domains**: `DatasetName`, `ExperimentName`, `MethodName`,
  `ContextMethodName`, `GeneratorName`, `DetectorFamily`, `NuisanceTransformName`,
  `PartitionRole`, `ExecutionRole`, `ExperimentState`, `FitStatus`,
  `ArtifactProducer`, `ResultMethodName`, `ExperimentHypothesis`
* **Hypotheses**: `PrimaryHolmHypothesis`, `SecondaryHolmHypothesis`
* **Configuration vocabulary**: `ConfigurationProfile`, `CommandName`,
  `RepositoryFileName`, `ConfigurationFilePath`, `PreprocessOrigin`, `ResumeStep`,
  `SeedCoordinateName`, `FederatedConfigKey`, `FederatedSeedComponent`,
  `RuntimeStage`, `DerivedConfigurationKey`, `MetricName`, `OverwritePolicy`,
  `PreprocessingLayer`, `ArtifactLifecycleState`, `DownstreamArtifactKind`
* **Artifact layout**: `ArtifactNamespace`, `ArtifactPathSegment`,
  `ArtifactFileSuffix`, `KnownArtifactOutputFilename`, `ArtifactIdentityKind`,
  `ArtifactFilenamePattern`, `ArtifactMetadataKey`, `ArtifactImplementationState`,
  `ArtifactScoringState`
* **Scientific outcome/status**: `ScientificOutcome`, `ScientificOutcomeReason`,
  `SyntheticComparison`, `RunOutputColumn`, `RuntimeFigureLabel`,
  `GroundTruthClass`, `RecordExclusionReason`
* **IntEnums**: `CoalitionOrder`, `SignFlipDirection`, `LatentMarkovState`,
  `DetectorFamilyRemainder`
* **Seed components**: `AutoencoderSeedComponent`, `SelfExplanationSeedComponent`

## 2. Classification of every string domain touched

| Domain | Sites | Classification | Decision |
| --- | --- | --- | --- |
| `"reconstructed"` / `"reused"` | `execution/preprocessing.py:289` (only literal) | **CLOSED_DOMAIN** | → `ReuseDecision` |
| `"primary-order-three"` | `synthetic/feasibility.py:106`, `experiments/synthetic.py:1144` | **CLOSED_DOMAIN** (single fixed member; siblings are config-driven `f"..."` labels) | → `EstimatorFeasibilityConditionName` |
| 33 smoke fixture labels | `evaluation/validation.py` | **CLOSED_DOMAIN** (AST-proven all 33 `args[0]` are `ast.Constant` str; zero f-strings, variables, comprehensions) | → `SmokeFixtureName` |
| `UNKNOWN_PROTOCOL`, `UNKNOWN_SERVICE`, `-`, `UNKNOWN_PROTOCOL_GROUP`, `PROTOCOL::…` | both `canonicalization.py` modules | **EXTERNAL_SERIALIZATION / BOUNDARY TOKEN** | keep; typed `NormalizedEventToken` |
| `("arp.", "http.", "tcp.", …)` | `datasets/edge_iiotset/canonicalization.py:6` | **EXTERNAL_SERIALIZATION** — vendored column-name prefixes; task explicitly names the Zeek prefix convention verbatim | keep; not a closed enum |
| `UNKNOWN_NORMALIZED_EVENT_TYPE` | same module | **EXTERNAL_SERIALIZATION** (composed token) + asserted as a literal in `test_edge_iiotset_contract.py:88-89` | keep |
| `("", "-", "0", "0.0", "0.0.0.0")` | same module | **FREE_TEXT / EXTERNAL_SERIALIZATION** value set | keep |
| `"resume_sequence="` | `cli.py:35` | **USER-FACING OUTPUT** prefix | keep |
| `"fedcampaign_emhi"` | `runtime.py:84` | **IDENTIFIER** — Python logging namespace | keep |
| `"reused"` / `"rebuilt"` in log format literals | `experiments/seed_materialization.py`, `experiments/seed_evaluation.py` | **FREE_TEXT log labels**, embedded in `%`-format strings, not compared | keep (see unresolved) |
| `"reconstructed"/"reused"` vocabulary duplication | CLI says `reused`/`rebuilt`; log said `reconstructed`/`reused` | naming inconsistency | CLI echo keys left unchanged to preserve stdout contract |

## 3. New enums created

```python
class ReuseDecision(StrEnum):
    RECONSTRUCTED = "reconstructed"
    REUSED = "reused"

class SmokeFixtureName(StrEnum):            # 33 members, values byte-identical to the removed labels
    MIDRANK_TIES = "midrank ties"
    ...

class EstimatorFeasibilityConditionName(StrEnum):
    PRIMARY_ORDER_THREE = "primary-order-three"
```

Enum-value naming follows the repository's established convention
(`DatasetName.TON_IOT_NETWORK = "TON_IoT Network"`,
`MethodName.FULL_FEDCAMPAIGN_EMHI = "Full FedCampaign-EMHI"`): member name is a
SCREAMING_SNAKE derivation, value is the human-readable label.

## 4. Propagation through the whole workflow (no `.value` round-trips)

### ReuseDecision

```
_execute_dataset  ->  reconstructed: Boolean (local)
                  ->  ReuseDecision.RECONSTRUCTED / .REUSED     (domain value)
_preprocessing_logger().info(..., decision.reuse_decision.value)  (boundary: log format)
cli.py            ->  if decision.reuse_decision is ReuseDecision.REUSED   (identity compare, no string)
```

`reused`/`reconstructed` booleans were **removed from the dataclass**, so no
caller can regress to a bool. No `str(...)`, no `ReuseDecision(x)` parsing inside
the workflow.

### EstimatorFeasibilityConditionName

```
feasibility_conditions          ->  EstimatorFeasibilityConditionName.PRIMARY_ORDER_THREE
experiments/synthetic.py:1144   ->  is EstimatorFeasibilityConditionName.PRIMARY_ORDER_THREE
JSON payload (synthetic.py:1164)->  identifier serialised by rfc8785/json as its string value
seed derivation                 ->  rfc8785.dumps byte-identical  (proven)
```

Comparison changed from `== "<literal>"` to `is <enum member>`.

### SmokeFixtureName

```
FixtureCollector.record / _check / SmokeValidationResult   ->  SmokeFixtureName       (domain value)
synthetic_execution.py diagnostic payload                  ->  fixture.value          (boundary: JSON)
```

The intermediate `# TODO`-marked constants were removed, so the domain value is
named once, in `domain/enums.py`.

## 5. Serialization boundaries (unchanged, all correct)

| Boundary | Mechanism |
| --- | --- |
| CLI stdout | `typer.echo(... .value)` in `cli.py` |
| Structured logging | `%s` format args using `.value` |
| JSON/checkpoint payloads | `fixture.value` in `synthetic_execution.py` |
| RFC 8785 canonical JSON (seeds/digests) | `rfc8785.dumps` handles `StrEnum` identically to `str` |
| YAML | `config/validation.py` `YamlNode` |

## 6. Enforcement extension

`tests/architecture/test_enum_integrity.py` scans every production file except
`config/` and `domain/enums.py` for bare string literals equal to any value of a
registered enum, and fails on a hit. The three new enums were **added to its
`ENUMS` tuple**, which is what makes them enforced rather than decorative:

* the 34 former `SmokeFixtureName(...)` literals are now bare-literal violations if reintroduced;
* `"reconstructed"` / `"reused"` can no longer be written as literals in `src/`;
* `"primary-order-three"` can no longer be written as a literal in `src/`.

The gate passes, proving no residual literal bypass exists.
