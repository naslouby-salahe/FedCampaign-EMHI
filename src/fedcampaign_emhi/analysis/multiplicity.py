from fedcampaign_emhi.domain.types import ModuleContract


def multiplicity_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.analysis.multiplicity",
        ownership="deterministic Holm-family correction and adjusted p-value computation",
    )
