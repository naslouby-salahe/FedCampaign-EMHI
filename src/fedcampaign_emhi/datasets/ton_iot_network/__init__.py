from fedcampaign_emhi.domain.types import ModuleContract


def package_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.datasets.ton_iot_network", ownership="dataset adapter"
    )
