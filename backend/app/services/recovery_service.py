import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.errors import (
    BadRequestException,
    NotFoundException,
    ForbiddenException,
    TamperDetectedException
)
from app.models.user import User, UserRole
from app.models.backup import Backup, BackupStatus
from app.models.recovery import RecoveryRequest, RecoveryStatus
from app.models.approval import Approval, ApprovalDecision
from app.crypto.secret_sharing import combine_shares
from app.crypto.encryption import decrypt_container
from app.storage.local_storage import LocalStorageManager
from app.services.audit_service import AuditService
from app.services.backup_service import BackupService


class RecoveryService:
    @staticmethod
    def create_recovery_request(
        db: Session,
        backup_id: str,
        user: User,
        reason: str
    ) -> RecoveryRequest:
        """Create a new recovery request for a backup."""
        backup = BackupService.get_backup_by_id(db, backup_id, user)
        
        if not reason or len(reason.strip()) < 3:
            raise BadRequestException("A valid reason of at least 3 characters is required for recovery")

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=settings.RECOVERY_REQUEST_TTL_HOURS)

        request = RecoveryRequest(
            id=str(uuid.uuid4()),
            backup_id=backup.id,
            requester_id=user.id,
            reason=reason.strip(),
            status=RecoveryStatus.PENDING,
            created_at=now,
            expires_at=expires_at,
        )
        db.add(request)
        db.commit()
        db.refresh(request)

        AuditService.log_event(
            db=db,
            actor_id=user.id,
            action="RECOVERY_REQUESTED",
            target_type="RECOVERY_REQUEST",
            target_id=request.id,
            outcome="SUCCESS",
            metadata={
                "backup_id": backup.id,
                "filename": backup.original_filename,
                "reason": reason,
            }
        )

        return request

    @staticmethod
    def get_requests(db: Session, user: User) -> List[dict]:
        """Fetch recovery requests relevant to the user."""
        query = select(RecoveryRequest).order_by(RecoveryRequest.created_at.desc())
        
        if user.role == UserRole.OWNER:
            query = query.where(RecoveryRequest.requester_id == user.id)
            
        requests = list(db.execute(query).scalars().all())
        
        # Format with approvals details and original filename
        result = []
        for req in requests:
            approvals_data = []
            approve_count = 0
            for app in req.approvals:
                custodian = db.get(User, app.custodian_id)
                approvals_data.append({
                    "id": app.id,
                    "custodian_id": app.custodian_id,
                    "custodian_name": custodian.display_name if custodian else "Custodian",
                    "decision": app.decision,
                    "comment": app.comment,
                    "created_at": app.created_at,
                })
                if app.decision == ApprovalDecision.APPROVE:
                    approve_count += 1

            backup = db.get(Backup, req.backup_id)
            original_filename = backup.original_filename if backup else "Unknown"

            result.append({
                "id": req.id,
                "backup_id": req.backup_id,
                "requester_id": req.requester_id,
                "reason": req.reason,
                "status": req.status,
                "created_at": req.created_at,
                "expires_at": req.expires_at,
                "completed_at": req.completed_at,
                "approvals": approvals_data,
                "approval_count": approve_count,
                "required_approvals": 2,
                "is_restorable": req.status == RecoveryStatus.APPROVED,
                "original_filename": original_filename,
            })
        return result

    @staticmethod
    def get_request_by_id(db: Session, request_id: str, user: User) -> dict:
        """Fetch a single recovery request."""
        req = db.get(RecoveryRequest, request_id)
        if not req:
            raise NotFoundException("Recovery request not found")

        if user.role == UserRole.OWNER and req.requester_id != user.id:
            raise ForbiddenException("You do not have access to this recovery request")

        approvals_data = []
        approve_count = 0
        for app in req.approvals:
            custodian = db.get(User, app.custodian_id)
            approvals_data.append({
                "id": app.id,
                "custodian_id": app.custodian_id,
                "custodian_name": custodian.display_name if custodian else "Custodian",
                "decision": app.decision,
                "comment": app.comment,
                "created_at": app.created_at,
            })
            if app.decision == ApprovalDecision.APPROVE:
                approve_count += 1

        backup = db.get(Backup, req.backup_id)
        original_filename = backup.original_filename if backup else "Unknown"

        return {
            "id": req.id,
            "backup_id": req.backup_id,
            "requester_id": req.requester_id,
            "reason": req.reason,
            "status": req.status,
            "created_at": req.created_at,
            "expires_at": req.expires_at,
            "completed_at": req.completed_at,
            "approvals": approvals_data,
            "approval_count": approve_count,
            "required_approvals": 2,
            "is_restorable": req.status == RecoveryStatus.APPROVED,
            "original_filename": original_filename,
        }

    @staticmethod
    def restore_backup(
        db: Session,
        request_id: str,
        user: User
    ) -> Tuple[str, bytes]:
        """
        Execute recovery restoration:
        1. Validate request is APPROVED and not expired.
        2. Validate requester ownership.
        3. Collect 2 key shares from isolated storage, reconstruct DEK in memory.
        4. Authenticate and decrypt AES-GCM ciphertext container.
        5. Mark request COMPLETED and log audit event.
        6. Return (original_filename, plaintext_bytes).
        """
        req = db.get(RecoveryRequest, request_id)
        if not req:
            raise NotFoundException("Recovery request not found")

        if user.role != UserRole.ADMIN and req.requester_id != user.id:
            raise ForbiddenException("Only the original requester can restore and download this file")

        if req.status != RecoveryStatus.APPROVED:
            raise BadRequestException(f"Recovery request cannot be restored in state '{req.status.value}'. Required state: 'APPROVED' with 2 custodian approvals.")

        now = datetime.now(timezone.utc)
        if req.expires_at.replace(tzinfo=timezone.utc) < now:
            req.status = RecoveryStatus.EXPIRED
            db.commit()
            raise BadRequestException("Recovery request has expired")

        backup = db.get(Backup, req.backup_id)
        if not backup or backup.status == BackupStatus.DELETED:
            raise NotFoundException("Associated backup is no longer available")

        # Reconstruct key from shares 1 and 2
        try:
            shares = LocalStorageManager.read_key_shares(backup.id, [1, 2])
            if len(shares) < 2:
                raise ValueError("Insufficient key shares available in storage")

            dek = combine_shares(shares)
            container_bytes = LocalStorageManager.read_ciphertext(backup.id)
            plaintext = decrypt_container(container_bytes, dek)
        except TamperDetectedException as e:
            req.status = RecoveryStatus.FAILED
            db.commit()
            AuditService.log_event(
                db=db,
                actor_id=user.id,
                action="RESTORE_FAILED_TAMPERED",
                target_type="RECOVERY_REQUEST",
                target_id=req.id,
                outcome="FAILURE",
                metadata={"error": str(e), "backup_id": backup.id}
            )
            raise e
        except Exception as e:
            req.status = RecoveryStatus.FAILED
            db.commit()
            AuditService.log_event(
                db=db,
                actor_id=user.id,
                action="RESTORE_FAILED_ERROR",
                target_type="RECOVERY_REQUEST",
                target_id=req.id,
                outcome="FAILURE",
                metadata={"error": str(e), "backup_id": backup.id}
            )
            raise BadRequestException(f"Failed to restore backup: {str(e)}")

        req.status = RecoveryStatus.COMPLETED
        req.completed_at = now
        db.commit()

        AuditService.log_event(
            db=db,
            actor_id=user.id,
            action="RESTORE_COMPLETED",
            target_type="RECOVERY_REQUEST",
            target_id=req.id,
            outcome="SUCCESS",
            metadata={
                "backup_id": backup.id,
                "original_filename": backup.original_filename,
                "restored_bytes": len(plaintext),
            }
        )

        return backup.original_filename, plaintext
