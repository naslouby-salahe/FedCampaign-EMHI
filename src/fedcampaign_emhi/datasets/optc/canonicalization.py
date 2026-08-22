from fedcampaign_emhi.domain.types import ModuleContract


def canonicalization_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.datasets.optc.canonicalization",
        ownership="dataset adapter contract",
    )
