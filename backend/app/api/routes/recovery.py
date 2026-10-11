from typing import List
import urllib.parse
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.recovery import (
    RecoveryRequestResponse,
    ApprovalCreate,
    ApprovalResponse,
)
from app.models.approval import ApprovalDecision
from app.models.user import User, UserRole
from app.api.deps import get_current_user, require_role
from app.services.recovery_service import RecoveryService
from app.services.approval_service import ApprovalService

router = APIRouter(prefix="/recovery-requests", tags=["Recovery & Restoration"])


@router.get("", response_model=List[RecoveryRequestResponse])
def list_recovery_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List recovery requests (filtered to owned backups for Owners, or all pending for Custodians)."""
    return RecoveryService.get_requests(db=db, user=current_user)


@router.get("/{request_id}", response_model=RecoveryRequestResponse)
def get_recovery_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get details of a specific recovery request."""
    return RecoveryService.get_request_by_id(db=db, request_id=request_id, user=current_user)


@router.post("/{request_id}/approve", response_model=ApprovalResponse)
def approve_recovery_request(
    request_id: str,
    approval_in: ApprovalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTODIAN)),
):
    """
    Custodian Approval:
    Submits an approval vote. When 2 distinct custodians approve, the request transitions to APPROVED.
    """
    approval = ApprovalService.process_approval(
        db=db,
        request_id=request_id,
        custodian=current_user,
        decision=ApprovalDecision.APPROVE,
        comment=approval_in.comment,
    )
    return {
        "id": approval.id,
        "custodian_id": approval.custodian_id,
        "custodian_name": current_user.display_name,
        "decision": approval.decision,
        "comment": approval.comment,
        "created_at": approval.created_at,
    }


@router.post("/{request_id}/reject", response_model=ApprovalResponse)
def reject_recovery_request(
    request_id: str,
    approval_in: ApprovalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTODIAN)),
):
    """Custodian Rejection: Submits a rejection vote and marks request REJECTED."""
    approval = ApprovalService.process_approval(
        db=db,
        request_id=request_id,
        custodian=current_user,
        decision=ApprovalDecision.REJECT,
        comment=approval_in.comment,
    )
    return {
        "id": approval.id,
        "custodian_id": approval.custodian_id,
        "custodian_name": current_user.display_name,
        "decision": approval.decision,
        "comment": approval.comment,
        "created_at": approval.created_at,
    }


@router.post("/{request_id}/restore")
def restore_backup_file(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Restore File from Approved Recovery Request:
    Reconstructs DEK from 2-of-3 Shamir shares, authenticates & decrypts ciphertext,
    and returns decrypted file download.
    """
    original_filename, plaintext_bytes = RecoveryService.restore_backup(
        db=db,
        request_id=request_id,
        user=current_user,
    )

    safe_filename = urllib.parse.quote(original_filename)
    return Response(
        content=plaintext_bytes,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}",
            "X-Restored-Filename": original_filename,
        },
    )
