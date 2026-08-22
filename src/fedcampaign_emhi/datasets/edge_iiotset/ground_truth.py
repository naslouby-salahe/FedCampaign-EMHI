from fedcampaign_emhi.domain.types import ModuleContract


def ground_truth_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.datasets.edge_iiotset.ground_truth",
        ownership="dataset adapter contract",
    )
