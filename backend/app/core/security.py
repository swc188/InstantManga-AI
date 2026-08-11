import base64
import hashlib
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


def _machine_fingerprint() -> str:
    for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        p = Path(path)
        if p.exists():
            return p.read_text().strip()
    return os.uname().nodename


def get_fernet() -> Fernet:
    master = os.environ.get("ACD_MASTER_KEY", "")
    raw = f"{master}:{_machine_fingerprint()}".encode()
    key = base64.urlsafe_b64encode(hashlib.sha256(raw).digest())
    return Fernet(key)


def encrypt_secret(plain: str) -> str:
    return get_fernet().encrypt(plain.encode()).decode()


def decrypt_secret(token: str) -> str:
    try:
        return get_fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("无法解密配置密钥，密钥派生上下文可能已变化") from exc
