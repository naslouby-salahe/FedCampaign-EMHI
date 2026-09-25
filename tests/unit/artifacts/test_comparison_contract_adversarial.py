from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest

from fedcampaign_emhi.artifacts.provenance import real_campaign_comparison_contract_digest
from fedcampaign_emhi.artifacts.records import CampaignRecord, SeedSummaryRecord
from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration, ScientificConfig
from fedcampaign_emhi.domain.enums import (
    CampaignEligibilityStatus,
    DatasetName,
    ExecutionRole,
    ExperimentName,
    MethodName,
)
from fedcampaign_emhi.domain.types import ConfigurationDigest
from fedcampaign_emhi.experiments import seed_statistics

DigestMutation = Callable[[LoadedScientificConfiguration], str]
PairFunction = Callable[
    [
        LoadedScientificConfiguration,
        Path,
        ExperimentName,
        tuple[tuple[Path, SeedSummaryRecord], ...],
        tuple[tuple[Path, SeedSummaryRecord], ...],
    ],
    tuple[
        tuple[Path, ...],
        tuple[SeedSummaryRecord, ...],
        tuple[SeedSummaryRecord, ...],
        tuple[object, ...],
        tuple[object, ...],
    ],
]


def _campaign() -> CampaignRecord:
    return CampaignRecord(
        start_epoch=100,
        end_epoch=105,
        participating_client_ids=("source-a", "source-b"),
        attack_types=("DDoS", "XSS"),
        integrity_checksum="c" * 64,
        warmup_epochs=60,
        evaluation_horizon_epochs=60,
        eligibility_status=CampaignEligibilityStatus.ELIGIBLE,
    )


def _digest(
    loaded: LoadedScientificConfiguration,
    *,
    dataset_name: DatasetName = DatasetName.TON_IOT_NETWORK,
    seed: int = 21,
    source_digests: tuple[str, ...] = ("a" * 64, "b" * 64, "c" * 64),
    selected_client_ids: tuple[str, ...] = ("source-a", "source-b"),
    campaign: CampaignRecord | None = None,
    evaluation_epochs: tuple[tuple[int, ...], ...] = (tuple(range(100, 160)),),
    local_policy_target_pfa: float | None = None,
    config: ScientificConfig | None = None,
) -> str:
    return real_campaign_comparison_contract_digest(
        loaded.values if config is None else config,
        dataset_name,
        seed,
        source_digests,
        selected_client_ids,
        (_campaign() if campaign is None else campaign,),
        evaluation_epochs,
        (
            loaded.values.local_policy.primary_horizon_pfa_target
            if local_policy_target_pfa is None
            else local_policy_target_pfa
        ),
    )


MISMATCH_CASES: tuple[tuple[str, DigestMutation], ...] = (
    (
        "dataset identity",
        lambda loaded: _digest(loaded, dataset_name=DatasetName.EDGE_IIOTSET),
    ),
    ("seed", lambda loaded: _digest(loaded, seed=22)),
    (
        "source data or upstream artifact",
        lambda loaded: _digest(loaded, source_digests=("x" * 64, "b" * 64, "c" * 64)),
    ),
    (
        "selected cohort",
        lambda loaded: _digest(loaded, selected_client_ids=("source-a", "source-c")),
    ),
    (
        "campaign start",
        lambda loaded: _digest(
            loaded, campaign=_campaign().model_copy(update={"start_epoch": 101})
        ),
    ),
    (
        "campaign end",
        lambda loaded: _digest(loaded, campaign=_campaign().model_copy(update={"end_epoch": 106})),
    ),
    (
        "campaign participants",
        lambda loaded: _digest(
            loaded,
            campaign=_campaign().model_copy(update={"participating_client_ids": ("source-a",)}),
        ),
    ),
    (
        "campaign categories",
        lambda loaded: _digest(
            loaded, campaign=_campaign().model_copy(update={"attack_types": ("scanning",)})
        ),
    ),
    (
        "exact replay epochs",
        lambda loaded: _digest(loaded, evaluation_epochs=(tuple(range(100, 159)),)),
    ),
    (
        "campaign registry metadata",
        lambda loaded: _digest(loaded, source_digests=("a" * 64, "b" * 64, "d" * 64)),
    ),
    (
        "local policy contract",
        lambda loaded: _digest(loaded, local_policy_target_pfa=0.025),
    ),
    (
        "global calibration contract",
        lambda loaded: _digest(
            loaded,
            config=loaded.values.model_copy(
                update={
                    "evidence": loaded.values.evidence.model_copy(
                        update={
                            "calibrated_finite_horizon": loaded.values.evidence.calibrated_finite_horizon.model_copy(
                                update={"calibration_confidence": 0.94}
                            )
                        }
                    )
                }
            ),
        ),
    ),
    (
        "evaluation horizon configuration",
        lambda loaded: _digest(
            loaded,
            config=loaded.values.model_copy(
                update={
                    "campaign": loaded.values.campaign.model_copy(
                        update={"evaluation_horizon_epochs": 61}
                    )
                }
            ),
        ),
    ),
)


@pytest.mark.parametrize("component,mutate", MISMATCH_CASES)
def test_material_comparison_component_mismatch_changes_contract_digest(
    component: str,
    mutate: DigestMutation,
) -> None:
    loaded = load_production_configuration()
    base = _digest(loaded)
    assert mutate(loaded) != base, component


def _summary(method: MethodName, path: str) -> SeedSummaryRecord:
    return SeedSummaryRecord(
        experiment_name=ExperimentName.PRIMARY_STRICT_ODI_EVALUATION,
        execution_role=ExecutionRole.CONFIRMATORY,
        method_name=method,
        reference_method_name=None,
        metric_name="strict_odi_rate",
        seed=21,
        method_value=0.5,
        reference_value=None,
        paired_difference=None,
        campaign_count=1,
        source_evaluation_ids=(path,),
        dependency_fingerprint="e" * 64,
        content_digest="f" * 64,
    )


@pytest.mark.parametrize("contracts_match", (True, False))
def test_confirmatory_pairing_rejects_mismatched_comparison_contracts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contracts_match: bool,
) -> None:
    full = _summary(MethodName.FULL_FEDCAMPAIGN_EMHI, "full-evaluation")
    comparator = _summary(
        MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI, "comparator-evaluation"
    )
    digests: dict[MethodName, ConfigurationDigest] = {
        MethodName.FULL_FEDCAMPAIGN_EMHI: "a" * 64,
        MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI: (
            "a" * 64 if contracts_match else "b" * 64
        ),
    }

    def comparison_digest(
        _loaded: LoadedScientificConfiguration,
        _repository: Path,
        _experiment: ExperimentName,
        record: SeedSummaryRecord,
    ) -> ConfigurationDigest:
        return digests[record.method_name]

    monkeypatch.setattr(
        seed_statistics,
        "_comparison_" + "contract_digest",
        comparison_digest,
    )
    pairing = cast(
        PairFunction,
        getattr(seed_statistics, "_pair_" + "confirmatory_odi"),
    )
    paired = pairing(
        load_production_configuration(),
        tmp_path,
        ExperimentName.PRIMARY_STRICT_ODI_EVALUATION,
        ((tmp_path / "full.json", full),),
        ((tmp_path / "comparator.json", comparator),),
    )
    assert bool(paired[0]) is contracts_match
    assert bool(paired[1]) is contracts_match
    assert bool(paired[2]) is contracts_match
