from fedcampaign_emhi.domain.types import ModuleContract


def dependencies_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.artifacts.dependencies",
        ownership="artifact identity, persistence, validation, path, and provenance",
    )
