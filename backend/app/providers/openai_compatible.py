import base64
import time
import uuid
from pathlib import Path

import httpx

from .base import GeneratedImage, GeneratedVideo, ProviderError

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

    def __init__(self, base_url: str, api_key: str, url_mode: str = "base"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.url_mode = url_mode  # "base" | "full"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _endpoint(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _client(self) -> httpx.Client:
        return httpx.Client(headers=self._headers(), timeout=DEFAULT_TIMEOUT)

    def test_connection(self) -> bool:
        # url_mode=full 时 base_url 本身就是完整端点，直接探测它
        if self.url_mode == "full":
            stripped = self.base_url.rstrip("/")
            try:
                with self._client() as client:
                    resp = client.get(stripped)
                if resp.status_code in (200, 405, 404):
                    return True
                if resp.status_code == 401:
                    raise ProviderError("鉴权失败：API Key 无效")
                if resp.status_code >= 400:
                    raise ProviderError(f"服务返回错误：HTTP {resp.status_code}")
                return True
            except ProviderError:
                raise
            except httpx.HTTPError as exc:
                raise ProviderError(f"服务不可达：{exc}") from exc
        # url_mode=base 时依次尝试多种探测方式，任意一种通过即返回 true
        # 1) /models GET
        try:
            with self._client() as client:
                resp = client.get(self._endpoint("/models"))
            if resp.status_code == 401:
                raise ProviderError("鉴权失败：API Key 无效")
            if resp.status_code == 200:
                return True
            if resp.status_code == 404:
                pass  # 继续尝试下一个
            else:
                return True
        except ProviderError:
            raise
        except httpx.HTTPError:
            pass
        # 2) /chat/completions POST
        try:
            with self._client() as client:
                resp2 = client.post(
                    self._endpoint("/chat/completions"),
                    json={"model": "test", "messages": [{"role": "user", "content": "test"}], "max_tokens": 1},
                )
            if resp2.status_code in (400, 401, 403):
                return True
            if resp2.status_code >= 400:
                raise ProviderError(f"模型服务返回错误：HTTP {resp2.status_code}")
        except ProviderError:
            raise
        except httpx.HTTPError:
            pass
        # 3) /v1 根路径 GET
        try:
            with self._client() as client:
                resp3 = client.get(self.base_url)
            if resp3.status_code == 401:
                raise ProviderError("鉴权失败：API Key 无效")
            if resp3.status_code in (200, 405, 404):
                return True
        except ProviderError:
            raise
        except httpx.HTTPError:
            pass
        raise ProviderError(
            "服务路径无效，请确认 base_url 已包含版本前缀，如 https://api.example.com/v1"
        )


class OpenAICompatibleTextProvider(OpenAICompatibleBase):
    def __init__(self, base_url: str, api_key: str, model_name: str, url_mode: str = "base"):
        super().__init__(base_url, api_key, url_mode)
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
    def __init__(self, base_url: str, api_key: str, model_name: str, url_mode: str = "base"):
        super().__init__(base_url, api_key, url_mode)
        self.model_name = model_name

    def _resolve_endpoint(self) -> str:
        """根据 url_mode 决定端点：full 模式直接用 base_url，base 模式拼接 /images/generations。"""
        if self.url_mode == "full":
            return self.base_url
        stripped = self.base_url.rstrip("/")
        return f"{stripped}/images/generations"

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
        url = self._resolve_endpoint()
        with self._client() as client:
            resp = client.post(url, json=payload)
        _raise_for(resp)
        data = resp.json().get("data", [])
        results: list[GeneratedImage] = []
        with self._client() as client:
            for item in data:
                image = _download_image(item, output_dir, client)
                results.append(GeneratedImage(path=image, used_ref=False, notes=notes))
        return results


class OpenAICompatibleTTSProvider(OpenAICompatibleBase):
    def __init__(self, base_url: str, api_key: str, model_name: str, url_mode: str = "base"):
        super().__init__(base_url, api_key, url_mode)
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


class OpenAICompatibleVideoProvider(OpenAICompatibleBase):
    """异步视频生成 provider（支持 Agnes Video V2.0 等兼容接口）。"""

    supports_ref_images = True
    POLL_INTERVAL = 5.0
    MAX_POLLS = 120

    def __init__(self, base_url: str, api_key: str, model_name: str, url_mode: str = "base"):
        super().__init__(base_url, api_key, url_mode)
        self.model_name = model_name

    def _resolve_video_endpoint(self) -> str:
        if self.url_mode == "full":
            return self.base_url
        stripped = self.base_url.rstrip("/")
        return f"{stripped}/v1/videos"

    def _resolve_query_endpoint(self) -> str:
        """拼接查询端点：<base>/agnesapi?video_id=xxx"""
        base = self.base_url.rstrip("/")
        if base.endswith(("/v1", "/v2")):
            base = base.rsplit("/", 1)[0]
        return f"{base}/agnesapi"

    def generate(
        self,
        prompt: str,
        ref_image: Path | None = None,
        output_dir: Path | None = None,
        **kw,
    ) -> GeneratedVideo:
        if not self.model_name:
            raise ProviderError("视频模型未配置")
        output_dir = output_dir or Path(".")
        output_dir.mkdir(parents=True, exist_ok=True)
        notes: list[str] = []

        payload: dict = {
            "model": self.model_name,
            "prompt": prompt,
            **kw,
        }
        if ref_image and ref_image.exists():
            b64 = base64.b64encode(ref_image.read_bytes()).decode()
            payload["ref_image"] = f"data:image/png;base64,{b64}"

        url = self._resolve_video_endpoint()
        with self._client() as client:
            resp = client.post(url, json=payload)
        _raise_for(resp)
        data = resp.json()
        video_id = data.get("video_id") or data.get("id") or data.get("task_id")
        if not video_id:
            raise ProviderError(f"视频任务创建失败，响应：{data}")

        # 轮询查询端点
        query_url = self._resolve_query_endpoint()
        for _ in range(self.MAX_POLLS):
            time.sleep(self.POLL_INTERVAL)
            with self._client() as client:
                poll_resp = client.get(query_url, params={"video_id": video_id})
            _raise_for(poll_resp)
            result = poll_resp.json()
            status = result.get("status", "")
            if status in ("succeeded", "completed", "done", 1, "1"):
                video_url = result.get("video_url") or result.get("output", {}).get("video_url")
                if not video_url:
                    raise ProviderError("视频生成完成但未返回视频 URL")
                filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
                path = output_dir / filename
                with client.get(video_url) as dl_resp:
                    dl_resp.raise_for_status()
                    path.write_bytes(dl_resp.content)
                return GeneratedVideo(path=path, notes=notes)
            if status in ("failed", "error", "cancelled", 2, "2"):
                msg = result.get("error", result.get("message", "视频生成失败"))
                raise ProviderError(f"视频生成失败：{msg}")

        raise ProviderError(f"视频生成超时（{self.MAX_POLLS * self.POLL_INTERVAL:.0f} 秒）")

    def test_connection(self) -> bool:
        stripped = self.base_url.rstrip("/")
        # 若为完整端点 URL，直接连通性检查
        if "/" in stripped[stripped.index("//") + 2:]:
            try:
                with self._client() as client:
                    resp = client.get(stripped)
                if resp.status_code in (200, 405):
                    return True
                if resp.status_code == 401:
                    raise ProviderError("鉴权失败：API Key 无效")
            except httpx.HTTPError as exc:
                raise ProviderError(f"服务不可达：{exc}") from exc
            return True
        # 标准 base_url，探测 /v1/videos 端点
        try:
            with self._client() as client:
                resp = client.post(
                    self._resolve_video_endpoint(),
                    json={"model": self.model_name, "prompt": "test", "n": 1},
                )
            if resp.status_code in (200, 400, 422):
                return True
            if resp.status_code == 401:
                raise ProviderError("鉴权失败：API Key 无效")
            if resp.status_code == 404:
                raise ProviderError(
                    "服务路径无效，请确认 base_url 已包含 /v1 等版本前缀，"
                    "如 https://api.example.com/v1"
                )
        except ProviderError:
            raise
        except httpx.HTTPError as exc:
            raise ProviderError(f"服务不可达：{exc}") from exc
        return True


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
