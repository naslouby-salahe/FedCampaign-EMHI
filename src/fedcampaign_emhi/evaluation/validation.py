from fedcampaign_emhi.domain.types import ModuleContract


def validation_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.evaluation.validation",
        ownership="metric eligibility, no-imputation rules, finite-value requirements, and outcome semantics",
    )
