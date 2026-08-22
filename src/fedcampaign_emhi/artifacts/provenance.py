from fedcampaign_emhi.artifacts.records import ArtifactManifest
from fedcampaign_emhi.artifacts.storage import payload_digest
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.types import ConfigurationDigest, MaterialDependencyFingerprint


def content_digest(payload: YamlNode) -> ConfigurationDigest:
    return payload_digest(payload)


def material_fingerprint(
    configuration_digest: ConfigurationDigest,
    upstream_digests: tuple[ConfigurationDigest, ...],
) -> MaterialDependencyFingerprint:
    payload: YamlNode = {
        "configuration_digest": configuration_digest,
        "upstream_digests": list(upstream_digests),
    }
    return payload_digest(payload)


def manifests_are_compatible(current: ArtifactManifest, observed: ArtifactManifest) -> bool:
    return (
        current.artifact_id == observed.artifact_id
        and current.material_fingerprint == observed.material_fingerprint
        and current.content_digest == observed.content_digest
        and current.upstream_ids == observed.upstream_ids
    )
