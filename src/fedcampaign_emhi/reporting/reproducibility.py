from fedcampaign_emhi.domain.types import ModuleContract


def reproducibility_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.reporting.reproducibility",
        ownership="compact final configuration, dataset, seed, software, and execution metadata",
    )
