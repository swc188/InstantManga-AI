import pytest

from app.core.security import decrypt_secret, encrypt_secret


def test_encrypt_decrypt_roundtrip(monkeypatch):
    monkeypatch.setenv("ACD_MASTER_KEY", "master-a")
    token = encrypt_secret("sk-123456789")
    assert token != "sk-123456789"
    assert decrypt_secret(token) == "sk-123456789"


def test_decrypt_fails_when_context_changes(monkeypatch):
    monkeypatch.setenv("ACD_MASTER_KEY", "master-a")
    token = encrypt_secret("top-secret")
    monkeypatch.setenv("ACD_MASTER_KEY", "master-b")
    with pytest.raises(ValueError, match="无法解密"):
        decrypt_secret(token)
