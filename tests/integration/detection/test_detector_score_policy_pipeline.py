from fedcampaign_emhi.execution.status import module_contracts


def test_test_detector_score_policy_pipeline_module_contract_exists() -> None:
    contracts = module_contracts()
    assert contracts
