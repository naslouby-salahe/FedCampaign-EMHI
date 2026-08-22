from fedcampaign_emhi.domain.types import ModuleContract


def scoring_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.detection.scoring",
        ownership="produces deterministic reusable detector score streams",
    )
