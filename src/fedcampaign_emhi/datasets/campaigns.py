from fedcampaign_emhi.domain.types import ModuleContract


def campaigns_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.datasets.campaigns",
        ownership="campaign merging, eligibility, warm-up, activity, and evaluation-horizon semantics",
    )
