from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.routes import script as script_routes
from app.database import SessionLocal
from app.main import app
from app.models import Character, Scene

client = TestClient(app)

RAW_SCRIPT = (
    "【开头】三年后，她带着秘密归来，站在大厦前。\n"
    "【冲突】他却早已订婚，而新娘竟是她最好的朋友。\n"
    "【结尾】她转身离开，嘴角却扬起一抹微笑。"
)


class FakeProvider:
    def generate(self, prompt, system=None, **kw):
        if "抽取" in prompt:
            return (
                '{"characters":[{"name":"男主","description":"黑发白衬衫"}],'
                '"scenes":[{"name":"总裁办公室"}]}'
            )
        return RAW_SCRIPT

    def rewrite(self, text, instruction):
        return RAW_SCRIPT


def make_project():
    return client.post("/api/projects", json={"title": "P"}).json()["data"]["id"]


def patch_provider(monkeypatch):
    monkeypatch.setattr(script_routes, "get_text_provider", lambda db: FakeProvider())


def test_generate_script_saves_structure_and_beats(monkeypatch):
    patch_provider(monkeypatch)
    pid = make_project()
    resp = client.post(
        f"/api/projects/{pid}/script/generate",
        json={"genre": "霸总", "theme": "逆袭"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["structure"]["opening"]
    assert data["structure"]["conflict"]
    assert data["structure"]["ending"]
    assert isinstance(data["beats"], list) and len(data["beats"]) >= 1
    assert data["content"]
    assert isinstance(data["awkward"], list)


def test_get_script_after_generate(monkeypatch):
    patch_provider(monkeypatch)
    pid = make_project()
    client.post(f"/api/projects/{pid}/script/generate", json={"genre": "霸总"})
    resp = client.get(f"/api/projects/{pid}/script")
    assert resp.status_code == 200
    assert resp.json()["data"]["content"]


def test_get_script_without_generation_404():
    pid = make_project()
    resp = client.get(f"/api/projects/{pid}/script")
    assert resp.status_code == 404


def test_rewrite_script(monkeypatch):
    patch_provider(monkeypatch)
    pid = make_project()
    client.post(f"/api/projects/{pid}/script/generate", json={"genre": "霸总"})
    resp = client.post(
        f"/api/projects/{pid}/script/rewrite",
        json={"instruction": "增加反转"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["structure"]["ending"]


def test_save_script_manual(monkeypatch):
    patch_provider(monkeypatch)
    pid = make_project()
    resp = client.put(
        f"/api/projects/{pid}/script",
        json={
            "content": "这是手动保存的剧本内容，包含完整的开头交代、中间的冲突反转以及结尾的悬念设置，讲述一个完整流畅的故事，篇幅足够长以便通过长度校验。",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["beats"]


def test_save_script_too_short_rejected():
    pid = make_project()
    resp = client.put(f"/api/projects/{pid}/script", json={"content": "太短"})
    assert resp.status_code == 422


def test_extract_entities_registers_character_and_scene(monkeypatch):
    patch_provider(monkeypatch)
    pid = make_project()
    client.post(f"/api/projects/{pid}/script/generate", json={"genre": "霸总"})
    resp = client.post(f"/api/projects/{pid}/script/extract")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["characters"]
    assert data["scenes"]

    with SessionLocal() as db:
        assert db.scalar(
            select(Character).where(Character.project_id == pid)
        ) is not None
        assert db.scalar(select(Scene).where(Scene.project_id == pid)) is not None


def test_generate_without_text_model_returns_400(monkeypatch):
    def no_provider(db):
        from app.core.errors import ApiError

        raise ApiError(400, 400, "文本模型未配置或未通过连通性测试")

    monkeypatch.setattr(script_routes, "get_text_provider", no_provider)
    pid = make_project()
    resp = client.post(
        f"/api/projects/{pid}/script/generate",
        json={"genre": "霸总"},
    )
    assert resp.status_code == 400
