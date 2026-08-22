from fedcampaign_emhi.domain.types import ModuleContract


def campaign_replay_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.evaluation.campaign_replay",
        ownership="campaign-anchored replay with independently reset global and local stopping state",
    )
