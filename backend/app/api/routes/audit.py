from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.audit import AuditLog
from app.db.session import get_db


router = APIRouter(prefix="/audit-log", tags=["audit"])


@router.get("")
def list_audit_log(db: Session = Depends(get_db)) -> list[dict]:
    entries = list(db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(250)))
    return [
        {
            "id": entry.id,
            "actor_id": entry.actor_id,
            "actor_type": entry.actor_type,
            "action": entry.action,
            "object_type": entry.object_type,
            "object_id": entry.object_id,
            "details": entry.details,
            "created_at": entry.created_at,
        }
        for entry in entries
    ]
