from fedcampaign_emhi.domain.types import ModuleContract


def validation_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.datasets.tc_engagement_5.validation",
        ownership="dataset adapter contract",
    )
