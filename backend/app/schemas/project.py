from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    title: str
    genre: str | None = None


class ProjectUpdate(BaseModel):
    title: str | None = None
    genre: str | None = None
    status: str | None = None


class ProjectOut(BaseModel):
    id: int
    title: str
    genre: str | None
    status: str
    created_at: datetime
    updated_at: datetime
