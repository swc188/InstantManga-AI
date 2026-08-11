from fastapi import APIRouter

from .routes import health, model_config

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(model_config.router)
