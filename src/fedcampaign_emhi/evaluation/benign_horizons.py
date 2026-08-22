from fedcampaign_emhi.domain.types import ModuleContract


def benign_horizons_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.evaluation.benign_horizons",
        ownership="calibration and held-out benign horizons and finite-horizon PFA",
    )
