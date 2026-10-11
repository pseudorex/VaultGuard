from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.backup import BackupStatus


class BackupBase(BaseModel):
    original_filename: str
    size_bytes: int
    algorithm: str
    payload_version: int
    status: BackupStatus


class BackupResponse(BackupBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    created_at: datetime
    shares_count: int = 3
    threshold: int = 2


class BackupVerifyResponse(BaseModel):
    backup_id: str
    status: str  # "VERIFIED" or "TAMPERED_OR_UNVERIFIABLE"
    is_valid: bool
    algorithm: str
    checked_at: datetime
    message: str
