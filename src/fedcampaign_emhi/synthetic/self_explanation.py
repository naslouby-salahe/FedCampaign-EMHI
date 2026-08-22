from fedcampaign_emhi.domain.types import ModuleContract


def self_explanation_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.synthetic.self_explanation",
        ownership="exact-exclusion versus inclusive-context self-explanation experiments",
    )
