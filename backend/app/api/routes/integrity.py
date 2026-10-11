from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.backup import BackupVerifyResponse
from app.services.integrity_service import IntegrityService
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/integrity", tags=["Integrity Verification"])


@router.post("/verify/{backup_id}", response_model=BackupVerifyResponse)
def verify_backup_integrity(
    backup_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Perform integrity verification on a specific backup."""
    return IntegrityService.verify_backup(db=db, backup_id=backup_id, user=current_user)
