from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.backup import BackupResponse, BackupVerifyResponse
from app.schemas.recovery import RecoveryRequestCreate, RecoveryRequestResponse
from app.services.backup_service import BackupService
from app.services.integrity_service import IntegrityService
from app.services.recovery_service import RecoveryService
from app.models.user import User, UserRole
from app.api.deps import get_current_user

router = APIRouter(prefix="/backups", tags=["Backups"])


@router.post("", response_model=BackupResponse, status_code=status.HTTP_201_CREATED)
async def create_backup(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a file for secure threshold backup:
    Encrypts file with AES-256-GCM and splits the DEK into 3 Shamir shares (2-of-3 threshold).
    """
    file_bytes = await file.read()
    backup = BackupService.create_backup(
        db=db,
        owner=current_user,
        filename=file.filename or "unnamed_file",
        file_bytes=file_bytes,
    )
    return backup


@router.get("", response_model=List[BackupResponse])
def list_backups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all backups owned by the authenticated user."""
    return BackupService.get_user_backups(db=db, user=current_user)


@router.get("/{backup_id}", response_model=BackupResponse)
def get_backup(
    backup_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get safe metadata for a specific owned backup."""
    return BackupService.get_backup_by_id(db=db, backup_id=backup_id, user=current_user)


@router.delete("/{backup_id}")
def delete_backup(
    backup_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a backup and destroy its ciphertext and key shares."""
    BackupService.delete_backup(db=db, backup_id=backup_id, user=current_user)
    return {"message": "Backup and key shares successfully deleted"}


@router.post("/{backup_id}/verify", response_model=BackupVerifyResponse)
def verify_backup_integrity(
    backup_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cryptographic Integrity Verification:
    Reconstructs DEK from 2 shares in memory and validates AES-GCM tag against stored ciphertext.
    """
    return IntegrityService.verify_backup(db=db, backup_id=backup_id, user=current_user)


@router.post("/{backup_id}/recovery-requests", response_model=RecoveryRequestResponse, status_code=status.HTTP_201_CREATED)
def create_recovery_request(
    backup_id: str,
    request_in: RecoveryRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a recovery request for a backup."""
    req = RecoveryService.create_recovery_request(
        db=db,
        backup_id=backup_id,
        user=current_user,
        reason=request_in.reason,
    )
    return RecoveryService.get_request_by_id(db=db, request_id=req.id, user=current_user)
