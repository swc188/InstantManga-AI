import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database import SessionLocal
from app.main import app
from app.models import ModelConfig
from app.providers.openai_compatible import OpenAICompatibleBase

from .fake_client import FakeClient

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_model_configs():
    with SessionLocal() as db:
        db.execute(delete(ModelConfig))
        db.commit()
    yield


def test_upsert_and_list_config(monkeypatch):
    resp = client.put(
        "/api/model-config/text",
        json={
            "provider_type": "openai_compatible",
            "base_url": "https://x.test/v1",
            "api_key": "sk-abcdefgh1234",
            "model_name": "gpt-4o-mini",
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["capability"] == "text"
    assert data["api_key_masked"] == "sk-a****1234"
    assert data["is_valid"] is False

    listed = client.get("/api/model-config").json()["data"]
    assert any(c["capability"] == "text" for c in listed)
    text_cfg = next(c for c in listed if c["capability"] == "text")
    assert "abcdefgh" not in text_cfg["api_key_masked"]


def test_upsert_requires_key_when_new_config():
    resp = client.put(
        "/api/model-config/tts",
        json={
            "base_url": "https://x.test/v1",
            "api_key": "",
            "model_name": "m",
        },
    )
    assert resp.status_code == 422


def test_upsert_unknown_capability():
    resp = client.put(
        "/api/model-config/video",
        json={"base_url": "u", "api_key": "k", "model_name": "m"},
    )
    assert resp.status_code == 404


def test_test_endpoint_ok(monkeypatch):
    def handler(method, url, **kw):
        return FakeClient_ok()

    def FakeClient_ok():
        from .fake_client import FakeResponse

        return FakeResponse(status_code=200, json={"data": []})

    monkeypatch.setattr(
        OpenAICompatibleBase,
        "_client",
        lambda self: FakeClient(handler),
    )
    resp = client.post(
        "/api/model-config/test",
        json={
            "capability": "text",
            "provider_type": "openai_compatible",
            "base_url": "https://x.test/v1",
            "api_key": "k",
            "model_name": "m",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["ok"] is True


def test_test_endpoint_failure_returns_ok_false(monkeypatch):
    def handler(method, url, **kw):
        from .fake_client import FakeResponse

        return FakeResponse(status_code=401, json={})

    monkeypatch.setattr(
        OpenAICompatibleBase,
        "_client",
        lambda self: FakeClient(handler),
    )
    resp = client.post(
        "/api/model-config/test",
        json={
            "capability": "text",
            "base_url": "https://x.test/v1",
            "api_key": "bad",
            "model_name": "m",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["code"] == 1
    assert resp.json()["data"]["ok"] is False


def test_saved_config_test_marks_valid(monkeypatch):
    def handler(method, url, **kw):
        from .fake_client import FakeResponse

        return FakeResponse(status_code=200, json={"data": []})

    monkeypatch.setattr(
        OpenAICompatibleBase,
        "_client",
        lambda self: FakeClient(handler),
    )
    client.put(
        "/api/model-config/image",
        json={
            "provider_type": "jimeng",
            "base_url": "https://x.test/v1",
            "api_key": "k-image",
            "model_name": "m",
        },
    )
    resp = client.post("/api/model-config/image/test")
    assert resp.json()["data"]["ok"] is True

    listed = client.get("/api/model-config").json()["data"]
    img_cfg = next(c for c in listed if c["capability"] == "image")
    assert img_cfg["is_valid"] is True
