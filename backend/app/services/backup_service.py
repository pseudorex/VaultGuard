import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.errors import BadRequestException, NotFoundException, ForbiddenException
from app.models.user import User, UserRole
from app.models.backup import Backup, BackupStatus
from app.models.key_share import KeyShare
from app.crypto.encryption import generate_dek, encrypt_bytes
from app.crypto.secret_sharing import split_secret
from app.storage.local_storage import LocalStorageManager
from app.services.audit_service import AuditService


class BackupService:
    @staticmethod
    def create_backup(
        db: Session,
        owner: User,
        filename: str,
        file_bytes: bytes,
    ) -> Backup:
        """
        Encrypt file with AES-256-GCM, split DEK via 2-of-3 Shamir Secret Sharing,
        store ciphertext and shares in isolated paths, save metadata, and audit log.
        """
        if not file_bytes:
            raise BadRequestException("File cannot be empty")
        
        if len(file_bytes) > settings.max_upload_size_bytes:
            raise BadRequestException(
                f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
            )

        # Sanitize filename (prevent path traversal or malformed strings)
        safe_filename = filename.replace("\\", "/").split("/")[-1]
        if not safe_filename:
            safe_filename = "unnamed_backup.dat"

        backup_id = str(uuid.uuid4())
        
        # 1. Generate DEK & encrypt payload
        dek = generate_dek()
        nonce, container_bytes = encrypt_bytes(file_bytes, dek)
        
        # 2. Split DEK using 2-of-3 Shamir Secret Sharing
        shares = split_secret(dek, threshold=2, total_shares=3)
        
        # 3. Store ciphertext safely
        stored_path = LocalStorageManager.save_ciphertext(backup_id, container_bytes)
        
        # 4. Save metadata in DB
        backup = Backup(
            id=backup_id,
            owner_id=owner.id,
            original_filename=safe_filename,
            stored_path=stored_path,
            size_bytes=len(file_bytes),
            algorithm="AES-256-GCM",
            nonce_hex=nonce.hex(),
            payload_version=1,
            status=BackupStatus.ACTIVE,
        )
        db.add(backup)

        # 5. Store key shares in isolated storage files & record KeyShare DB entries
        for idx, share_str in enumerate(shares, start=1):
            share_path = LocalStorageManager.save_key_share(backup_id, idx, share_str)
            key_share_model = KeyShare(
                backup_id=backup_id,
                share_index=idx,
                protected_share_path=share_path,
            )
            db.add(key_share_model)

        db.commit()
        db.refresh(backup)

        # 6. Audit log
        AuditService.log_event(
            db=db,
            actor_id=owner.id,
            action="BACKUP_CREATED",
            target_type="BACKUP",
            target_id=backup.id,
            outcome="SUCCESS",
            metadata={
                "original_filename": backup.original_filename,
                "size_bytes": backup.size_bytes,
                "algorithm": backup.algorithm,
                "threshold": "2-of-3",
            }
        )

        return backup

    @staticmethod
    def get_user_backups(db: Session, user: User) -> List[Backup]:
        """List active backups owned by the current user (or all if admin)."""
        query = select(Backup).where(Backup.status == BackupStatus.ACTIVE)
        if user.role != UserRole.ADMIN:
            query = query.where(Backup.owner_id == user.id)
        
        query = query.order_by(Backup.created_at.desc())
        return list(db.execute(query).scalars().all())

    @staticmethod
    def get_backup_by_id(db: Session, backup_id: str, user: User) -> Backup:
        """Get a single backup by ID with ownership verification."""
        backup = db.get(Backup, backup_id)
        if not backup or backup.status == BackupStatus.DELETED:
            raise NotFoundException("Backup not found")
        
        if user.role != UserRole.ADMIN and backup.owner_id != user.id:
            raise ForbiddenException("You do not have access to this backup")
            
        return backup

    @staticmethod
    def delete_backup(db: Session, backup_id: str, user: User) -> None:
        """Delete a backup and wipe its storage files and key shares."""
        backup = BackupService.get_backup_by_id(db, backup_id, user)
        
        # Wipe storage files
        LocalStorageManager.delete_backup_files(backup_id)
        
        # Update DB status or remove
        backup.status = BackupStatus.DELETED
        db.commit()

        AuditService.log_event(
            db=db,
            actor_id=user.id,
            action="BACKUP_DELETED",
            target_type="BACKUP",
            target_id=backup_id,
            outcome="SUCCESS",
            metadata={"filename": backup.original_filename}
        )
