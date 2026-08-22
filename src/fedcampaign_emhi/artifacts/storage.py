from fedcampaign_emhi.domain.types import ModuleContract


def storage_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.artifacts.storage",
        ownership="artifact identity, persistence, validation, path, and provenance",
    )
