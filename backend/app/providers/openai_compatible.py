import base64
import uuid
from pathlib import Path

import httpx

from .base import GeneratedImage, ProviderError

DEFAULT_TIMEOUT = 60.0

EMOTION_VOICES: dict[str, str] = {
    "生气": "onyx",
    "愤怒": "onyx",
    "哭泣": "shimmer",
    "悲伤": "shimmer",
    "惊喜": "nova",
    "开心": "alloy",
    "温柔": "echo",
    "冷漠": "fable",
}


class OpenAICompatibleBase:
    """OpenAI 兼容协议共享逻辑：鉴权、端点拼接、错误转换、连通性探测。"""

    supports_ref_images = False

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _endpoint(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _client(self) -> httpx.Client:
        return httpx.Client(headers=self._headers(), timeout=DEFAULT_TIMEOUT)

    def test_connection(self) -> bool:
        try:
            with self._client() as client:
                resp = client.get(self._endpoint("/models"))
        except httpx.HTTPError as exc:
            raise ProviderError(f"模型服务不可达：{exc}") from exc
        if resp.status_code == 401:
            raise ProviderError("鉴权失败：API Key 无效")
        if resp.status_code == 404:
            raise ProviderError("服务路径无效，base_url 可能缺少 /v1 等版本前缀")
        if resp.status_code >= 400:
            raise ProviderError(f"模型服务返回错误：HTTP {resp.status_code}")
        return True


class OpenAICompatibleTextProvider(OpenAICompatibleBase):
    def __init__(self, base_url: str, api_key: str, model_name: str):
        super().__init__(base_url, api_key)
        self.model_name = model_name

    def generate(self, prompt: str, system: str | None = None, **kw) -> str:
        if not self.model_name:
            raise ProviderError("文本模型未配置")
        payload: dict = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system or ""},
                {"role": "user", "content": prompt},
            ],
            **kw,
        }
        with self._client() as client:
            resp = client.post(self._endpoint("/chat/completions"), json=payload)
        _raise_for(resp)
        try:
            return resp.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise ProviderError("文本服务响应结构异常") from exc

    def rewrite(self, text: str, instruction: str) -> str:
        return self.generate(f"请按以下要求改写原文：{instruction}\n\n原文：{text}")


class OpenAICompatibleImageProvider(OpenAICompatibleBase):
    def __init__(self, base_url: str, api_key: str, model_name: str):
        super().__init__(base_url, api_key)
        self.model_name = model_name

    def generate(
        self,
        prompt: str,
        ref_images: list[Path] | None = None,
        output_dir: Path | None = None,
        n: int = 1,
        **kw,
    ) -> list[GeneratedImage]:
        if not self.model_name:
            raise ProviderError("图像模型未配置")
        output_dir = output_dir or Path(".")
        output_dir.mkdir(parents=True, exist_ok=True)
        notes: list[str] = []
        if ref_images:
            notes.append("当前提供商不支持垫图，已忽略参考图并降级为纯描述词生成")

        payload: dict = {
            "model": self.model_name,
            "prompt": prompt,
            "n": n,
            "size": kw.pop("size", "1024x1024"),
        }
        payload.update(kw)
        with self._client() as client:
            resp = client.post(self._endpoint("/images/generations"), json=payload)
        _raise_for(resp)
        data = resp.json().get("data", [])
        results: list[GeneratedImage] = []
        with self._client() as client:
            for item in data:
                image = _download_image(item, output_dir, client)
                results.append(GeneratedImage(path=image, used_ref=False, notes=notes))
        return results


class OpenAICompatibleTTSProvider(OpenAICompatibleBase):
    def __init__(self, base_url: str, api_key: str, model_name: str):
        super().__init__(base_url, api_key)
        self.model_name = model_name

    def synthesize(
        self,
        text: str,
        emotion: str | None = None,
        voice: str | None = None,
        output_dir: Path | None = None,
    ) -> Path:
        if not self.model_name:
            raise ProviderError("语音合成模型未配置")
        output_dir = output_dir or Path(".")
        output_dir.mkdir(parents=True, exist_ok=True)
        payload: dict = {
            "model": self.model_name,
            "input": text,
            "voice": voice or EMOTION_VOICES.get(emotion or "", "alloy"),
        }
        with self._client() as client:
            resp = client.post(self._endpoint("/audio/speech"), json=payload)
        _raise_for(resp)
        filename = f"voice_{uuid.uuid4().hex[:8]}.mp3"
        path = output_dir / filename
        path.write_bytes(resp.content)
        return path


def _raise_for(resp: httpx.Response) -> None:
    if resp.status_code >= 400:
        detail = ""
        try:
            detail = resp.json().get("error", {}).get("message", "")
        except Exception:
            detail = resp.text[:200]
        raise ProviderError(f"模型调用失败（HTTP {resp.status_code}）：{detail}")


def _download_image(
    item: dict,
    output_dir: Path,
    client: httpx.Client,
) -> Path:
    filename = f"img_{uuid.uuid4().hex[:8]}.png"
    path = output_dir / filename
    if item.get("b64_json"):
        path.write_bytes(base64.b64decode(item["b64_json"]))
        return path
    url = item.get("url")
    if url:
        resp = client.get(url)
        resp.raise_for_status()
        ext = Path(url.split("?")[0]).suffix or ".png"
        path = path.with_suffix(ext)
        path.write_bytes(resp.content)
        return path
    raise ProviderError("图像服务响应缺少图片数据")
