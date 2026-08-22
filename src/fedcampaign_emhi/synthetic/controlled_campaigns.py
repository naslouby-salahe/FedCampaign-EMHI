from fedcampaign_emhi.domain.types import ModuleContract


def controlled_campaigns_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.synthetic.controlled_campaigns",
        ownership="controlled campaign alternatives and interaction structures",
    )
