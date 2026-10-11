from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.recovery import RecoveryStatus
from app.models.approval import ApprovalDecision
from app.schemas.user import UserResponse


class RecoveryRequestCreate(BaseModel):
    reason: str


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    custodian_id: str
    decision: ApprovalDecision
    comment: Optional[str] = None
    created_at: datetime
    custodian_name: Optional[str] = None


class ApprovalCreate(BaseModel):
    comment: Optional[str] = None


class RecoveryRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    backup_id: str
    requester_id: str
    reason: str
    status: RecoveryStatus
    created_at: datetime
    expires_at: datetime
    completed_at: Optional[datetime] = None
    approvals: List[ApprovalResponse] = []
    approval_count: int = 0
    required_approvals: int = 2
    is_restorable: bool = False
    original_filename: Optional[str] = None
