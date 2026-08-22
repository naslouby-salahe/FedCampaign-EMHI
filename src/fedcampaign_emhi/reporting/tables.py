from fedcampaign_emhi.domain.types import ModuleContract


def tables_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.reporting.tables",
        ownership="compact manuscript-facing tables without recomputing scientific metrics or statistics",
    )
