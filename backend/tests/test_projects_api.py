from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_and_list_projects():
    resp = client.post(
        "/api/projects",
        json={"title": "霸总逆袭第一话", "genre": "霸总"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["title"] == "霸总逆袭第一话"
    assert data["genre"] == "霸总"
    assert data["status"] == "draft"
    project_id = data["id"]

    listed = client.get("/api/projects").json()["data"]
    assert any(p["id"] == project_id for p in listed)


def test_create_project_initializes_media_dirs(tmp_path, monkeypatch):
    import app.core.storage as storage_mod
    from app import config

    monkeypatch.setattr(config, "get_settings", lambda: type(
        "S", (), {"media_root": tmp_path}
    )())
    monkeypatch.setattr(storage_mod.config, "get_settings", config.get_settings)

    resp = client.post("/api/projects", json={"title": "T"})
    project_id = resp.json()["data"]["id"]
    for sub in ("characters", "shots", "audio", "exports"):
        assert (tmp_path / str(project_id) / sub).is_dir()


def test_get_missing_project_returns_404():
    resp = client.get("/api/projects/999999")
    assert resp.status_code == 404
    assert resp.json()["code"] == 404


def test_update_project():
    created = client.post("/api/projects", json={"title": "A"}).json()["data"]
    resp = client.put(
        f"/api/projects/{created['id']}",
        json={"title": "B", "status": "active"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["title"] == "B"
    assert data["status"] == "active"
