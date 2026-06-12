from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.app_settings import AppSettings, AppSettingsRead
from app.services.app_settings import AppSettingsService, default_app_settings
from app.services.audit_log import AuditLogService


router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/defaults", response_model=AppSettings)
def get_default_settings() -> AppSettings:
    return default_app_settings()


@router.get("/app", response_model=AppSettingsRead)
def get_app_settings(db: Session = Depends(get_db)) -> AppSettingsRead:
    settings, updated_at = AppSettingsService(db).get_with_updated_at()
    return AppSettingsRead(**settings.model_dump(), updated_at=updated_at)


@router.put("/app", response_model=AppSettingsRead)
def update_app_settings(payload: AppSettings, db: Session = Depends(get_db)) -> AppSettingsRead:
    saved = AppSettingsService(db).save(payload)
    AuditLogService(db).log(
        "app_settings_updated",
        "settings",
        "app_settings",
        {
            "company_legal_name": saved.company.legal_name,
            "sender_email": str(saved.sender.email) if saved.sender.email else None,
            "controlled_questions": len(saved.controlled_questions),
            "response_playbook_rules": len(saved.response_playbook),
        },
    )
    db.commit()
    settings, updated_at = AppSettingsService(db).get_with_updated_at()
    return AppSettingsRead(**settings.model_dump(), updated_at=updated_at)
