from fedcampaign_emhi.config.schema import FrozenConfigModel
from fedcampaign_emhi.domain.enums import (
    ArtifactLifecycleState,
    ArtifactNamespace,
    ExecutionRole,
    ExperimentName,
    ExperimentState,
    OverwritePolicy,
)
from fedcampaign_emhi.domain.types import (
    ArtifactIdentity,
    ConfigurationDigest,
    MaterialDependencyFingerprint,
    RelativePath,
    ResumeStep,
    SeedCount,
)


class ArtifactManifest(FrozenConfigModel):
    artifact_id: ArtifactIdentity
    namespace: ArtifactNamespace
    experiment_name: ExperimentName | None
    relative_path: RelativePath
    content_digest: ConfigurationDigest
    material_fingerprint: MaterialDependencyFingerprint
    upstream_ids: tuple[ArtifactIdentity, ...]
    lifecycle_state: ArtifactLifecycleState


class ExperimentRunRecord(FrozenConfigModel):
    experiment_name: ExperimentName
    material_digest: ConfigurationDigest
    overwrite_policy: OverwritePolicy
    resume_sequence: tuple[ResumeStep, ...]
    state: ExperimentState


class PlannedExperimentRecord(FrozenConfigModel):
    experiment_name: ExperimentName
    execution_role: ExecutionRole
    seed_count: SeedCount
    state: ExperimentState


class PlanArtifactRecord(FrozenConfigModel):
    material_digest: ConfigurationDigest
    resume_sequence: tuple[ResumeStep, ...]
    experiments: tuple[PlannedExperimentRecord, ...]
