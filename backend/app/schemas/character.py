from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CharacterCreate(BaseModel):
    name: str
    keywords: str
    portrait_style: str | None = None


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    keywords: Optional[str] = None
    portrait_path: Optional[str] = None
    portrait_style: Optional[str] = None


class CharacterOut(CharacterUpdate):
    id: int
    project_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SceneCreate(BaseModel):
    name: str
    desc_words: str


class SceneUpdate(BaseModel):
    name: Optional[str] = None
    desc_words: Optional[str] = None


class SceneOut(SceneUpdate):
    id: int
    project_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
