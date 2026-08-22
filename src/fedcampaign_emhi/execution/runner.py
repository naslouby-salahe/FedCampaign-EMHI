from pathlib import Path

from fedcampaign_emhi.artifacts.paths import build_artifact_layout
from fedcampaign_emhi.artifacts.storage import write_atomic_json
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import ExperimentName, ExperimentState
from fedcampaign_emhi.domain.types import ResumeStep
from fedcampaign_emhi.execution.planning import RESUME_SEQUENCE, plan_experiments


def resume_sequence() -> tuple[ResumeStep, ...]:
    return RESUME_SEQUENCE


def run_is_blocked_until_scientific_producers_exist(
    experiment_name: ExperimentName,
) -> ExperimentState:
    return ExperimentState.READY if experiment_name else ExperimentState.BLOCKED


def publish_plan_artifact(loaded: LoadedScientificConfiguration, repository: Path) -> Path:
    layout = build_artifact_layout(loaded, repository)
    staging = layout.roots.outputs_root / "cache" / "staging"
    destination = layout.roots.outputs_root / "preprocessing" / "metadata" / "execution-plan.json"
    payload = {
        "material_digest": loaded.material_digest,
        "resume_sequence": list(RESUME_SEQUENCE),
        "experiments": [
            {
                "experiment_name": planned.experiment_name.value,
                "execution_role": planned.execution_role.value,
                "seed_count": planned.seed_count,
                "state": planned.state.value,
            }
            for planned in plan_experiments(loaded)
        ],
    }
    write_atomic_json(destination, payload, staging)
    return destination
