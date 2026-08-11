from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.errors import ApiError
from ..core.security import decrypt_secret
from ..models import ModelConfig
from ..providers.registry import build_text_provider


def get_text_provider(db: Session):
    cfg = db.scalar(select(ModelConfig).where(ModelConfig.capability == "text"))
    if cfg is None or not cfg.is_valid:
        raise ApiError(
            status_code=400,
            code=400,
            message="文本模型未配置或未通过连通性测试，请先到模型配置页完成设置",
        )
    return build_text_provider(
        base_url=cfg.base_url,
        api_key=decrypt_secret(cfg.api_key_enc),
        model_name=cfg.model_name,
    )
