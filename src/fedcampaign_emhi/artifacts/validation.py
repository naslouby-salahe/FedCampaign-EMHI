from pathlib import Path

from fedcampaign_emhi.artifacts.records import ArtifactManifest
from fedcampaign_emhi.domain.enums import ArtifactLifecycleState
from fedcampaign_emhi.domain.types import ArtifactInspection, ConfigurationDigest


def inspect_artifact(
    path: Path,
    expected: ArtifactManifest | None,
    computed_digest: ConfigurationDigest | None,
) -> ArtifactInspection:
    if expected is None or not path.is_file():
        return ArtifactInspection(
            artifact_id="missing",
            lifecycle_state=ArtifactLifecycleState.MISSING,
            material_fingerprint=None,
        )
    if computed_digest is None:
        return ArtifactInspection(
            artifact_id=expected.artifact_id,
            lifecycle_state=ArtifactLifecycleState.MALFORMED,
            material_fingerprint=expected.material_fingerprint,
        )
    if computed_digest != expected.content_digest:
        return ArtifactInspection(
            artifact_id=expected.artifact_id,
            lifecycle_state=ArtifactLifecycleState.STALE,
            material_fingerprint=expected.material_fingerprint,
        )
    if expected.lifecycle_state is ArtifactLifecycleState.INCOMPLETE:
        return ArtifactInspection(
            artifact_id=expected.artifact_id,
            lifecycle_state=ArtifactLifecycleState.INCOMPLETE,
            material_fingerprint=expected.material_fingerprint,
        )
    if expected.lifecycle_state is ArtifactLifecycleState.FAILED:
        return ArtifactInspection(
            artifact_id=expected.artifact_id,
            lifecycle_state=ArtifactLifecycleState.FAILED,
            material_fingerprint=expected.material_fingerprint,
        )
    return ArtifactInspection(
        artifact_id=expected.artifact_id,
        lifecycle_state=ArtifactLifecycleState.VALID,
        material_fingerprint=expected.material_fingerprint,
    )


def may_reuse(inspection: ArtifactInspection) -> bool:
    return inspection.lifecycle_state is ArtifactLifecycleState.VALID
