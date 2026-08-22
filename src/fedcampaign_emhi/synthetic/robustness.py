from fedcampaign_emhi.domain.types import ModuleContract


def robustness_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.synthetic.robustness",
        ownership="outside-contamination, dropout, and context-sparsity robustness scenarios",
    )
