from datetime import datetime

from pydantic import BaseModel


class ManualTaskPatch(BaseModel):
    status: str | None = None
    assigned_to: str | None = None
    title: str | None = None
    description: str | None = None


class ManualTaskRead(BaseModel):
    id: str
    task_type: str | None = None
    title: str | None = None
    description: str | None = None
    related_object_type: str | None = None
    related_object_id: str | None = None
    status: str | None = None
    assigned_to: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}
