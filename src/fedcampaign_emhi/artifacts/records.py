from fedcampaign_emhi.domain.types import ModuleContract


def records_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.artifacts.records",
        ownership="artifact identity, persistence, validation, path, and provenance",
    )
