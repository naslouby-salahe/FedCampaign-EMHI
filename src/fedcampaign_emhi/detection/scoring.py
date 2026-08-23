from fedcampaign_emhi.artifacts.records import (
    ClientDetectorScoreStream,
    DatasetSplitRecord,
    DetectorScoreArtifactRecord,
    PreparedDatasetRecord,
)
from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.detection.detector_assignment import assign_detector_families
from fedcampaign_emhi.detection.fitting import (
    score_autoencoder,
    score_isolation_forest,
    score_one_class_svm,
)
from fedcampaign_emhi.domain.enums import DatasetName, DetectorFamily
from fedcampaign_emhi.domain.types import (
    ClientId,
    FiniteFloat,
    MaterialDependencyFingerprint,
    NumericalFloor,
    RankReference,
    RankValue,
    RecordCount,
    SeedDerivationIdentity,
    SeedValue,
)
from fedcampaign_emhi.emhi.ranks import clip_rank, midrank
from fedcampaign_emhi.runtime.determinism import derive_component_seed


def oriented_score_stream(scores: tuple[FiniteFloat, ...]) -> tuple[FiniteFloat, ...]:
    if not scores:
        raise ValueError("score stream must contain at least one epoch")
    return scores


def score_stream_isolation_check(score_count: RecordCount, epoch_count: RecordCount) -> None:
    if score_count != epoch_count:
        raise ValueError("detector score stream must contain exactly one score per scored epoch")


def rank_stream(
    scores: tuple[FiniteFloat, ...],
    benign_reference_scores: tuple[FiniteFloat, ...],
    rank_clip_epsilon: NumericalFloor,
) -> tuple[RankValue, ...]:
    if not benign_reference_scores:
        raise ValueError("marginal rank reference requires benign nuisance-fit scores")
    reference = RankReference(scores=benign_reference_scores)
    return tuple(clip_rank(midrank(score, reference), rank_clip_epsilon) for score in scores)


def detector_seed(
    root_seed: SeedValue,
    dataset_name: DatasetName,
    client_id: ClientId,
) -> SeedValue:
    return derive_component_seed(
        SeedDerivationIdentity(
            base_seed=root_seed,
            component_name="local-detector-fit",
            dataset=dataset_name,
            client_ids=(client_id,),
            coalition_ids=(),
            condition_coordinates=(),
        )
    )


def _score_client(
    config: ScientificConfig,
    detector_family: DetectorFamily,
    fit_rows: tuple[tuple[FiniteFloat, ...], ...],
    score_rows: tuple[tuple[FiniteFloat, ...], ...],
    seed: SeedValue,
    client_id: ClientId,
) -> tuple[FiniteFloat, ...]:
    if detector_family is DetectorFamily.ISOLATION_FOREST:
        detector = config.detectors.isolation_forest
        return score_isolation_forest(
            fit_rows,
            score_rows,
            detector.trees,
            detector.max_samples_cap,
            detector.max_features,
            detector.jobs,
            seed,
        )
    if detector_family is DetectorFamily.ONE_CLASS_SVM:
        detector = config.detectors.one_class_svm
        return score_one_class_svm(
            fit_rows,
            score_rows,
            detector.nu,
            detector.coefficient_zero,
            detector.solver_tolerance,
            detector.kernel_cache_mib,
            detector.max_iterations,
            seed,
        )
    detector = config.detectors.autoencoder
    if len(detector.betas) != 2:
        raise ValueError("autoencoder requires exactly two Adam beta coefficients")
    return score_autoencoder(
        fit_rows,
        score_rows,
        detector.learning_rate,
        detector.betas[0],
        detector.betas[1],
        detector.optimizer_epsilon,
        detector.weight_decay,
        detector.batch_size,
        detector.epochs,
        seed,
        client_id,
    )


def build_detector_score_artifact(
    config: ScientificConfig,
    prepared: PreparedDatasetRecord,
    split: DatasetSplitRecord,
    dataset_name: DatasetName,
    root_seed: SeedValue,
    dependency_fingerprint: MaterialDependencyFingerprint,
) -> DetectorScoreArtifactRecord:
    assignments = assign_detector_families(split.selected_client_ids)
    streams: list[ClientDetectorScoreStream] = []
    for assignment in assignments:
        client_rows = tuple(
            row for row in prepared.epochs if row.client_id == assignment.client_id
        )
        fit_rows = tuple(
            row.feature_values
            for row in client_rows
            if row.epoch_index in split.detector_fit_epochs
        )
        if not fit_rows:
            raise ValueError(
                f"selected client {assignment.client_id} has no benign detector-fit rows"
            )
        score_rows = tuple(row.feature_values for row in client_rows)
        seed = detector_seed(root_seed, dataset_name, assignment.client_id)
        scores = _score_client(
            config,
            assignment.family,
            fit_rows,
            score_rows,
            seed,
            assignment.client_id,
        )
        score_stream_isolation_check(len(scores), len(client_rows))
        streams.append(
            ClientDetectorScoreStream(
                client_id=assignment.client_id,
                detector_family=assignment.family,
                detector_seed=seed,
                epoch_indexes=tuple(row.epoch_index for row in client_rows),
                scores=scores,
            )
        )
    return DetectorScoreArtifactRecord(
        dataset_name=dataset_name,
        root_seed=root_seed,
        selected_client_ids=split.selected_client_ids,
        client_streams=tuple(streams),
        dependency_fingerprint=dependency_fingerprint,
    )
