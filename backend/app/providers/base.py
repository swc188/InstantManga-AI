from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable


class ProviderError(Exception):
    """AI 模型调用失败时的统一异常，message 面向用户可读。"""


@dataclass
class GeneratedImage:
    path: Path
    used_ref: bool = False
    notes: list[str] = field(default_factory=list)


@runtime_checkable
class TextProvider(Protocol):
    supports: str = "text"

    def generate(self, prompt: str, system: str | None = None, **kw) -> str:
        """根据提示词生成文本。"""

    def rewrite(self, text: str, instruction: str) -> str:
        """按指令改写文本。"""

    def test_connection(self) -> bool:
        """探测服务连通性与鉴权是否有效。"""


@runtime_checkable
class ImageProvider(Protocol):
    supports: str = "image"

    def generate(
        self,
        prompt: str,
        ref_images: list[Path] | None = None,
        **kw,
    ) -> list[GeneratedImage]:
        """生成一张或多张图像。ref_images 为垫图参考，不支持时自动降级。"""

    def test_connection(self) -> bool:
        """探测服务连通性与鉴权是否有效。"""


@runtime_checkable
class TTSProvider(Protocol):
    supports: str = "tts"

    def synthesize(
        self,
        text: str,
        emotion: str | None = None,
        voice: str | None = None,
    ) -> Path:
        """合成带情绪的语音文件。"""

    def test_connection(self) -> bool:
        """探测服务连通性与鉴权是否有效。"""
