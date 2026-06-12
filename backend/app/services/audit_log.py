from sqlalchemy.orm import Session

from app.db.models.audit import AuditLog


class AuditLogService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def log(
        self,
        action: str,
        object_type: str | None = None,
        object_id: str | None = None,
        details: dict | None = None,
        actor_id: str | None = None,
        actor_type: str = "system",
    ) -> AuditLog:
        entry = AuditLog(
            actor_id=actor_id,
            actor_type=actor_type,
            action=action,
            object_type=object_type,
            object_id=object_id,
            details=details or {},
        )
        self.db.add(entry)
        self.db.flush()
        return entry
