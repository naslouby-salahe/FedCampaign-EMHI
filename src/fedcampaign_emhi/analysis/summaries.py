from fedcampaign_emhi.domain.types import ModuleContract


def summaries_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.analysis.summaries",
        ownership="seed-level and condition-level aggregates preserving the correct inferential unit",
    )
