from fedcampaign_emhi.domain.types import ModuleContract


def fedavg_autoencoder_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.comparators.fedavg_autoencoder",
        ownership="unmatched FedAvg autoencoder comparator",
    )
