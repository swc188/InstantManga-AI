from pathlib import Path

from .. import config

MEDIA_SUBDIRS = ("characters", "shots", "audio", "exports")


def ensure_project_media(project_id: int) -> Path:
    root: Path = config.get_settings().media_root / str(project_id)
    for sub in MEDIA_SUBDIRS:
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root
