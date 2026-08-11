from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StoryboardBase(BaseModel):
    scene_desc: str
    shot_type: str
    camera_angle: Optional[str] = None
    dialogue: Optional[str] = None
    emotion: Optional[str] = None
    duration: float = 1.8


class StoryboardGenerateRequest(BaseModel):
    content: str


class StoryboardOut(StoryboardBase):
    id: int
    project_id: int
    shot_no: int
    created_at: datetime

    model_config = {"from_attributes": True}


class StoryboardUpdate(BaseModel):
    id: int
    scene_desc: Optional[str] = None
    shot_type: Optional[str] = None
    camera_angle: Optional[str] = None
    dialogue: Optional[str] = None
    emotion: Optional[str] = None
    duration: Optional[float] = None


class TransitionIssue(BaseModel):
    from_shot: int
    to_shot: int
    reason: str
    type: str = "shot_type_jump"


class StoryboardValidation(BaseModel):
    uncovered_dialogues: list[str] = []
    transition_issues: list[TransitionIssue] = []
