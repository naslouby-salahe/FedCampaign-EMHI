from fedcampaign_emhi.domain.types import ModuleContract


def conditional_log_linear_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.comparators.conditional_log_linear",
        ownership="conditional log-linear interaction reference",
    )
