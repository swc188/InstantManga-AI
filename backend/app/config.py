from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_prefix="ACD_",
        extra="ignore",
    )

    app_name: str = "AI Comic Drama Studio"
    debug: bool = True
    api_prefix: str = "/api"
    database_url: str = f"sqlite:///{BASE_DIR / 'media' / 'studio.db'}"
    media_root: Path = BASE_DIR / "media"
    cors_origins: list[str] = ["http://localhost:5173"]
    default_model_base_url: str = "https://agnes-ai.cn"


@lru_cache
def get_settings() -> Settings:
    return Settings()
