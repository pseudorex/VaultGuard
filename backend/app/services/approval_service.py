from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.errors import (
    BadRequestException,
    NotFoundException,
    ForbiddenException,
    ConflictException
)
from app.models.user import User, UserRole
from app.models.recovery import RecoveryRequest, RecoveryStatus
from app.models.approval import Approval, ApprovalDecision
from app.services.audit_service import AuditService


class ApprovalService:
    @staticmethod
    def process_approval(
        db: Session,
        request_id: str,
        custodian: User,
        decision: ApprovalDecision,
        comment: str | None = None
    ) -> Approval:
        """Record custodian approval or rejection for a recovery request and trigger state transitions."""
        # 1. Role verification
        if custodian.role not in (UserRole.CUSTODIAN, UserRole.ADMIN):
            raise ForbiddenException("Only authorized Custodians can approve or reject recovery requests")

        # 2. Get recovery request
        request = db.get(RecoveryRequest, request_id)
        if not request:
            raise NotFoundException("Recovery request not found")

        if request.status != RecoveryStatus.PENDING:
            raise BadRequestException(f"Cannot vote on recovery request with status '{request.status.value}'")

        # 3. Check expiration
        now = datetime.now(timezone.utc)
        if request.expires_at.replace(tzinfo=timezone.utc) < now:
            request.status = RecoveryStatus.EXPIRED
            db.commit()
            raise BadRequestException("This recovery request has expired")

        # 4. Check for duplicate approval by same custodian
        existing_approval = db.execute(
            select(Approval).where(
                Approval.recovery_request_id == request_id,
                Approval.custodian_id == custodian.id
            )
        ).scalar_one_or_none()

        if existing_approval:
            raise ConflictException("You have already submitted a decision for this recovery request")

        # 5. Prevent owner from approving their own recovery request as a custodian (separation of duty)
        if request.requester_id == custodian.id:
            raise ForbiddenException("A requester cannot approve their own recovery request")

        # 6. Create Approval record
        approval = Approval(
            recovery_request_id=request_id,
            custodian_id=custodian.id,
            decision=decision,
            comment=comment.strip() if comment else None,
            created_at=now,
        )
        db.add(approval)
        db.flush()

        # 7. Evaluate State Transition
        if decision == ApprovalDecision.REJECT:
            request.status = RecoveryStatus.REJECTED
        elif decision == ApprovalDecision.APPROVE:
            # Count total APPROVE approvals
            approvals = db.execute(
                select(Approval).where(
                    Approval.recovery_request_id == request_id,
                    Approval.decision == ApprovalDecision.APPROVE
                )
            ).scalars().all()

            if len(approvals) >= 2:
                request.status = RecoveryStatus.APPROVED

        db.commit()
        db.refresh(approval)

        # 8. Log Audit Event
        AuditService.log_event(
            db=db,
            actor_id=custodian.id,
            action=f"CUSTODIAN_{decision.value}",
            target_type="RECOVERY_REQUEST",
            target_id=request_id,
            outcome="SUCCESS",
            metadata={
                "decision": decision.value,
                "new_request_status": request.status.value,
                "comment": comment,
            }
        )

        return approval
