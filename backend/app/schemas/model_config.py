from datetime import datetime

from pydantic import BaseModel, Field


class ModelConfigOut(BaseModel):
    capability: str
    provider_type: str
    base_url: str
    api_key_masked: str
    model_name: str
    url_mode: str
    is_valid: bool
    updated_at: datetime


class ModelConfigUpsert(BaseModel):
    provider_type: str = "openai_compatible"
    base_url: str
    api_key: str | None = None
    model_name: str
    endpoint_url: str | None = None
    url_mode: str = "base"


class ModelConfigTest(BaseModel):
    capability: str
    provider_type: str = "openai_compatible"
    base_url: str
    api_key: str
    model_name: str
    url_mode: str = "base"


CAPABILITIES = ("text", "image", "tts", "video")


def mask_key(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}****{key[-4:]}"
