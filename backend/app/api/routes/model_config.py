from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.errors import ApiError
from ...core.security import decrypt_secret, encrypt_secret
from ...database import get_db
from ...models import ModelConfig
from ...providers.base import ProviderError
from ...providers.registry import (
    build_image_provider,
    build_text_provider,
    build_tts_provider,
    build_video_provider,
)
from ...schemas.model_config import (
    CAPABILITIES,
    ModelConfigOut,
    ModelConfigTest,
    ModelConfigUpsert,
    mask_key,
)
from ...core.response import ApiResponse

router = APIRouter(prefix="/model-config", tags=["model-config"])


def _build(
    capability: str,
    provider_type: str,
    base_url: str,
    api_key: str,
    model_name: str,
    url_mode: str = "base",
):
    if capability == "text":
        return build_text_provider(base_url, api_key, model_name, url_mode=url_mode)
    if capability == "image":
        return build_image_provider(provider_type, base_url, api_key, model_name, url_mode=url_mode)
    if capability == "tts":
        return build_tts_provider(base_url, api_key, model_name, url_mode=url_mode)
    if capability == "video":
        return build_video_provider(provider_type, base_url, api_key, model_name, url_mode=url_mode)
    raise ApiError(status_code=404, code=404, message=f"未知的能力类型：{capability}")


def _to_out(cfg: ModelConfig) -> ModelConfigOut:
    return ModelConfigOut(
        capability=cfg.capability,
        provider_type=cfg.provider_type,
        base_url=cfg.base_url,
        api_key_masked=mask_key(decrypt_secret(cfg.api_key_enc)),
        model_name=cfg.model_name,
        url_mode=cfg.url_mode or "base",
        is_valid=bool(cfg.is_valid),
        updated_at=cfg.updated_at,
    )


@router.get("", response_model=ApiResponse)
def list_model_configs(db: Session = Depends(get_db)) -> ApiResponse:
    configs = db.scalars(select(ModelConfig).order_by(ModelConfig.capability)).all()
    return ApiResponse(data=[_to_out(c) for c in configs])


@router.put("/{capability}", response_model=ApiResponse)
def upsert_model_config(
    capability: str,
    payload: ModelConfigUpsert,
    db: Session = Depends(get_db),
) -> ApiResponse:
    if capability not in CAPABILITIES:
        raise ApiError(status_code=404, code=404, message=f"未知的能力类型：{capability}")

    cfg = db.scalar(select(ModelConfig).where(ModelConfig.capability == capability))
    if cfg is None:
        cfg = ModelConfig(capability=capability)
        db.add(cfg)

    if payload.api_key:
        cfg.api_key_enc = encrypt_secret(payload.api_key)
    elif not cfg.api_key_enc:
        raise ApiError(status_code=422, code=422, message="必须提供 API Key")
    cfg.provider_type = payload.provider_type
    cfg.base_url = payload.base_url
    cfg.model_name = payload.model_name
    cfg.url_mode = payload.url_mode
    cfg.is_valid = 0
    db.commit()
    db.refresh(cfg)
    return ApiResponse(data=_to_out(cfg))


@router.post("/test", response_model=ApiResponse)
def test_model_config(payload: ModelConfigTest) -> ApiResponse:
    if payload.capability not in CAPABILITIES:
        raise ApiError(status_code=404, code=404, message=f"未知的能力类型：{payload.capability}")

    builder = _build(
        capability=payload.capability,
        provider_type=payload.provider_type,
        base_url=payload.base_url,
        api_key=payload.api_key,
        model_name=payload.model_name,
        url_mode=payload.url_mode,
    )
    try:
        ok = builder.test_connection()
    except ProviderError as exc:
        return ApiResponse(code=1, message=str(exc), data={"ok": False})
    return ApiResponse(data={"ok": ok})


@router.post("/{capability}/test", response_model=ApiResponse)
def test_saved_model_config(
    capability: str,
    db: Session = Depends(get_db),
) -> ApiResponse:
    cfg = db.scalar(select(ModelConfig).where(ModelConfig.capability == capability))
    if cfg is None:
        raise ApiError(status_code=404, code=404, message=f"{capability} 能力未配置")
    provider = _build(
        capability=capability,
        provider_type=cfg.provider_type,
        base_url=cfg.base_url,
        api_key=decrypt_secret(cfg.api_key_enc),
        model_name=cfg.model_name,
        url_mode=cfg.url_mode or "base",
    )
    try:
        ok = provider.test_connection()
    except ProviderError as exc:
        return ApiResponse(code=1, message=str(exc), data={"ok": False})
    if ok:
        cfg.is_valid = 1
        db.commit()
    return ApiResponse(data={"ok": ok})
