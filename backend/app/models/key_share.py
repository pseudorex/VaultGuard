import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class KeyShare(Base):
    __tablename__ = "key_shares"
    __table_args__ = (
        UniqueConstraint("backup_id", "share_index", name="uq_backup_share_index"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    backup_id: Mapped[str] = mapped_column(String(36), ForeignKey("backups.id", ondelete="CASCADE"), nullable=False, index=True)
    share_index: Mapped[int] = mapped_column(Integer, nullable=False)
    protected_share_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    backup = relationship("Backup", back_populates="shares")
