from fedcampaign_emhi.domain.types import ModuleContract


def lancaster_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.comparators.lancaster",
        ownership="Lancaster higher-order interaction reference",
    )
