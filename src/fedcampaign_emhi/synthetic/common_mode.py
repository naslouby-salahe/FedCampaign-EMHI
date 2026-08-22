from fedcampaign_emhi.domain.types import ModuleContract


def common_mode_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.synthetic.common_mode",
        ownership="latent common-mode benign coordination and count-stress scenarios",
    )
