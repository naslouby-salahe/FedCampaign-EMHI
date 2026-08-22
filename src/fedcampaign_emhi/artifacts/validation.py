from fedcampaign_emhi.domain.types import ModuleContract


def validation_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.artifacts.validation",
        ownership="artifact identity, persistence, validation, path, and provenance",
    )
