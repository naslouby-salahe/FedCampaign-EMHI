from fedcampaign_emhi.domain.types import ModuleContract


def multistream_cusum_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.comparators.multistream_cusum",
        ownership="roadmap-defined multistream CUSUM sequential baseline",
    )
