from .base import ImageProvider, ProviderError, TextProvider, TTSProvider
from .openai_compatible import (
    OpenAICompatibleImageProvider,
    OpenAICompatibleTextProvider,
    OpenAICompatibleTTSProvider,
)
from .vendors import JimengImageProvider, KelingImageProvider

_IMAGE_FACTORIES: dict[str, type] = {
    "openai_compatible": OpenAICompatibleImageProvider,
    "jimeng": JimengImageProvider,
    "keling": KelingImageProvider,
}


def build_text_provider(base_url: str, api_key: str, model_name: str) -> TextProvider:
    return OpenAICompatibleTextProvider(
        base_url=base_url,
        api_key=api_key,
        model_name=model_name,
    )


def build_tts_provider(base_url: str, api_key: str, model_name: str) -> TTSProvider:
    return OpenAICompatibleTTSProvider(
        base_url=base_url,
        api_key=api_key,
        model_name=model_name,
    )


def build_image_provider(
    provider_type: str,
    base_url: str,
    api_key: str,
    model_name: str,
) -> ImageProvider:
    cls = _IMAGE_FACTORIES.get(provider_type)
    if cls is None:
        raise ProviderError(f"未知的图像提供商类型：{provider_type}")
    return cls(base_url=base_url, api_key=api_key, model_name=model_name)


def register_image_factory(provider_type: str, cls: type) -> None:
    _IMAGE_FACTORIES[provider_type] = cls


__all__ = [
    "build_image_provider",
    "build_text_provider",
    "build_tts_provider",
    "register_image_factory",
]
