from fedcampaign_emhi.domain.types import ModuleContract


def global_factor_residual_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.comparators.global_factor_residual",
        ownership="PCA global-factor residualization and deterministic rank selection",
    )
