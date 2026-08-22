from fedcampaign_emhi.config.schema import FrozenConfigModel
from fedcampaign_emhi.domain.enums import ArtifactLifecycleState, ArtifactNamespace, ExperimentName
from fedcampaign_emhi.domain.types import (
    ArtifactIdentity,
    ConfigurationDigest,
    MaterialDependencyFingerprint,
    RelativePath,
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
