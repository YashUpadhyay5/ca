from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/")
def get_audit_trail(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves immutable audit trail for the CA organization."""
    logs = db.query(AuditLog).filter(AuditLog.org_id == current_user.org_id).order_by(AuditLog.timestamp.desc()).limit(100).all()
    return [
        {
            "id": log.id,
            "action": log.action,
            "entity_name": log.entity_name,
            "entity_id": log.entity_id,
            "old_value": log.old_value,
            "new_value": log.new_value,
            "details": log.details,
            "user_email": log.user.email if log.user else "System Worker",
            "timestamp": log.timestamp.isoformat()
        } for log in logs
    ]
