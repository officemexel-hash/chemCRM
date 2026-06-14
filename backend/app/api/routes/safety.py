from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.config import get_settings
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.safety import SafetyOverrideRead, SafetyOverrideUpdate
from app.services.audit_log import AuditLogService
from app.services.safety_override import SafetyOverrideService


router = APIRouter(prefix="/safety-override", tags=["safety"])


@router.get("", response_model=SafetyOverrideRead)
def get_safety_override(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> SafetyOverrideRead:
    return SafetyOverrideService(db, get_settings().app_env).get()


@router.put("", response_model=SafetyOverrideRead)
def update_safety_override(
    payload: SafetyOverrideUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> SafetyOverrideRead:
    service = SafetyOverrideService(db, get_settings().app_env)
    try:
        if payload.enabled:
            state = service.enable(payload, admin)
            AuditLogService(db).log(
                "safety_override_enabled",
                "settings",
                "safety_override",
                {
                    "mode": state.mode,
                    "enabled_by": admin.email,
                    "allowed_overrides": state.allowed_overrides,
                    "expires_at": state.expires_at.isoformat() if state.expires_at else None,
                },
                actor_id=admin.id,
                actor_type="user",
            )
        else:
            state = service.disable(admin, payload.reason)
            AuditLogService(db).log(
                "safety_override_disabled",
                "settings",
                "safety_override",
                {"enabled_by": admin.email},
                actor_id=admin.id,
                actor_type="user",
            )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    db.commit()
    return state
