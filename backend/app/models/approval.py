import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Enum, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ApprovalDecision(str, enum.Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class Approval(Base):
    __tablename__ = "approvals"
    __table_args__ = (
        UniqueConstraint("recovery_request_id", "custodian_id", name="uq_request_custodian"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recovery_request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("recovery_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    custodian_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    decision: Mapped[ApprovalDecision] = mapped_column(Enum(ApprovalDecision), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    recovery_request = relationship("RecoveryRequest", back_populates="approvals")
    custodian = relationship("User", back_populates="approvals")
