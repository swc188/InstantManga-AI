from fastapi import APIRouter

from ...core.response import ApiResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ApiResponse)
def health_check() -> ApiResponse:
    return ApiResponse(data={"status": "ok"})
