from fedcampaign_emhi.domain.types import ModuleContract


def conditional_hofd_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.comparators.conditional_hofd",
        ownership="exclusion-matched conditional HOFD equivalence comparison",
    )
