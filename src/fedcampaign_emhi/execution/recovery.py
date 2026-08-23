from dataclasses import dataclass

from fedcampaign_emhi.artifacts.dependencies import descendant_ids
from fedcampaign_emhi.artifacts.validation import may_reuse
from fedcampaign_emhi.domain.types import (
    ArtifactDependencyNode,
    ArtifactIdentity,
    ArtifactInspection,
    ResumeStep,
)
from fedcampaign_emhi.execution.planning import RESUME_SEQUENCE


@dataclass(frozen=True)
class RecoveryDecision:
    reconstruct_from_artifact_id: ArtifactIdentity | None
    reusable_ancestor_ids: tuple[ArtifactIdentity, ...]
    invalidated_descendant_ids: tuple[ArtifactIdentity, ...]
    resume_step: ResumeStep


def recovery_sequence() -> tuple[ResumeStep, ...]:
    return RESUME_SEQUENCE


def select_recovery_boundary(
    graph: tuple[ArtifactDependencyNode, ...],
    inspections: tuple[ArtifactInspection, ...],
) -> RecoveryDecision:
    by_id = {inspection.artifact_id: inspection for inspection in inspections}
    reusable: list[ArtifactIdentity] = []
    for node in graph:
        inspection = by_id.get(node.artifact_id)
        if inspection is not None and may_reuse(inspection):
            reusable.append(node.artifact_id)
            continue
        invalidated = descendant_ids(graph, (node.artifact_id,))
        return RecoveryDecision(
            reconstruct_from_artifact_id=node.artifact_id,
            reusable_ancestor_ids=tuple(reusable),
            invalidated_descendant_ids=invalidated,
            resume_step=RESUME_SEQUENCE[4],
        )
    return RecoveryDecision(
        reconstruct_from_artifact_id=None,
        reusable_ancestor_ids=tuple(reusable),
        invalidated_descendant_ids=(),
        resume_step=RESUME_SEQUENCE[-1],
    )
