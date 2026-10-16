from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.core import Utc


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ColumnOut(BaseModel):
    name: str
    type: str
    required: bool
    condition: str | None
    allowed: list[str] | None
    reference: str | None
    description: str
    example: str


class TemplateOut(BaseModel):
    template_id: str
    name: str
    format: str
    target: str
    key: str
    order: int
    available: bool
    channel: str
    phase: str | None
    description: str
    depends_on: list[str]
    record_count: int | None
    prerequisites_met: bool
    missing_prerequisites: list[str]
    columns: list[ColumnOut]


class ImportFileOut(ORMModel):
    import_file_id: int
    file_name: str
    relative_path: str
    checksum: str
    file_type: str
    size_bytes: int
    template_id: str | None
    template_source: str | None
    sheet_name: str | None
    status: str
    file_error: str | None
    rows_total: int
    rows_valid: int
    rows_invalid: int
    rows_new: int
    rows_update: int
    rows_unchanged: int
    rows_loaded: int
    error_count: int
    warning_count: int
    duplicate_of_batch: str | None = None


class ImportBatchOut(ORMModel):
    batch_id: str
    batch_type: str
    source: str
    uploaded_by: str | None
    status: str
    options: dict
    created_at: Utc | None
    started_at: Utc | None
    validated_at: Utc | None
    completed_at: Utc | None
    total_files: int
    successful_files: int
    failed_files: int
    total_records: int
    successful_records: int
    failed_records: int
    warning_count: int
    error_message: str | None


class ImportBatchDetail(ImportBatchOut):
    files: list[ImportFileOut]
    progress: dict | None


class ResetStatusOut(ORMModel):
    """Whether a reset is running, read from the reset lock (G1.32), and how the last one ended.

    `batch` is the running reset's seed batch, or null when idle. Its own status is *not* the signal:
    it reads Completed once the seed is loaded, long before the reset has finished (CR-53, TR-65).
    """
    in_progress: bool
    batch: ImportBatchOut | None
    stage: str | None = None
    acquired_at: Utc | None = None
    released_at: Utc | None = None
    last_outcome: str | None = None
    last_reason: str | None = None


class ImportIssueOut(ORMModel):
    issue_id: int
    import_file_id: int
    stage: str
    severity: str
    sheet: str | None
    row_number: int | None
    column_name: str | None
    error_type: str
    message: str
    original_value: str | None


class FileTemplateUpdate(BaseModel):
    template_id: str | None
