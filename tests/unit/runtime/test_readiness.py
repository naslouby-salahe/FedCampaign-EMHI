from fedcampaign_emhi.domain.enums import DatasetName
from fedcampaign_emhi.domain.types import SeedDerivationIdentity
from fedcampaign_emhi.runtime.determinism import (
    derive_component_seed,
    seed_derivation_payload,
    thirty_two_bit_seed,
)
from fedcampaign_emhi.runtime.monitoring import assess_implementation_readiness


def test_readiness_probe() -> None:
    readiness = assess_implementation_readiness()
    assert readiness.production_configuration_valid is True
    assert readiness.unspecified_scientific_choice_count == 0


def test_component_seed_is_deterministic() -> None:
    identity = SeedDerivationIdentity(
        base_seed=4100,
        component_name="context",
        dataset=DatasetName.TON_IOT_NETWORK,
        client_ids=("b", "a"),
        coalition_ids=("c1",),
        condition_coordinates=(),
    )
    first = derive_component_seed(identity)
    second = derive_component_seed(identity)
    payload = seed_derivation_payload(identity)
    assert first == second
    assert first < 1 << 53
    assert isinstance(payload, dict)
    assert payload["base_seed"] == "4100"
    assert thirty_two_bit_seed(first) == first % (1 << 32)


def test_component_seed_accepts_a_prior_64_bit_derived_seed() -> None:
    identity = SeedDerivationIdentity(
        base_seed=4_213_418_195_274_617_918,
        component_name="nested-deterministic-component",
        dataset=None,
        client_ids=(),
        coalition_ids=(),
        condition_coordinates=(),
    )

    payload = seed_derivation_payload(identity)
    assert isinstance(payload, dict)
    assert payload["base_seed"] == "4213418195274617918"
    assert 0 <= derive_component_seed(identity) < 1 << 53


def test_component_seed_sorts_client_ids() -> None:
    left = SeedDerivationIdentity(
        base_seed=4100,
        component_name="context",
        dataset=None,
        client_ids=("b", "a"),
        coalition_ids=(),
        condition_coordinates=(),
    )
    right = SeedDerivationIdentity(
        base_seed=4100,
        component_name="context",
        dataset=None,
        client_ids=("a", "b"),
        coalition_ids=(),
        condition_coordinates=(),
    )
    assert derive_component_seed(left) == derive_component_seed(right)
