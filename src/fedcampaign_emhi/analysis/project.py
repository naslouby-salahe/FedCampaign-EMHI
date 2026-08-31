from pathlib import Path
from typing import cast

from fedcampaign_emhi.analysis.multiplicity import HolmHypothesisInput, primary_holm_family
from fedcampaign_emhi.artifacts.boundaries import statistical_analysis_boundary_digest
from fedcampaign_emhi.artifacts.paths import build_artifact_layout
from fedcampaign_emhi.artifacts.provenance import material_fingerprint
from fedcampaign_emhi.artifacts.records import (
    HolmFamilyResultRecord,
    PrimaryHolmFamilyRecord,
    StatisticalRecord,
)
from fedcampaign_emhi.artifacts.storage import file_sha256, payload_digest, write_atomic_json
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import ExperimentName, PrimaryHolmHypothesis

PRIMARY_HOLM_STATISTICS = (
    (
        ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION,
        PrimaryHolmHypothesis.SELF_EXPLANATION_MATERIAL_ATTENUATION,
    ),
    (
        ExperimentName.PURE_ORDER_SEPARATION_VALIDATION,
        PrimaryHolmHypothesis.PURE_ORDER_TARGET_DRIFT,
    ),
    (
        ExperimentName.PRIMARY_STRICT_ODI_EVALUATION,
        PrimaryHolmHypothesis.PRIMARY_ODI_ADVANTAGE_OVER_ORDER_AT_MOST_TWO_EMHI,
    ),
    (
        ExperimentName.BENIGN_COMMON_MODE_ROBUSTNESS,
        PrimaryHolmHypothesis.COMMON_MODE_FALSE_CAMPAIGN_REDUCTION,
    ),
    (
        ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE,
        PrimaryHolmHypothesis.STRONG_LOCAL_ODI_ABOVE_MINIMUM,
    ),
)


def _verified_statistical_record(
    loaded: LoadedScientificConfiguration, repository: Path, path: Path
) -> StatisticalRecord:
    record = StatisticalRecord.model_validate_json(path.read_bytes())
    source_paths = tuple(repository / source_id for source_id in record.source_result_ids)
    if not source_paths or any(not source_path.is_file() for source_path in source_paths):
        raise ValueError(f"statistical record {path} has missing source results")
    source_digests = tuple(file_sha256(source_path) for source_path in source_paths)
    if record.dependency_fingerprint != material_fingerprint(
        statistical_analysis_boundary_digest(loaded.values), source_digests
    ):
        raise ValueError(f"statistical record {path} has stale source lineage")
    return record


def materialize_primary_holm_family(
    loaded: LoadedScientificConfiguration, repository: Path
) -> Path:
    layout = build_artifact_layout(loaded, repository)
    paths: list[Path] = []
    inputs: list[HolmHypothesisInput] = []
    for experiment_name, hypothesis in PRIMARY_HOLM_STATISTICS:
        root = layout.experiment_outputs_root(experiment_name) / "statistics"
        matching = tuple(
            path
            for path in sorted(root.rglob("*.json"))
            if _verified_statistical_record(loaded, repository, path).hypothesis_identifier
            == hypothesis.value
        )
        if len(matching) != 1:
            raise FileNotFoundError(f"missing verified primary Holm statistic {hypothesis.value!r}")
        record = _verified_statistical_record(loaded, repository, matching[0])
        paths.append(matching[0])
        inputs.append(
            HolmHypothesisInput(
                identifier=hypothesis.value,
                raw_p_value=record.raw_p_value,
                decision=record.decision,
            )
        )
    results = primary_holm_family(tuple(inputs))
    relative_paths = tuple(path.relative_to(repository).as_posix() for path in paths)
    source_hashes = tuple(file_sha256(path) for path in paths)
    payload: YamlNode = {
        "material_digest": loaded.material_digest,
        "results": [
            {
                "hypothesis_identifier": result.identifier,
                "raw_p_value": result.raw_p_value,
                "holm_input_p_value": result.holm_input_p_value,
                "adjusted_p_value": result.adjusted_p_value,
                "decision": result.decision.value,
            }
            for result in results
        ],
        "source_statistical_paths": list(relative_paths),
        "source_artifact_hashes": list(source_hashes),
    }
    record = PrimaryHolmFamilyRecord(
        material_digest=loaded.material_digest,
        results=tuple(
            HolmFamilyResultRecord(
                hypothesis_identifier=result.identifier,
                raw_p_value=result.raw_p_value,
                holm_input_p_value=result.holm_input_p_value,
                adjusted_p_value=result.adjusted_p_value,
                decision=result.decision,
            )
            for result in results
        ),
        source_statistical_paths=relative_paths,
        source_artifact_hashes=source_hashes,
        content_digest=payload_digest(payload),
    )
    path = (
        layout.roots.results_root
        / "project_summary"
        / "statistics"
        / "multiplicity"
        / "primary-holm.json"
    )
    write_atomic_json(
        path,
        cast(YamlNode, record.model_dump(mode="json")),
        layout.roots.outputs_root / "cache" / "staging",
    )
    return path
