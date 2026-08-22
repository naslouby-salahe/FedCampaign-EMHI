from fedcampaign_emhi.domain.types import ModuleContract


def context_boundaries_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.synthetic.context_boundaries",
        ownership="estimator-support, context-support, and numerical-feasibility boundary scenarios",
    )
