from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Storyboard(Base):
    __tablename__ = "storyboards"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    shot_no: Mapped[int] = mapped_column(Integer, nullable=False)
    scene_desc: Mapped[str] = mapped_column(Text, nullable=False)
    shot_type: Mapped[str] = mapped_column(String, nullable=False)
    camera_angle: Mapped[str | None] = mapped_column(String)
    dialogue: Mapped[str | None] = mapped_column(Text)
    emotion: Mapped[str | None] = mapped_column(String)
    duration: Mapped[float] = mapped_column(Float, default=1.8)
    image_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
