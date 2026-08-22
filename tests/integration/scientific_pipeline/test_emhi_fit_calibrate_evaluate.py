from fedcampaign_emhi.execution.status import module_contracts


def test_test_emhi_fit_calibrate_evaluate_module_contract_exists() -> None:
    contracts = module_contracts()
    assert contracts
