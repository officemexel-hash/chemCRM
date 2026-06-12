from datetime import datetime

from pydantic import BaseModel, Field


class BulkImportJobRead(BaseModel):
    id: str
    filename: str
    original_filename: str | None
    total_rows: int
    valid_rows: int
    invalid_rows: int
    status: str
    error_details: dict | None
    created_at: datetime
    items: list["BulkImportItemRead"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class BulkImportItemRead(BaseModel):
    id: str
    job_id: str
    row_number: int
    cas_raw: str
    cas_valid: bool
    substance_id: str | None
    status: str
    error_message: str | None

    model_config = {"from_attributes": True}


BulkImportJobRead.model_rebuild()
