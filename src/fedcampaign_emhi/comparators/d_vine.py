from fedcampaign_emhi.domain.types import ModuleContract


def d_vine_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.comparators.d_vine",
        ownership="D-vine conditional-dependence reference",
    )
