from fedcampaign_emhi.domain.types import ModuleContract


def records_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.evaluation.records",
        ownership="typed immutable campaign, horizon, stop, evidence, latency, coverage, and evaluation records",
    )
