from fedcampaign_emhi.domain.types import ArtifactDependencyNode, ArtifactIdentity


def descendant_ids(
    graph: tuple[ArtifactDependencyNode, ...],
    changed_ids: tuple[ArtifactIdentity, ...],
) -> tuple[ArtifactIdentity, ...]:
    edges: list[tuple[ArtifactIdentity, ArtifactIdentity]] = []
    for node in graph:
        for upstream_id in node.upstream_ids:
            edges.append((upstream_id, node.artifact_id))
    discovered: list[ArtifactIdentity] = []
    pending: list[ArtifactIdentity] = list(changed_ids)
    seen: set[ArtifactIdentity] = set(changed_ids)
    while pending:
        current = pending.pop()
        for upstream_id, child in edges:
            if upstream_id != current or child in seen:
                continue
            seen.add(child)
            discovered.append(child)
            pending.append(child)
    return tuple(sorted(discovered))


def nodes_by_id(
    graph: tuple[ArtifactDependencyNode, ...],
) -> tuple[tuple[ArtifactIdentity, ArtifactDependencyNode], ...]:
    return tuple((node.artifact_id, node) for node in graph)
