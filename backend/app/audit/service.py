import json
import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.database.models import AuditLogModel


class AuditService:
    @staticmethod
    def record_event(
        db: Session,
        event_type: str,
        action: str,
        entity_type: str,
        entity_id: str,
        actor: str = "system",
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLogModel:
        """
        Creates an immutable audit log record.
        """
        audit_entry = AuditLogModel(
            event_type=event_type,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=actor,
            details_json=json.dumps(details or {}),
            timestamp=datetime.datetime.utcnow(),
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry
