from datetime import datetime

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class AudioAsset(Base):
    __tablename__ = "audio_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    storyboard_id: Mapped[int | None] = mapped_column(ForeignKey("storyboards.id"))
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    emotion: Mapped[str | None] = mapped_column(String)
    volume: Mapped[float] = mapped_column(Float, default=1.0)
    align_shot: Mapped[int | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
