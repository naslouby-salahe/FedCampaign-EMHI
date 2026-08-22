from fedcampaign_emhi.domain.types import ModuleContract


def scalability_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.evaluation.scalability",
        ownership="client-count and reference-harness scalability and latency measurements",
    )
