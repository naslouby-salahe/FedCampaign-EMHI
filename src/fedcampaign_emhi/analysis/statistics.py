from fedcampaign_emhi.domain.types import ModuleContract


def statistics_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.analysis.statistics",
        ownership="sign-flip inference, BCa intervals, Clopper-Pearson inference, effects, and equivalence procedures",
    )
