from fedcampaign_emhi.domain.types import ModuleContract


def local_policy_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.detection.local_policy",
        ownership="calibrates and evaluates primary and strong local stopping policies",
    )
