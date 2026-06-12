from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.task import ManualTask
from app.db.session import get_db
from app.schemas.task import ManualTaskPatch, ManualTaskRead
from app.services.audit_log import AuditLogService


router = APIRouter(prefix="/manual-tasks", tags=["manual-tasks"])


@router.get("", response_model=list[ManualTaskRead])
def list_manual_tasks(db: Session = Depends(get_db)) -> list[ManualTask]:
    return list(db.scalars(select(ManualTask).order_by(ManualTask.created_at.desc())))


@router.patch("/{task_id}", response_model=ManualTaskRead)
def patch_manual_task(task_id: str, payload: ManualTaskPatch, db: Session = Depends(get_db)) -> ManualTask:
    task = db.get(ManualTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    AuditLogService(db).log("manual_task_updated", "manual_task", task.id, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(task)
    return task


@router.post("/{task_id}/complete", response_model=ManualTaskRead)
def complete_manual_task(task_id: str, db: Session = Depends(get_db)) -> ManualTask:
    task = db.get(ManualTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    task.status = "completed"
    task.completed_at = datetime.now(timezone.utc)
    AuditLogService(db).log("manual_task_completed", "manual_task", task.id)
    db.commit()
    db.refresh(task)
    return task
