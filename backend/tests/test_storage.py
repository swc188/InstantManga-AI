from app.core.storage import MEDIA_SUBDIRS, ensure_project_media


def test_ensure_project_media_creates_subdirs(tmp_path, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "get_settings", lambda: type(
        "S", (), {"media_root": tmp_path}
    )())

    root = ensure_project_media(7)
    assert root == tmp_path / "7"
    for sub in MEDIA_SUBDIRS:
        assert (root / sub).is_dir()


def test_ensure_project_media_is_idempotent(tmp_path, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "get_settings", lambda: type(
        "S", (), {"media_root": tmp_path}
    )())

    first = ensure_project_media(1)
    second = ensure_project_media(1)
    assert first == second
