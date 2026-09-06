from pathlib import Path

from tests.architecture.ast_scans import SRC_ROOT

REQUIRED_ROOT_FILES = (
    "README.md",
    "pyproject.toml",
    "configs/fedcampaign-emhi.yaml",
    "docs/Roadmap.md",
)

REQUIRED_AREAS = {
    "domain": {"enums.py", "types.py"},
    "config": {"schema.py", "loading.py", "validation.py"},
    "datasets": {"inventory.py", "preprocessing.py", "partitions.py", "campaigns.py"},
    "models": {"classical.py", "autoencoder.py"},
    "emhi": {
        "structure.py",
        "contexts.py",
        "projection.py",
        "innovations.py",
        "calibration.py",
        "thresholds.py",
        "evidence.py",
        "sequential.py",
    },
    "comparators": {
        "contracts.py",
        "dependence.py",
        "fusion.py",
        "sequential.py",
        "federated.py",
        "runtime.py",
    },
    "synthetic": {
        "generators.py",
        "self_explanation.py",
        "pure_order.py",
        "feasibility.py",
        "sequential.py",
    },
    "experiments": {
        "registry.py",
        "execution.py",
        "technical_retry.py",
        "synthetic.py",
        "synthetic_execution.py",
        "calibration.py",
        "robustness.py",
        "seed_materialization.py",
        "seed_evaluation.py",
        "seed_statistics.py",
        "coalition_scalability.py",
        "orchestration.py",
    },
    "evaluation": {"records.py", "sequential.py", "metrics.py", "scalability.py", "validation.py"},
    "analysis": {"statistics.py", "results.py"},
    "artifacts": {"records.py", "storage.py", "provenance.py"},
    "execution": {"preprocessing.py", "planning.py", "runner.py", "status.py"},
    "reporting": {"evidence.py", "export.py"},
}

FORBIDDEN_LEGACY_PATHS = {
    "detection",
    "runtime",
    "cli",
    "models/isolation_forest.py",
    "models/one_class_svm.py",
    "analysis/multiplicity.py",
    "analysis/summaries.py",
    "analysis/project.py",
    "analysis/claims.py",
    "analysis/claim_registry.py",
    "analysis/identity.py",
    "artifacts/paths.py",
    "artifacts/boundaries.py",
    "artifacts/dependencies.py",
    "synthetic/common_mode.py",
    "synthetic/controlled_campaigns.py",
    "synthetic/robustness.py",
    "synthetic/context_boundaries.py",
    "synthetic/validation.py",
}


def test_required_repository_files_exist(repo_root: Path) -> None:
    assert [name for name in REQUIRED_ROOT_FILES if not (repo_root / name).is_file()] == []


def test_target_areas_have_canonical_owners() -> None:
    for area, modules in REQUIRED_AREAS.items():
        root = SRC_ROOT / area
        assert root.is_dir(), area
        assert all((root / module).is_file() for module in modules), area
    assert (SRC_ROOT / "detection.py").is_file()
    assert (SRC_ROOT / "runtime.py").is_file()
    assert (SRC_ROOT / "cli.py").is_file()


def test_dataset_adapters_remain_dataset_specific() -> None:
    for dataset in ("ton_iot_network", "edge_iiotset"):
        root = SRC_ROOT / "datasets" / dataset
        assert all(
            (root / name).is_file()
            for name in ("loading.py", "canonicalization.py", "ground_truth.py", "validation.py")
        )


def test_legacy_paths_are_physically_absent() -> None:
    assert [path for path in FORBIDDEN_LEGACY_PATHS if (SRC_ROOT / path).exists()] == []


def test_source_tree_has_only_approved_top_level_areas() -> None:
    approved = set(REQUIRED_AREAS) | {
        "__init__.py",
        "detection.py",
        "runtime.py",
        "cli.py",
        "py.typed",
    }
    assert {path.name for path in SRC_ROOT.iterdir() if path.name != "__pycache__"} <= approved
