from fedcampaign_emhi.config.loading import load_smoke_configuration
from fedcampaign_emhi.evaluation.scalability import scalability_client_ids
from fedcampaign_emhi.synthetic.generators import (
    contaminate_rank,
    contaminated_outside_clients,
    outside_contamination_targets,
)


def test_boundary_client_ids_match_lexicographic_target_order() -> None:
    client_ids = scalability_client_ids(12)
    assert client_ids == tuple(sorted(client_ids))
    assert outside_contamination_targets(client_ids) == (
        "client-000",
        "client-001",
        "client-002",
    )


def test_contamination_shifts_only_selected_outside_clients() -> None:
    loaded = load_smoke_configuration()
    client_ids = scalability_client_ids(4)
    target = outside_contamination_targets(client_ids)
    outside = tuple(client_id for client_id in client_ids if client_id not in set(target))
    contaminated_ids = set(contaminated_outside_clients(outside, 1.0))
    shift = loaded.values.generators.outside_contamination.outside_rank_shift
    clip = loaded.values.context.rank_clip_epsilon
    row = (0.1, 0.2, 0.3, 0.4)
    shifted = tuple(
        contaminate_rank(rank, shift, clip) if client_id in contaminated_ids else rank
        for client_id, rank in zip(client_ids, row, strict=True)
    )
    assert shifted[:3] == row[:3]
    assert shifted[3] == contaminate_rank(row[3], shift, clip)
