from fedcampaign_emhi.domain.types import ModuleContract


def canonicalization_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.datasets.edge_iiotset.canonicalization",
        ownership="dataset adapter contract",
    )
