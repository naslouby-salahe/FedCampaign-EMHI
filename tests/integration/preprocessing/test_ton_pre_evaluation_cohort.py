import csv
from pathlib import Path

from fedcampaign_emhi.artifacts.records import PreparedDatasetRecord
from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import (
    CohortSelectionWindow,
    DatasetName,
    GroundTruthClass,
    OverwritePolicy,
    PreprocessingCohortVariant,
)
from fedcampaign_emhi.execution.preprocessing import (
    execute_pre_evaluation_cohort_preprocess,
    execute_preprocess,
    missing_preprocessing_layers,
)
from fedcampaign_emhi.experiments.seed_materialization import preprocessing_paths


def test_pre_evaluation_selection_uses_fixed_window_but_prepares_all_selected_events(
    tmp_path: Path,
) -> None:
    loaded = load_production_configuration()
    sensitivity = loaded.values.experiments.pre_evaluation_cohort_selection_sensitivity
    start = sensitivity.support_window_start_epoch
    end = sensitivity.support_window_end_epoch_exclusive
    epoch_seconds = loaded.values.time.real_data_epoch_seconds
    raw = tmp_path / loaded.values.datasets.primary.raw_directory
    raw.mkdir(parents=True)
    path = raw / "Network_dataset_1.csv"
    clients = (
        ("10.0.0.0", 10_000, end + 100),
        ("10.0.0.1", 5_100, start),
        ("10.0.0.2", 5_000, start),
        ("10.0.0.3", 5_000, start),
        ("10.0.0.4", 5_000, start),
    )
    flow_id = 0
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(("ts", "src_ip", "proto", "service", "label", "type", "flow_id"))
        for client_id, total, first_epoch in clients:
            base, extra = divmod(total, 600)
            for epoch_offset in range(600):
                epoch = first_epoch + epoch_offset
                for within_epoch in range(base + int(epoch_offset < extra)):
                    flow_id += 1
                    writer.writerow(
                        (
                            epoch * epoch_seconds + within_epoch,
                            client_id,
                            "tcp",
                            "http",
                            0,
                            "normal",
                            flow_id,
                        )
                    )
        writer.writerow(
            (end * epoch_seconds, "10.0.0.1", "tcp", "http", 1, "scan", "attack-after-window")
        )

    execute_preprocess(
        loaded, tmp_path, DatasetName.TON_IOT_NETWORK, OverwritePolicy.REUSE_COMPATIBLE
    )
    assert missing_preprocessing_layers(loaded, tmp_path, DatasetName.TON_IOT_NETWORK) == ()
    _inventory_path, primary_prepared_path, *_rest = preprocessing_paths(
        loaded, tmp_path, DatasetName.TON_IOT_NETWORK
    )
    full_release = PreparedDatasetRecord.model_validate_json(primary_prepared_path.read_bytes())
    assert "10.0.0.0" in full_release.selected_client_ids
    assert "10.0.0.4" not in full_release.selected_client_ids

    execute_pre_evaluation_cohort_preprocess(loaded, tmp_path, OverwritePolicy.REUSE_COMPATIBLE)
    _inventory_path, variant_prepared_path, *_rest = preprocessing_paths(
        loaded,
        tmp_path,
        DatasetName.TON_IOT_NETWORK,
        PreprocessingCohortVariant.PRE_EVALUATION_SUPPORT_SENSITIVITY,
    )
    pre_evaluation = PreparedDatasetRecord.model_validate_json(variant_prepared_path.read_bytes())
    assert pre_evaluation.selected_client_ids == (
        "10.0.0.1",
        "10.0.0.2",
        "10.0.0.3",
        "10.0.0.4",
    )
    assert (
        pre_evaluation.cohort_selection_window
        is CohortSelectionWindow.PRE_EVALUATION_BENIGN_SUPPORT
    )
    assert pre_evaluation.cohort_selection_window_start_epoch == start
    assert pre_evaluation.cohort_selection_window_end_epoch_exclusive == end
    support = {row.client_id: row for row in pre_evaluation.cohort_support}
    assert support["10.0.0.1"].benign_event_count == 5_100
    assert support["10.0.0.1"].benign_nonempty_epoch_count == 600
    post_window_attack = next(
        row
        for row in pre_evaluation.epochs
        if row.client_id == "10.0.0.1" and row.epoch_index == end
    )
    assert post_window_attack.ground_truth is GroundTruthClass.MALICIOUS
    assert post_window_attack.raw_event_count == 1
