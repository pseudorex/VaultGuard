import os
import uuid
from pathlib import Path
from typing import List, Optional
from app.core.config import settings
from app.core.errors import NotFoundException


class LocalStorageManager:
    @staticmethod
    def _sanitize_id(identifier: str) -> str:
        # Validate that the identifier is a valid UUID or safe alphanumeric string
        try:
            val = uuid.UUID(str(identifier))
            return str(val)
        except ValueError:
            # Strip any directory traversal characters
            safe = "".join(c for c in str(identifier) if c.isalnum() or c in "-_")
            if not safe:
                raise ValueError("Invalid identifier for storage")
            return safe

    @classmethod
    def save_ciphertext(cls, backup_id: str, payload_bytes: bytes) -> str:
        """Save encrypted container to isolated ciphertext directory."""
        safe_id = cls._sanitize_id(backup_id)
        file_path = settings.ciphertext_path / f"{safe_id}.enc"
        
        # Write atomically using a temporary file in the temp directory
        temp_file = settings.temp_path / f"temp_{safe_id}_{uuid.uuid4().hex}.tmp"
        with open(temp_file, "wb") as f:
            f.write(payload_bytes)
        
        os.replace(temp_file, file_path)
        return str(file_path.relative_to(settings.storage_path))

    @classmethod
    def read_ciphertext(cls, backup_id: str) -> bytes:
        """Read encrypted container from ciphertext directory."""
        safe_id = cls._sanitize_id(backup_id)
        file_path = settings.ciphertext_path / f"{safe_id}.enc"
        if not file_path.exists():
            raise NotFoundException("Ciphertext file not found in storage")
        
        with open(file_path, "rb") as f:
            return f.read()

    @classmethod
    def save_key_share(cls, backup_id: str, share_index: int, share_str: str) -> str:
        """Save a single key share to isolated shares directory."""
        safe_id = cls._sanitize_id(backup_id)
        file_path = settings.shares_path / f"{safe_id}_share_{share_index}.dat"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(share_str.strip())
            
        return str(file_path.relative_to(settings.storage_path))

    @classmethod
    def read_key_shares(cls, backup_id: str, share_indices: Optional[List[int]] = None) -> List[str]:
        """Read key shares for a backup."""
        safe_id = cls._sanitize_id(backup_id)
        shares: List[str] = []
        
        indices = share_indices or [1, 2, 3]
        for idx in indices:
            file_path = settings.shares_path / f"{safe_id}_share_{idx}.dat"
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        shares.append(content)
        return shares

    @classmethod
    def delete_backup_files(cls, backup_id: str) -> None:
        """Safely delete ciphertext and all corresponding share files."""
        safe_id = cls._sanitize_id(backup_id)
        
        # Delete ciphertext
        enc_file = settings.ciphertext_path / f"{safe_id}.enc"
        if enc_file.exists():
            try:
                enc_file.unlink()
            except OSError:
                pass
        
        # Delete shares
        for idx in range(1, 10):
            share_file = settings.shares_path / f"{safe_id}_share_{idx}.dat"
            if share_file.exists():
                try:
                    share_file.unlink()
                except OSError:
                    pass
