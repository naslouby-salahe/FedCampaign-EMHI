from fedcampaign_emhi.domain.types import ModuleContract


def ground_truth_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.datasets.optc.ground_truth",
        ownership="dataset adapter contract",
    )
