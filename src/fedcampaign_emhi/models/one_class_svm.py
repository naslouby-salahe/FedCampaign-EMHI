from fedcampaign_emhi.domain.types import ModuleContract


def one_class_svm_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.models.one_class_svm",
        ownership="RBF One-Class SVM construction, fitting, persistence, and anomaly-score orientation",
    )
