from fedcampaign_emhi.domain.enums import DetectorFamily, DetectorFamilyRemainder
from fedcampaign_emhi.domain.types import ClientId, DetectorFamilyAssignment

_FAMILY_BY_REMAINDER = {
    DetectorFamilyRemainder.ISOLATION_FOREST: DetectorFamily.ISOLATION_FOREST,
    DetectorFamilyRemainder.ONE_CLASS_SVM: DetectorFamily.ONE_CLASS_SVM,
    DetectorFamilyRemainder.AUTOENCODER: DetectorFamily.AUTOENCODER,
}


def assign_detector_families(
    client_ids: tuple[ClientId, ...],
) -> tuple[DetectorFamilyAssignment, ...]:
    ordered = tuple(sorted(client_ids))
    assignments: list[DetectorFamilyAssignment] = []
    for index, client_id in enumerate(ordered):
        remainder = DetectorFamilyRemainder(index % 3)
        assignments.append(
            DetectorFamilyAssignment(
                client_id=client_id,
                zero_based_index=index,
                family=_FAMILY_BY_REMAINDER[remainder],
            )
        )
    return tuple(assignments)
