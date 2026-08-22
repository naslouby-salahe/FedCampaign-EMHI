from fedcampaign_emhi.domain.types import ModuleContract


def pair_dependence_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.comparators.pair_dependence",
        ownership="conditional order-two dependence predecessor",
    )
