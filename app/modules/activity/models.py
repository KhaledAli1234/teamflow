from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.users.models import User


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    __table_args__ = (Index("ix_activity_entity", "entity_type", "entity_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=True
    )
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(50))
    entity_type: Mapped[str] = mapped_column(String(30))
    entity_id: Mapped[int] = mapped_column()
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    actor: Mapped["User | None"] = relationship(foreign_keys=[actor_id], lazy="selectin")