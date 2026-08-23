from dataclasses import dataclass

from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import ExperimentState, NuisanceTransformName
from fedcampaign_emhi.domain.types import ComponentName
from fedcampaign_emhi.synthetic.common_mode import (
    equally_spaced_loadings,
    generate_common_mode_scores,
    generate_unit_variance_autoregressive_latent,
)
from fedcampaign_emhi.synthetic.controlled_campaigns import (
    apply_marginal_score_shift,
    gaussian_copula_pair,
)
from fedcampaign_emhi.synthetic.robustness import (
    contaminated_outside_clients,
    dropout_coalition_is_active,
)
from fedcampaign_emhi.synthetic.self_explanation import (
    apply_persistent_perturbation,
    scalar_innovation_fixture,
)


@dataclass(frozen=True)
class SyntheticValidationResult:
    state: ExperimentState
    failed_checks: tuple[ComponentName, ...]


def validate_synthetic_generators(
    loaded: LoadedScientificConfiguration,
) -> SyntheticValidationResult:
    del loaded
    failed: list[ComponentName] = []
    loadings = equally_spaced_loadings(3, 0.0, 1.0)
    if loadings != (0.0, 0.5, 1.0):
        failed.append("common-mode loading grid")
    latent = generate_unit_variance_autoregressive_latent(8, 0.5, 11)
    scores = generate_common_mode_scores(latent, loadings, 0.5, 12)
    if len(scores) != len(latent) or any(len(row) != len(loadings) for row in scores):
        failed.append("common-mode score shape")
    shifted = apply_marginal_score_shift((0.0, 0.0, 0.0), ("a", "b", "c"), 1.0)
    if shifted != (1.0, 1.0, 1.0):
        failed.append("controlled marginal campaign")
    pair = gaussian_copula_pair(0.5, 13)
    if any(value < 0.0 or value > 1.0 for value in pair):
        failed.append("gaussian copula rank range")
    contaminated = contaminated_outside_clients(("a", "b", "c", "d"), 0.5)
    if contaminated != ("a", "b"):
        failed.append("outside contamination selection")
    if not dropout_coalition_is_active(
        ("a",), ("a", "b", "c"), ("a", "b", "c"), 1, 0.5
    ):
        failed.append("dropout active-coalition rule")
    perturbed = apply_persistent_perturbation((0.0, 0.0, 0.0), (1,), 0.5)
    if perturbed != (0.0, 0.5, 0.0):
        failed.append("self-explanation perturbation")
    innovation = scalar_innovation_fixture((1.0,), (1.0,), NuisanceTransformName.LINEAR)
    if innovation != 0.0:
        failed.append("self-explanation scalar fixture")
    return SyntheticValidationResult(
        state=ExperimentState.COMPLETED if not failed else ExperimentState.INVALID,
        failed_checks=tuple(failed),
    )
