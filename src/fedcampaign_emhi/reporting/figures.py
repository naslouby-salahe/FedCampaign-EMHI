from fedcampaign_emhi.domain.types import ModuleContract


def figures_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.reporting.figures",
        ownership="compact manuscript-facing figures from already verified machine-readable outputs",
    )
