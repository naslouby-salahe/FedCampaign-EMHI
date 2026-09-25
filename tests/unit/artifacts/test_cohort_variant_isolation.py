from pathlib import Path

from fedcampaign_emhi.artifacts.provenance import experiment_semantic_digest
from fedcampaign_emhi.artifacts.storage import (
    detector_score_artifact_id,
    detector_score_artifact_path,
    emhi_fit_artifact_id,
    emhi_fit_artifact_path,
    layer_artifact_id,
    marginal_rank_artifact_id,
    marginal_rank_artifact_path,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import (
    ExperimentName,
    MethodName,
    PreprocessingCohortVariant,
    PreprocessingLayer,
)
from fedcampaign_emhi.experiments.execution import preprocessing_cohort_variant
from fedcampaign_emhi.experiments.seed_materialization import (
    preprocessing_paths,
    required_preprocessing_artifacts,
)


def test_pre_evaluation_cohort_artifacts_are_separate(
    production_configuration: LoadedScientificConfiguration, repo_root: Path
) -> None:
    loaded = production_configuration
    dataset = loaded.values.datasets.primary.name
    variant = PreprocessingCohortVariant.PRE_EVALUATION_SUPPORT_SENSITIVITY
    assert (
        preprocessing_cohort_variant(ExperimentName.PRE_EVALUATION_COHORT_SELECTION_SENSITIVITY)
        is variant
    )
    assert preprocessing_cohort_variant(ExperimentName.PRIMARY_STRICT_ODI_EVALUATION) is None
    primary_preprocessing = preprocessing_paths(loaded, repo_root, dataset)
    variant_preprocessing = preprocessing_paths(loaded, repo_root, dataset, variant)
    assert all(
        primary != alternate
        for primary, alternate in zip(primary_preprocessing, variant_preprocessing, strict=True)
    )
    assert (
        required_preprocessing_artifacts(
            loaded,
            repo_root,
            ExperimentName.PRE_EVALUATION_COHORT_SELECTION_SENSITIVITY,
        )
        == variant_preprocessing
    )
    primary_score = detector_score_artifact_path(loaded, repo_root, dataset, 1)
    variant_score = detector_score_artifact_path(loaded, repo_root, dataset, 1, variant)
    primary_rank = marginal_rank_artifact_path(loaded, repo_root, dataset, 1)
    variant_rank = marginal_rank_artifact_path(loaded, repo_root, dataset, 1, variant)
    primary_fit = emhi_fit_artifact_path(
        loaded, repo_root, dataset, 1, MethodName.FULL_FEDCAMPAIGN_EMHI
    )
    variant_fit = emhi_fit_artifact_path(
        loaded, repo_root, dataset, 1, MethodName.FULL_FEDCAMPAIGN_EMHI, variant
    )
    assert primary_score != variant_score
    assert primary_rank != variant_rank
    assert primary_fit != variant_fit
    assert detector_score_artifact_id(dataset, 1) != detector_score_artifact_id(dataset, 1, variant)
    assert marginal_rank_artifact_id(dataset, 1) != marginal_rank_artifact_id(dataset, 1, variant)
    assert emhi_fit_artifact_id(
        dataset, 1, MethodName.FULL_FEDCAMPAIGN_EMHI
    ) != emhi_fit_artifact_id(dataset, 1, MethodName.FULL_FEDCAMPAIGN_EMHI, variant)
    assert layer_artifact_id(dataset, PreprocessingLayer.PREPARED) != layer_artifact_id(
        dataset, PreprocessingLayer.PREPARED, variant
    )


def test_pre_evaluation_cohort_has_distinct_semantic_digest() -> None:
    assert experiment_semantic_digest(
        ExperimentName.PRE_EVALUATION_COHORT_SELECTION_SENSITIVITY
    ) != experiment_semantic_digest(ExperimentName.PRIMARY_STRICT_ODI_EVALUATION)
