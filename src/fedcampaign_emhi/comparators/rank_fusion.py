from fedcampaign_emhi.domain.types import ModuleContract


def rank_fusion_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.comparators.rank_fusion",
        ownership="roadmap-defined marginal rank-fusion references",
    )
