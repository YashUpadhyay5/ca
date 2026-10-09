from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentResponse(BaseModel):
    id: str
    org_id: str
    client_id: str
    file_name: str
    file_size: int
    file_hash: str
    page_count: int
    status: str
    is_scanned: bool
    error_message: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True

class DocumentUploadResponse(BaseModel):
    document_id: str
    file_name: str
    file_size: int
    page_count: int
    status: str
    message: str
    is_encrypted: bool = False
    password_required: bool = False

class ProcessDocumentRequest(BaseModel):
    password: Optional[str] = None

class ProcessingJobStatus(BaseModel):
    job_id: str
    document_id: str
    status: str  # QUEUED, READING_PDF, DETECTING_BANK, EXTRACTING, VALIDATING, COMPLETED, FAILED
    progress_percentage: int
    current_step: str
    pages_processed: int
    total_pages: int
    transactions_extracted: int
    high_confidence_pct: float
    review_required_count: int
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    statement_id: Optional[str] = None

