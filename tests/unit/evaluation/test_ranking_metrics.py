import pytest

from fedcampaign_emhi.evaluation.metrics import auprc, auroc


def test_auroc_perfect_separation_is_one() -> None:
    scores = (0.1, 0.2, 0.8, 0.9)
    malicious = (False, False, True, True)
    assert auroc(scores, malicious) == pytest.approx(1.0)


def test_auroc_inverted_separation_is_zero() -> None:
    scores = (0.9, 0.8, 0.2, 0.1)
    malicious = (False, False, True, True)
    assert auroc(scores, malicious) == pytest.approx(0.0)


def test_auroc_ties_contribute_one_half() -> None:
    scores = (0.5, 0.5)
    malicious = (True, False)
    assert auroc(scores, malicious) == pytest.approx(0.5)


def test_auroc_matches_manual_pair_count() -> None:
    scores = (0.1, 0.4, 0.35, 0.8)
    malicious = (False, True, False, True)
    positives = (0.4, 0.8)
    negatives = (0.1, 0.35)
    concordant = 0.0
    for positive in positives:
        for negative in negatives:
            if positive > negative:
                concordant += 1.0
            elif positive == negative:
                concordant += 0.5
    expected = concordant / (len(positives) * len(negatives))
    assert auroc(scores, malicious) == pytest.approx(expected)


def test_auroc_is_not_defined_when_only_one_class_present() -> None:
    assert auroc((0.1, 0.2, 0.3), (False, False, False)) is None
    assert auroc((0.1, 0.2, 0.3), (True, True, True)) is None


def test_auroc_requires_aligned_and_nonempty_inputs() -> None:
    with pytest.raises(ValueError):
        auroc((0.1, 0.2), (True,))
    with pytest.raises(ValueError):
        auroc((), ())


def test_auprc_perfect_separation_is_one() -> None:
    scores = (0.1, 0.2, 0.8, 0.9)
    malicious = (False, False, True, True)
    assert auprc(scores, malicious) == pytest.approx(1.0)


def test_auprc_worst_case_ranking_equals_base_rate_lower_bound() -> None:
    scores = (0.9, 0.8, 0.2, 0.1)
    malicious = (False, False, True, True)
    result = auprc(scores, malicious)
    assert result is not None
    assert result < 0.6


def test_auprc_is_not_defined_when_only_one_class_present() -> None:
    assert auprc((0.1, 0.2, 0.3), (False, False, False)) is None
    assert auprc((0.1, 0.2, 0.3), (True, True, True)) is None


def test_auprc_requires_aligned_and_nonempty_inputs() -> None:
    with pytest.raises(ValueError):
        auprc((0.1, 0.2), (True,))
    with pytest.raises(ValueError):
        auprc((), ())


def test_auprc_matches_manual_average_precision() -> None:
    scores = (0.9, 0.1, 0.7, 0.3)
    malicious = (True, False, True, False)
    assert auprc(scores, malicious) == pytest.approx(1.0)
