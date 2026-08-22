from fedcampaign_emhi.domain.types import ModuleContract


def connected_information_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.comparators.connected_information",
        ownership="connected-information reference",
    )
