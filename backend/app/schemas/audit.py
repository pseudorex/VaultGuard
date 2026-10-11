from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_id: Optional[str] = None
    action: str
    target_type: str
    target_id: Optional[str] = None
    outcome: str
    timestamp: datetime
    previous_hash: str
    event_hash: str
    safe_metadata_json: Optional[str] = None
    actor_name: Optional[str] = None


class AuditChainVerificationResponse(BaseModel):
    is_valid: bool
    total_events: int
    checked_at: datetime
    broken_event_id: Optional[str] = None
    message: str
    genesis_hash: str
    latest_hash: Optional[str] = None
