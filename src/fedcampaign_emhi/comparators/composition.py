from fedcampaign_emhi.domain.types import ModuleContract


def composition_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.comparators.composition",
        ownership="predeclared strongest-comparator composition using fixed selection rules",
    )
