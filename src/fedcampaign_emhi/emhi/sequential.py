from fedcampaign_emhi.domain.types import ModuleContract


def sequential_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.emhi.sequential",
        ownership="sequential recursion, distributed support, statistical stopping, and stopping-time semantics",
    )
