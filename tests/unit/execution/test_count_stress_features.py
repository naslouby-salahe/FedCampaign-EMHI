from math import expm1, log1p

import pytest

from fedcampaign_emhi.datasets.preprocessing import shannon_entropy
from fedcampaign_emhi.execution.runner import stress_epoch_feature_values


def test_stress_preserves_bucket_proportions_and_scales_total() -> None:
    original_counts = (10.0, 30.0, 60.0)
    buckets = tuple(log1p(count) for count in original_counts)
    unscaled = (*buckets, 100.0, shannon_entropy(original_counts))
    stressed = stress_epoch_feature_values(unscaled, 2.0)
    stressed_buckets = stressed[:-2]
    stressed_total = stressed[-2]
    stressed_entropy = stressed[-1]
    recovered = tuple(expm1(value) for value in stressed_buckets)
    assert recovered == pytest.approx((20.0, 60.0, 120.0))
    assert stressed_total == pytest.approx(200.0)
    original_proportions = tuple(count / sum(original_counts) for count in original_counts)
    stressed_proportions = tuple(count / sum(recovered) for count in recovered)
    assert stressed_proportions == pytest.approx(original_proportions)
    assert stressed_entropy == pytest.approx(shannon_entropy(original_counts))


def test_stress_rejects_vectors_without_bucket_dimensions() -> None:
    with pytest.raises(ValueError):
        stress_epoch_feature_values((1.0,), 2.0)
