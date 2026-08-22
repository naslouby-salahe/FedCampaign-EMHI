from fedcampaign_emhi.execution.status import module_contracts


def test_test_comparator_pipeline_module_contract_exists() -> None:
    contracts = module_contracts()
    assert contracts
