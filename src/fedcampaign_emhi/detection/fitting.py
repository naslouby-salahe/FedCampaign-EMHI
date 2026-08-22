from fedcampaign_emhi.domain.types import ModuleContract


def fitting_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.detection.fitting",
        ownership="fits local detectors exclusively from permitted benign detector-fit data",
    )
