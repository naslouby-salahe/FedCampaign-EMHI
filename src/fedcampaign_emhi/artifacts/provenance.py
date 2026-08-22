from fedcampaign_emhi.domain.types import ModuleContract


def provenance_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.artifacts.provenance",
        ownership="artifact identity, persistence, validation, path, and provenance",
    )
