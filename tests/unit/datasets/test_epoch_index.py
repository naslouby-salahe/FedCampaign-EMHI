from fedcampaign_emhi.datasets.partitions import epoch_index


def test_epoch_index_uses_floor_division() -> None:
    computed = epoch_index(125.9, 60)
    assert computed.index == 2
