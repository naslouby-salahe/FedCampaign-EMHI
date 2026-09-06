import hashlib
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from fedcampaign_emhi.artifacts.records import (
    ExperimentRunRecord,
)
from fedcampaign_emhi.artifacts.storage import (
    build_artifact_layout,
    write_atomic_json,
)
from fedcampaign_emhi.comparators.contracts import (
    ComparatorMethodContract,
    comparator_method_contracts,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration, ScientificConfig
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    ContextMethodName,
    DatasetName,
    ExperimentName,
    ExperimentState,
    MethodName,
    OverwritePolicy,
)
from fedcampaign_emhi.domain.types import (
    Boolean,
    ComponentName,
    ConfigurationDigest,
    RecordCount,
    YamlKeyPath,
)
from fedcampaign_emhi.experiments.registry import (
    RESUME_SEQUENCE,
    ExperimentContract,
    experiment_registry,
)
from fedcampaign_emhi.runtime import component_logger


def campaigns_logger() -> logging.Logger:
    return component_logger("experiments")


def campaign_dataset(
    loaded: LoadedScientificConfiguration, experiment_name: ExperimentName
) -> DatasetName:
    if experiment_name is ExperimentName.SECONDARY_CONTROLLED_TRACE_GENERALIZATION:
        return loaded.values.datasets.secondary.name
    return loaded.values.datasets.primary.name


@dataclass(frozen=True)
class ExperimentExecutionResult:
    experiment_name: ExperimentName
    state: ExperimentState
    run_record_path: Path
    completed_cell_count: RecordCount
    detail: ComponentName


@dataclass(frozen=True)
class _EmhiMethodSpecification:
    method_name: MethodName
    context_method: ContextMethodName
    maximum_order: CoalitionOrder
    purification_enabled: Boolean


def experiment_contract(
    config: ScientificConfig, experiment_name: ExperimentName
) -> ExperimentContract:
    return next(
        contract
        for contract in experiment_registry(config)
        if contract.experiment_name is experiment_name
    )


def _method_contract(method_name: MethodName) -> ComparatorMethodContract | None:
    return next(
        (
            contract
            for contract in comparator_method_contracts()
            if contract.method_name is method_name
        ),
        None,
    )


def emhi_method_specification(method_name: MethodName) -> _EmhiMethodSpecification | None:
    contract = _method_contract(method_name)
    if contract is None or contract.context_method is None or contract.enabled_order_set is None:
        return None
    if contract.is_equivalence_comparator:
        return None
    purification = contract.proper_subset_purification_enabled
    if purification is None:
        return None
    return _EmhiMethodSpecification(
        method_name=method_name,
        context_method=contract.context_method,
        maximum_order=max(contract.enabled_order_set),
        purification_enabled=purification,
    )


def run_record_path(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
) -> Path:
    layout = build_artifact_layout(loaded, repository)
    return (
        layout.experiment_outputs_root(experiment_name)
        / "provenance"
        / "dependencies"
        / "run-record.json"
    )


def implementation_digest(repository: Path) -> ConfigurationDigest:
    source_root = repository / "src" / "fedcampaign_emhi"
    digest = hashlib.sha256()
    for source_path in sorted(source_root.rglob("*.py")):
        digest.update(source_path.relative_to(source_root).as_posix().encode("utf-8"))
        digest.update(source_path.read_bytes())
    return digest.hexdigest()


def publish_experiment_run_record(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    overwrite_policy: OverwritePolicy,
    state: ExperimentState,
) -> Path:
    if state in {ExperimentState.NOT_STARTED, ExperimentState.READY}:
        raise ValueError("run records require an active, blocked, or terminal execution state")
    layout = build_artifact_layout(loaded, repository)
    staging = layout.roots.outputs_root / "cache" / "staging"
    destination = run_record_path(loaded, repository, experiment_name)
    record = ExperimentRunRecord(
        experiment_name=experiment_name,
        material_digest=loaded.material_digest,
        implementation_digest=implementation_digest(repository),
        overwrite_policy=overwrite_policy,
        resume_sequence=RESUME_SEQUENCE,
        state=state,
    )
    write_atomic_json(destination, cast(YamlNode, record.model_dump(mode="json")), staging)
    return destination


def as_mapping(payload: YamlNode) -> Mapping[YamlKeyPath, YamlNode]:
    if not isinstance(payload, Mapping):
        raise ValueError("evaluation payload must be a mapping")
    return payload
