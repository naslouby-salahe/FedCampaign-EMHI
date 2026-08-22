from fedcampaign_emhi.domain.types import ModuleContract


def isolation_forest_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.models.isolation_forest",
        ownership="Isolation Forest construction, fitting, persistence, and anomaly-score orientation",
    )
