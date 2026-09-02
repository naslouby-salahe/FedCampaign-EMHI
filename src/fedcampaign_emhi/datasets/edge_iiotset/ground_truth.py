from fedcampaign_emhi.domain.enums import GroundTruthClass
from fedcampaign_emhi.domain.types import AttackTypeName, BinaryClassLabel, GroundTruthLabel

BENIGN_ATTACK_TYPE = "normal"


def edge_iiotset_ground_truth(
    binary_label: BinaryClassLabel, attack_type: AttackTypeName
) -> GroundTruthLabel:
    normalized_type = attack_type.strip()
    if binary_label == 0 and normalized_type.lower() == BENIGN_ATTACK_TYPE:
        return GroundTruthLabel(
            classification=GroundTruthClass.BENIGN,
            attack_type=normalized_type,
            is_ambiguous=False,
        )
    if binary_label == 1 and normalized_type.lower() != BENIGN_ATTACK_TYPE:
        return GroundTruthLabel(
            classification=GroundTruthClass.MALICIOUS,
            attack_type=normalized_type,
            is_ambiguous=False,
        )
    return GroundTruthLabel(
        classification=GroundTruthClass.AMBIGUOUS,
        attack_type=normalized_type,
        is_ambiguous=True,
    )
