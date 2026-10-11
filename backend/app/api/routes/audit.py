from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.audit import AuditEventResponse, AuditChainVerificationResponse
from app.services.audit_service import AuditService
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/audit-events", tags=["Audit Ledger"])


@router.get("", response_model=List[AuditEventResponse])
def get_audit_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve chronologically chained audit log entries with safe metadata."""
    return AuditService.get_events(db=db, skip=skip, limit=limit)


@router.post("/verify-chain", response_model=AuditChainVerificationResponse)
def verify_audit_hash_chain(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cryptographic Hash Chain Verification:
    Iterates sequentially through the entire audit ledger to verify that each event's hash
    matches its canonical data and links unconditionally to the previous event's hash.
    """
    is_valid, total_events, broken_id, message, latest_hash = AuditService.verify_chain(db)
    return {
        "is_valid": is_valid,
        "total_events": total_events,
        "checked_at": datetime.now(timezone.utc),
        "broken_event_id": broken_id,
        "message": message,
        "genesis_hash": "0" * 64,
        "latest_hash": latest_hash,
    }
