from datetime import datetime

from pydantic import BaseModel


class ScriptGenerateRequest(BaseModel):
    genre: str
    theme: str = ""


class ScriptRewriteRequest(BaseModel):
    instruction: str


class ScriptSaveRequest(BaseModel):
    content: str
    structure: dict | None = None
    beats: list[dict] | None = None


class ScriptOut(BaseModel):
    id: int
    project_id: int
    content: str
    beats: list[dict]
    structure: dict
    awkward: list[dict] = []
    created_at: datetime


class EntityOut(BaseModel):
    characters: list[dict] = []
    scenes: list[dict] = []
    note: str | None = None
