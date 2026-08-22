from fedcampaign_emhi.domain.types import ModuleContract


def validation_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.datasets.ton_iot_network.validation",
        ownership="dataset adapter contract",
    )
