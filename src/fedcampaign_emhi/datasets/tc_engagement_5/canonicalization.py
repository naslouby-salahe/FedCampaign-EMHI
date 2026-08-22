from fedcampaign_emhi.domain.types import ModuleContract


def canonicalization_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.datasets.tc_engagement_5.canonicalization",
        ownership="dataset adapter contract",
    )
