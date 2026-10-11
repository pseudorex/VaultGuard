from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.backup import Backup
from app.crypto.secret_sharing import combine_shares
from app.crypto.encryption import verify_ciphertext_integrity
from app.storage.local_storage import LocalStorageManager
from app.services.backup_service import BackupService
from app.services.audit_service import AuditService


class IntegrityService:
    @staticmethod
    def verify_backup(
        db: Session,
        backup_id: str,
        user: User
    ) -> dict:
        """
        Perform a controlled server-side cryptographic integrity verification:
        Reconstruct DEK from 2 shares in memory, verify AES-GCM ciphertext authentication tag.
        """
        backup = BackupService.get_backup_by_id(db, backup_id, user)
        now = datetime.now(timezone.utc)

        try:
            # Read 2 shares (indexes 1 and 2)
            shares = LocalStorageManager.read_key_shares(backup_id, [1, 2])
            if len(shares) < 2:
                raise ValueError("Insufficient key shares available in storage for verification")

            # Reconstruct DEK in memory
            dek = combine_shares(shares)

            # Read ciphertext
            container_bytes = LocalStorageManager.read_ciphertext(backup_id)

            # Verify integrity
            is_valid = verify_ciphertext_integrity(container_bytes, dek)
        except Exception:
            is_valid = False

        status_str = "VERIFIED" if is_valid else "TAMPERED_OR_UNVERIFIABLE"
        outcome_str = "SUCCESS" if is_valid else "TAMPERED"
        message_str = (
            "Cryptographic verification successful: Ciphertext and authentication tags are intact."
            if is_valid
            else "INTEGRITY VIOLATION DETECTED: Ciphertext payload or metadata has been altered or corrupted!"
        )

        AuditService.log_event(
            db=db,
            actor_id=user.id,
            action="BACKUP_INTEGRITY_VERIFIED",
            target_type="BACKUP",
            target_id=backup.id,
            outcome=outcome_str,
            metadata={
                "status": status_str,
                "algorithm": backup.algorithm,
                "is_valid": is_valid,
            }
        )

        return {
            "backup_id": backup.id,
            "status": status_str,
            "is_valid": is_valid,
            "algorithm": backup.algorithm,
            "checked_at": now,
            "message": message_str,
        }
