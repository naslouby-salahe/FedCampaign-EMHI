from fedcampaign_emhi.execution.status import module_contracts


def test_test_checkpoint_recovery_module_contract_exists() -> None:
    contracts = module_contracts()
    assert contracts
