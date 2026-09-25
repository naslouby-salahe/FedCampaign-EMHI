from dataclasses import replace

from fedcampaign_emhi.datasets.campaigns import build_campaign_registry, merge_malicious_runs
from fedcampaign_emhi.domain.enums import DatasetName
from fedcampaign_emhi.domain.types import ClientMaliciousEpochs


def test_merge_malicious_runs_merges_within_tolerance_and_splits_beyond_it() -> None:
    assert merge_malicious_runs((10, 11, 15, 30), 3, (12, 13, 14)) == ((10, 15), (30, 30))


def test_merge_malicious_runs_empty_input() -> None:
    assert merge_malicious_runs((), 5, ()) == ()


def test_merge_malicious_runs_does_not_merge_across_ambiguous_gap() -> None:
    assert merge_malicious_runs((10, 12), 1, ()) == ((10, 10), (12, 12))


def test_campaign_metadata_preserves_mixed_attack_categories_deterministically() -> None:
    clients = (
        ClientMaliciousEpochs(
            client_id="b",
            malicious_epochs=(100, 102),
            earliest_observed_epoch=0,
            fully_benign_epochs=(101,),
            attack_types_by_epoch=((100, ("DDoS",)), (102, ("XSS",))),
        ),
        ClientMaliciousEpochs(
            client_id="a",
            malicious_epochs=(100, 102),
            earliest_observed_epoch=0,
            fully_benign_epochs=(101,),
            attack_types_by_epoch=((100, ("DDoS",)), (102, ("XSS",))),
        ),
    )
    first = build_campaign_registry(
        DatasetName.TON_IOT_NETWORK,
        ("b", "a"),
        clients,
        1,
        2,
        5,
        3,
        60,
        (101,),
        evaluation_horizon_epochs=60,
    )
    second = build_campaign_registry(
        DatasetName.TON_IOT_NETWORK,
        ("b", "a"),
        clients,
        1,
        2,
        5,
        3,
        60,
        (101,),
        evaluation_horizon_epochs=60,
    )
    assert first == second
    assert first[0].sorted_participating_client_ids == ("a", "b")
    assert first[0].attack_types == ("DDoS", "XSS")
    assert first[0].warmup_epochs == 60
    assert first[0].evaluation_horizon_epochs == 60
    assert first[0].eligibility_status.value == "eligible"
    assert first[0].ineligibility_reason is None
    assert first[0].integrity_checksum == second[0].integrity_checksum
    assert (
        first[0].integrity_checksum
        != replace(first[0], evaluation_horizon_epochs=61).integrity_checksum
    )


def _client(
    client_id: str,
    malicious_epochs: tuple[int, ...],
    earliest_observed_epoch: int,
) -> ClientMaliciousEpochs:
    return ClientMaliciousEpochs(
        client_id=client_id,
        malicious_epochs=malicious_epochs,
        earliest_observed_epoch=earliest_observed_epoch,
    )


def test_campaign_rejected_when_prestart_warmup_precedes_observed_data() -> None:
    clients = (
        _client("a", (100, 101, 102), earliest_observed_epoch=50),
        _client("b", (100, 101, 102), earliest_observed_epoch=50),
    )
    registry = build_campaign_registry(
        dataset=DatasetName.TON_IOT_NETWORK,
        selected_client_ids=("a", "b"),
        client_malicious_epochs=clients,
        merge_max_intervening_benign_epochs=1,
        minimum_clients=2,
        distributed_first_activity_window_epochs=5,
        minimum_duration_epochs=1,
        prestart_warmup_epochs=60,
        evaluation_horizon_epochs=60,
    )
    assert registry == ()


def test_campaign_accepted_when_prestart_warmup_fully_observed_and_clean() -> None:
    clients = (
        _client("a", (100, 101, 102), earliest_observed_epoch=0),
        _client("b", (100, 101, 102), earliest_observed_epoch=0),
    )
    registry = build_campaign_registry(
        dataset=DatasetName.TON_IOT_NETWORK,
        selected_client_ids=("a", "b"),
        client_malicious_epochs=clients,
        merge_max_intervening_benign_epochs=1,
        minimum_clients=2,
        distributed_first_activity_window_epochs=5,
        minimum_duration_epochs=1,
        prestart_warmup_epochs=60,
        evaluation_horizon_epochs=60,
    )
    assert len(registry) == 1
    assert registry[0].start_epoch == 100
    assert registry[0].end_epoch == 102


def test_campaign_rejected_when_prior_malicious_epoch_falls_inside_warmup_window() -> None:
    clients = (
        _client("a", (40, 100, 101), earliest_observed_epoch=0),
        _client("b", (100, 101), earliest_observed_epoch=0),
    )
    registry = build_campaign_registry(
        dataset=DatasetName.TON_IOT_NETWORK,
        selected_client_ids=("a", "b"),
        client_malicious_epochs=clients,
        merge_max_intervening_benign_epochs=1,
        minimum_clients=2,
        distributed_first_activity_window_epochs=5,
        minimum_duration_epochs=1,
        prestart_warmup_epochs=60,
        evaluation_horizon_epochs=60,
    )
    assert registry == ()


def test_campaign_requires_minimum_distributed_clients() -> None:
    clients = (
        _client("a", (100, 101), earliest_observed_epoch=0),
        _client("b", (), earliest_observed_epoch=0),
    )
    registry = build_campaign_registry(
        dataset=DatasetName.TON_IOT_NETWORK,
        selected_client_ids=("a", "b"),
        client_malicious_epochs=clients,
        merge_max_intervening_benign_epochs=1,
        minimum_clients=2,
        distributed_first_activity_window_epochs=5,
        minimum_duration_epochs=1,
        prestart_warmup_epochs=60,
        evaluation_horizon_epochs=60,
    )
    assert registry == ()


def test_campaign_requires_synchronized_first_activity_window() -> None:
    clients = (
        _client("a", (100, 101, 102, 103, 104, 105, 106), earliest_observed_epoch=0),
        _client("b", (106,), earliest_observed_epoch=0),
    )
    registry = build_campaign_registry(
        dataset=DatasetName.TON_IOT_NETWORK,
        selected_client_ids=("a", "b"),
        client_malicious_epochs=clients,
        merge_max_intervening_benign_epochs=1,
        minimum_clients=2,
        distributed_first_activity_window_epochs=5,
        minimum_duration_epochs=1,
        prestart_warmup_epochs=60,
        evaluation_horizon_epochs=60,
    )
    assert registry == ()
