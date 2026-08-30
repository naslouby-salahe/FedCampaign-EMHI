from dataclasses import dataclass
from pathlib import Path

from fedcampaign_emhi.domain.enums import ExecutionRole, ExperimentName, ExperimentState
from fedcampaign_emhi.domain.types import ComponentName, RelativePath, RuntimeSeconds, SeedValue
from fedcampaign_emhi.runtime.determinism import deterministic_utf8_bytes


@dataclass(frozen=True)
class RuntimeLogEvent:
    experiment_name: ExperimentName
    execution_role: ExecutionRole | None
    semantic_cell_path: RelativePath | None
    seed: SeedValue | None
    stage: ComponentName
    state: ExperimentState
    elapsed_seconds: RuntimeSeconds
    detail: ComponentName


def write_runtime_log(destination: Path, event: RuntimeLogEvent) -> None:
    payload = {
        "experiment_name": event.experiment_name.value,
        "execution_role": None if event.execution_role is None else event.execution_role.value,
        "semantic_cell_path": event.semantic_cell_path,
        "seed": event.seed,
        "stage": event.stage,
        "state": event.state.value,
        "elapsed_seconds": event.elapsed_seconds,
        "detail": event.detail,
    }
    encoded = deterministic_utf8_bytes(payload)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_suffix(destination.suffix + ".partial")
    staging.write_bytes(encoded)
    staging.replace(destination)
