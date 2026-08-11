from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class ShotAsset(Base):
    __tablename__ = "shot_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    storyboard_id: Mapped[int] = mapped_column(ForeignKey("storyboards.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    is_selected: Mapped[int] = mapped_column(Integer, default=0)
    style_score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
