import os
import uuid

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.app_settings import AppSettings, AppSettingsRead
from app.services.app_settings import AppSettingsService, default_app_settings
from app.services.audit_log import AuditLogService
from app.core.config import get_settings


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


@router.post("/app/logo", response_model=dict)
async def upload_logo(file: UploadFile, db: Session = Depends(get_db)) -> dict:
    if not file.content_type or not file.content_type.startswith("image/"):
        return {"error": "Only image files are accepted"}
    cfg = get_settings()
    os.makedirs(cfg.storage_path, exist_ok=True)
    ext = os.path.splitext(file.filename or "logo.png")[1] or ".png"
    filename = f"logo_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(cfg.storage_path, filename)
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    logo_url = f"/storage/{filename}"
    svc = AppSettingsService(db)
    current = svc.get()
    current.logo_url = logo_url
    svc.save(current)
    AuditLogService(db).log("logo_uploaded", "settings", "app_settings", {"logo_url": logo_url})
    db.commit()
    return {"logo_url": logo_url}
