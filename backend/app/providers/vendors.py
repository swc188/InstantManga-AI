from pathlib import Path

from .base import GeneratedImage
from .openai_compatible import OpenAICompatibleImageProvider


class VendorImageProvider(OpenAICompatibleImageProvider):
    """厂商图像适配骨架。

    声明支持垫图参考（supports_ref_images=True），默认实现将参考图信息并入
    提示词并标注"垫图已应用"；子类可覆盖 _apply_ref 接入厂商的上传/参考接口。
    """

    supports_ref_images = True
    provider_type = "vendor"

    def _apply_ref(self, prompt: str, ref_images: list[Path]) -> str:
        names = ", ".join(p.name for p in ref_images)
        return f"{prompt}（参考图：{names}，请保持角色形象一致）"

    def generate(
        self,
        prompt: str,
        ref_images: list[Path] | None = None,
        output_dir: Path | None = None,
        n: int = 1,
        **kw,
    ) -> list[GeneratedImage]:
        effective_prompt = prompt
        notes: list[str] = []
        if ref_images:
            effective_prompt = self._apply_ref(prompt, ref_images)
            notes.append("垫图已应用：参考图信息已并入生成提示")
        results = super().generate(
            effective_prompt,
            ref_images=None,
            output_dir=output_dir,
            n=n,
            **kw,
        )
        for img in results:
            img.used_ref = bool(ref_images)
            img.notes = notes + img.notes
        return results


class JimengImageProvider(VendorImageProvider):
    provider_type = "jimeng"


class KelingImageProvider(VendorImageProvider):
    provider_type = "keling"
