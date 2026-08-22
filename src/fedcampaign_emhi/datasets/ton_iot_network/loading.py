from fedcampaign_emhi.domain.types import ModuleContract


def loading_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.datasets.ton_iot_network.loading",
        ownership="dataset adapter contract",
    )
