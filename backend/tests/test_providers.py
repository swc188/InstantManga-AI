import pytest

from app.providers.base import GeneratedImage, ProviderError
from app.providers.openai_compatible import (
    OpenAICompatibleBase,
    OpenAICompatibleImageProvider,
    OpenAICompatibleTextProvider,
    OpenAICompatibleTTSProvider,
)
from app.providers.registry import (
    build_image_provider,
    build_text_provider,
    build_tts_provider,
    register_image_factory,
)
from app.providers.vendors import JimengImageProvider

from .fake_client import FakeClient, FakeResponse


def patch_client(monkeypatch, handler):
    monkeypatch.setattr(
        OpenAICompatibleBase,
        "_client",
        lambda self: FakeClient(handler),
    )


def test_text_generate_returns_content(monkeypatch):
    def handler(method, url, **kw):
        assert method == "POST"
        assert url == "https://x.test/v1/chat/completions"
        return FakeResponse(json={"choices": [{"message": {"content": "你好"}}]})

    patch_client(monkeypatch, handler)
    provider = OpenAICompatibleTextProvider("https://x.test/v1", "k", "text-m")
    assert provider.generate("hi") == "你好"


def test_text_generate_missing_model():
    provider = OpenAICompatibleTextProvider("https://x.test/v1", "k", "")
    with pytest.raises(ProviderError, match="文本模型未配置"):
        provider.generate("hi")


def test_text_rewrite_prepends_instruction(monkeypatch):
    def handler(method, url, **kw):
        prompt = kw["json"]["messages"][1]["content"]
        assert "改写" in prompt
        return FakeResponse(json={"choices": [{"message": {"content": "new"}}]})

    patch_client(monkeypatch, handler)
    provider = OpenAICompatibleTextProvider("https://x.test/v1", "k", "text-m")
    assert provider.rewrite("old text", "更简洁") == "new"


def test_image_generate_writes_file_and_degrades_ref(monkeypatch, tmp_path):
    def handler(method, url, **kw):
        assert url == "https://x.test/v1/images/generations"
        assert kw["json"]["n"] == 2
        return FakeResponse(json={"data": [{"b64_json": "aGVsbG8="}, {"b64_json": "d29ybGQ="}]})

    patch_client(monkeypatch, handler)
    ref = tmp_path / "ref.png"
    ref.write_bytes(b"ref")
    provider = OpenAICompatibleImageProvider("https://x.test/v1", "k", "image-m")
    images = provider.generate("a girl", ref_images=[ref], output_dir=tmp_path, n=2)
    assert len(images) == 2
    assert images[0].path.is_file()
    assert images[0].used_ref is False
    assert any("降级" in n for n in images[0].notes)


def test_tts_writes_audio_file(monkeypatch, tmp_path):
    def handler(method, url, **kw):
        assert url == "https://x.test/v1/audio/speech"
        assert kw["json"]["voice"] == "onyx"
        return FakeResponse(content=b"fake-audio")

    patch_client(monkeypatch, handler)
    provider = OpenAICompatibleTTSProvider("https://x.test/v1", "k", "tts-m")
    path = provider.synthesize("你还好吗", emotion="生气", output_dir=tmp_path)
    assert path.is_file()
    assert path.read_bytes() == b"fake-audio"
    assert path.suffix == ".mp3"


def test_test_connection_ok(monkeypatch):
    def handler(method, url, **kw):
        return FakeResponse(json={"data": []})

    patch_client(monkeypatch, handler)
    provider = OpenAICompatibleTextProvider("https://x.test/v1", "k", "m")
    assert provider.test_connection() is True


def test_test_connection_unauthorized(monkeypatch):
    def handler(method, url, **kw):
        return FakeResponse(status_code=401)

    patch_client(monkeypatch, handler)
    provider = OpenAICompatibleTextProvider("https://x.test/v1", "k", "m")
    with pytest.raises(ProviderError, match="鉴权失败"):
        provider.test_connection()


def test_vendor_applies_ref_images(monkeypatch, tmp_path):
    provider = JimengImageProvider("https://x.test/v1", "k", "image-m")
    captured: dict = {}

    def fake_super(self, prompt, ref_images=None, output_dir=None, n=1, **kw):
        captured["prompt"] = prompt
        return [GeneratedImage(path=tmp_path / "a.png")]

    monkeypatch.setattr(OpenAICompatibleImageProvider, "generate", fake_super)
    ref = tmp_path / "ref.png"
    ref.write_bytes(b"x")
    results = provider.generate("女孩", ref_images=[ref], output_dir=tmp_path)
    assert "ref.png" in captured["prompt"]
    assert results[0].used_ref is True
    assert any("垫图已应用" in n for n in results[0].notes)


def test_build_image_provider_unknown_type():
    with pytest.raises(ProviderError, match="未知"):
        build_image_provider("nope", "u", "k", "m")


def test_register_custom_factory():
    class MyImage:
        def __init__(self, **kw):
            self.kw = kw

    register_image_factory("my-vendor", MyImage)
    provider = build_image_provider("my-vendor", "u", "k", "m")
    assert isinstance(provider, MyImage)


def test_builders_return_typed_providers():
    assert isinstance(build_text_provider("u", "k", "m"), OpenAICompatibleTextProvider)
    assert isinstance(build_tts_provider("u", "k", "m"), OpenAICompatibleTTSProvider)
    assert isinstance(
        build_image_provider("jimeng", "u", "k", "m"),
        JimengImageProvider,
    )
