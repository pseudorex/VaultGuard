import json
import hashlib
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy import select, asc
from sqlalchemy.orm import Session
from app.models.audit_event import AuditEvent
from app.models.user import User

GENESIS_HASH = "0" * 64


def format_timestamp(dt: datetime) -> str:
    """Standardize datetime to UTC string for deterministic hash computation."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    # Format down to second precision to avoid microsecond sqlite serialization nuances
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def calculate_event_hash(
    previous_hash: str,
    actor_id: Optional[str],
    action: str,
    target_type: str,
    target_id: Optional[str],
    outcome: str,
    timestamp_str: str,
    safe_metadata_json: Optional[str],
) -> str:
    """Compute deterministic SHA-256 hash for an audit event."""
    canonical_repr = (
        f"{previous_hash}|"
        f"{actor_id or ''}|"
        f"{action}|"
        f"{target_type}|"
        f"{target_id or ''}|"
        f"{outcome}|"
        f"{timestamp_str}|"
        f"{safe_metadata_json or ''}"
    )
    return hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest()


class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        action: str,
        target_type: str,
        outcome: str,
        actor_id: Optional[str] = None,
        target_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> AuditEvent:
        """Append a new tamper-evident, hash-chained audit event to the ledger."""
        # Get the latest audit event to link previous_hash
        latest_event = (
            db.execute(select(AuditEvent).order_by(AuditEvent.timestamp.desc(), AuditEvent.id.desc()))
            .scalars()
            .first()
        )
        previous_hash = latest_event.event_hash if latest_event else GENESIS_HASH

        now = datetime.now(timezone.utc)
        timestamp_str = format_timestamp(now)
        metadata_json = json.dumps(metadata, sort_keys=True) if metadata else None

        event_hash = calculate_event_hash(
            previous_hash=previous_hash,
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            outcome=outcome,
            timestamp_str=timestamp_str,
            safe_metadata_json=metadata_json,
        )

        event = AuditEvent(
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            outcome=outcome,
            timestamp=now,
            previous_hash=previous_hash,
            event_hash=event_hash,
            safe_metadata_json=metadata_json,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def get_events(
        db: Session, skip: int = 0, limit: int = 100
    ) -> List[dict]:
        """Fetch audit events with actor names, ordered by newest first."""
        events = (
            db.execute(
                select(AuditEvent)
                .order_by(AuditEvent.timestamp.desc(), AuditEvent.id.desc())
                .offset(skip)
                .limit(limit)
            )
            .scalars()
            .all()
        )

        result = []
        for ev in events:
            actor_name = None
            if ev.actor_id:
                user = db.get(User, ev.actor_id)
                if user:
                    actor_name = user.display_name
            
            result.append({
                "id": ev.id,
                "actor_id": ev.actor_id,
                "actor_name": actor_name,
                "action": ev.action,
                "target_type": ev.target_type,
                "target_id": ev.target_id,
                "outcome": ev.outcome,
                "timestamp": ev.timestamp,
                "previous_hash": ev.previous_hash,
                "event_hash": ev.event_hash,
                "safe_metadata_json": ev.safe_metadata_json,
            })
        return result

    @staticmethod
    def verify_chain(db: Session) -> Tuple[bool, int, Optional[str], str, Optional[str]]:
        """
        Verify the complete cryptographic hash chain of all audit events.
        Returns: (is_valid, total_events, broken_event_id_if_any, message, latest_hash)
        """
        events = (
            db.execute(select(AuditEvent).order_by(asc(AuditEvent.timestamp), asc(AuditEvent.id)))
            .scalars()
            .all()
        )

        total_events = len(events)
        if total_events == 0:
            return True, 0, None, "Audit ledger is empty (valid).", None

        expected_prev_hash = GENESIS_HASH
        latest_hash = None

        for idx, ev in enumerate(events):
            # Check 1: Previous hash link
            if ev.previous_hash != expected_prev_hash:
                return (
                    False,
                    total_events,
                    ev.id,
                    f"Hash link broken at event {idx + 1} (ID: {ev.id}). Expected previous hash {expected_prev_hash[:12]}..., found {ev.previous_hash[:12]}...",
                    latest_hash,
                )

            # Check 2: Content integrity
            timestamp_str = format_timestamp(ev.timestamp)
            computed_hash = calculate_event_hash(
                previous_hash=ev.previous_hash,
                actor_id=ev.actor_id,
                action=ev.action,
                target_type=ev.target_type,
                target_id=ev.target_id,
                outcome=ev.outcome,
                timestamp_str=timestamp_str,
                safe_metadata_json=ev.safe_metadata_json,
            )

            if computed_hash != ev.event_hash:
                return (
                    False,
                    total_events,
                    ev.id,
                    f"Event content hash mismatch at event {idx + 1} (ID: {ev.id}). Data has been modified!",
                    latest_hash,
                )

            expected_prev_hash = ev.event_hash
            latest_hash = ev.event_hash

        return True, total_events, None, "Audit log hash chain successfully verified. No tampering detected.", latest_hash
