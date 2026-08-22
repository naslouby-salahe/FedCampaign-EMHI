from fedcampaign_emhi.execution.status import module_contracts


def test_test_edge_iiotset_pipeline_module_contract_exists() -> None:
    contracts = module_contracts()
    assert contracts
