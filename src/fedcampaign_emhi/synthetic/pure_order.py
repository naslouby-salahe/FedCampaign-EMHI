from fedcampaign_emhi.domain.types import ModuleContract


def pure_order_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.synthetic.pure_order",
        ownership="polynomial, XOR, context-dependent, and mixed pure-order alternatives",
    )
