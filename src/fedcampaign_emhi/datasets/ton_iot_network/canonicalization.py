from fedcampaign_emhi.domain.types import ModuleContract


def canonicalization_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.datasets.ton_iot_network.canonicalization",
        ownership="dataset adapter contract",
    )
