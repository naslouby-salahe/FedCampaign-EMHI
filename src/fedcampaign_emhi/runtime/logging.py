from fedcampaign_emhi.domain.types import ModuleContract


def logging_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.runtime.logging",
        ownership="structured experiment, dataset, seed, stage, coordinate, reuse, status, and failure logs",
    )
