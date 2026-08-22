from fedcampaign_emhi.domain.types import FeatureDimension, LayerWidth, ModuleContract

AUTOENCODER_ENCODER_WIDTH: LayerWidth = 32
AUTOENCODER_LATENT_WIDTH: LayerWidth = 8
AUTOENCODER_DECODER_WIDTH: LayerWidth = 32


def autoencoder_layer_widths(
    input_dimension: FeatureDimension,
) -> tuple[FeatureDimension, LayerWidth, LayerWidth, LayerWidth, FeatureDimension]:
    return (
        input_dimension,
        AUTOENCODER_ENCODER_WIDTH,
        AUTOENCODER_LATENT_WIDTH,
        AUTOENCODER_DECODER_WIDTH,
        input_dimension,
    )


def autoencoder_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.models.autoencoder",
        ownership="roadmap-defined autoencoder architecture, deterministic training, and reconstruction scoring",
    )
