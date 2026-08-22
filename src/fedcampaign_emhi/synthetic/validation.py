from fedcampaign_emhi.domain.types import ModuleContract


def validation_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.synthetic.validation",
        ownership="synthetic truth, purity, boundedness, seed behavior, and generator invariants",
    )
