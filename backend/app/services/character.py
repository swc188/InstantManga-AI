import base64
import io
import logging
from pathlib import Path

from openai import OpenAI
import requests

from ..core.errors import ApiError
from ..core.security import decrypt_secret
from ..config import get_settings
from ..database import get_db
from ..models import ModelConfig
from sqlalchemy import select

logger = logging.getLogger(__name__)


def generate_character_portrait(
    project_id: int,
    character_name: str,
    keywords: str,
) -> str:
    """生成角色定妆照，返回文件路径。"""
    db = next(get_db())
    try:
        cfg = db.scalar(select(ModelConfig).where(ModelConfig.capability == "image"))
        if cfg is None or not cfg.is_valid:
            raise ApiError(
                status_code=400,
                code=400,
                message="图像模型未配置或未通过连通性测试",
            )

        client = OpenAI(
            api_key=decrypt_secret(cfg.api_key_enc),
            base_url=cfg.base_url,
        )

        prompt = f"Character portrait of {character_name}. {keywords}. High quality, detailed, manga style, full body shot, neutral background."

        response = client.images.generate(
            model=cfg.model_name,
            prompt=prompt,
            n=1,
            size="1024x1024",
        )

        image_url = response.data[0].url
        if not image_url:
            raise ApiError(status_code=502, code=502, message="图像生成失败：未返回图片")

        # 下载并保存图像
        import requests
        resp = requests.get(image_url, timeout=30)
        if resp.status_code != 200:
            raise ApiError(status_code=502, code=502, message="图像下载失败")

        # 保存到本地
        settings = get_settings()
        media_root = settings.media_root / str(project_id) / "characters"
        filename = f"{character_name}_portrait.png"
        filepath = media_root / filename

        with open(filepath, "wb") as f:
            f.write(resp.content)

        return f"characters/{filename}"
    finally:
        db.close()
