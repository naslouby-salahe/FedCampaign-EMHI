from math import floor

from fedcampaign_emhi.domain.types import (
    ChronologicalPartitionLengths,
    EpochCount,
    Probability,
)


def chronological_partition_lengths(
    common_benign_epoch_count: EpochCount,
    detector_fit_fraction: Probability,
    nuisance_fit_fraction: Probability,
    threshold_fraction: Probability,
) -> ChronologicalPartitionLengths:
    detector_fit = floor(detector_fit_fraction * common_benign_epoch_count)
    nuisance_fit = floor(nuisance_fit_fraction * common_benign_epoch_count)
    threshold = floor(threshold_fraction * common_benign_epoch_count)
    used = detector_fit + nuisance_fit + threshold
    if used > common_benign_epoch_count:
        raise ValueError("configured partition fractions exceed the common benign epoch count")
    return ChronologicalPartitionLengths(
        detector_fit=detector_fit,
        nuisance_fit=nuisance_fit,
        threshold_and_policy_calibration=threshold,
        heldout_benign=common_benign_epoch_count - used,
    )
