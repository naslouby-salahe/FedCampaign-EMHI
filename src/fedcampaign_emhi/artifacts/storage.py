import hashlib
from pathlib import Path

from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.types import CanonicalUtf8Bytes, ConfigurationDigest
from fedcampaign_emhi.runtime.determinism import deterministic_digest, deterministic_utf8_bytes


def encode_canonical_payload(payload: YamlNode) -> CanonicalUtf8Bytes:
    return deterministic_utf8_bytes(payload)


def payload_digest(payload: YamlNode) -> ConfigurationDigest:
    return deterministic_digest(payload)


def file_sha256(path: Path) -> ConfigurationDigest:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def write_atomic_json(
    destination: Path, payload: YamlNode, staging_directory: Path
) -> ConfigurationDigest:
    staging_directory.mkdir(parents=True, exist_ok=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    encoded = encode_canonical_payload(payload)
    digest = hashlib.sha256(encoded).hexdigest()
    staging_path = staging_directory / f"{destination.name}.{digest}.partial"
    staging_path.write_bytes(encoded)
    staging_path.replace(destination)
    return digest


def read_json_bytes(path: Path) -> CanonicalUtf8Bytes:
    return path.read_bytes()
