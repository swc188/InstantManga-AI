from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.main import app

client = TestClient(app)


def test_unified_error_format_on_validation_failure():
    router = APIRouter()

    class Body(BaseModel):
        title: str

    @router.post("/validate")
    def validate(body: Body):
        return body

    app.include_router(router)
    try:
        resp = client.post("/validate", json={})
    finally:
        app.router.routes = [
            r for r in app.router.routes if r.path != "/validate"
        ]
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == 422
    assert body["data"] is not None


def test_health_returns_ok():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "ok"


def test_unified_error_format_on_unknown_route():
    resp = client.get("/api/not-exist")
    assert resp.status_code == 404
    body = resp.json()
    assert body["code"] == 404
    assert "message" in body
    assert "data" in body


def test_openapi_schema_generated():
    resp = client.get("/api/openapi.json")
    assert resp.status_code == 200
    assert resp.json()["info"]["title"] == "AI Comic Drama Studio"
