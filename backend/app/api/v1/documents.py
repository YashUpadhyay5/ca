import uuid
import fitz
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.user import User
from app.models.client import Client
from app.models.document import Document
from app.schemas.document import DocumentResponse, DocumentUploadResponse, ProcessingJobStatus, ProcessDocumentRequest
from app.core.storage import StorageManager
from app.workers.job_manager import JobManager
from app.extraction.pipeline import ExtractionPipeline
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    client_id: Optional[str] = Form(None),
    client_name: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Securely uploads bank statement PDF for a client, auto-provisioning client and detecting password encryption."""
    client = None
    if client_id and client_id.strip():
        client = db.query(Client).filter(Client.id == client_id.strip(), Client.org_id == current_user.org_id).first()

    if not client:
        # Check if an existing client exists in this org
        client = db.query(Client).filter(Client.org_id == current_user.org_id).first()

    if not client:
        # Auto-create first client
        name_to_use = client_name.strip() if client_name and client_name.strip() else "Client Account"
        client = Client(
            org_id=current_user.org_id,
            name=name_to_use,
            notes="Auto-created from bank statement upload"
        )
        db.add(client)
        db.commit()
        db.refresh(client)

    doc_id = str(uuid.uuid4())
    rel_path, sha256_hash, file_size = StorageManager.save_document(file, current_user.org_id, doc_id)
    abs_path = StorageManager.get_absolute_path(rel_path)

    # Inspect encryption
    is_encrypted = ExtractionPipeline.check_pdf_encryption(str(abs_path))
    password_required = False

    if is_encrypted:
        if password and password.strip():
            try:
                tdoc = fitz.open(str(abs_path))
                if tdoc.authenticate(password.strip()):
                    tdoc.close()
                    password_required = False
                else:
                    tdoc.close()
                    password_required = True
            except Exception:
                password_required = True
        else:
            password_required = True

    doc_status = "PASSWORD_REQUIRED" if password_required else "UPLOADED"

    doc = Document(
        id=doc_id,
        org_id=current_user.org_id,
        client_id=client.id,
        file_name=file.filename,
        storage_path=rel_path,
        file_size=file_size,
        file_hash=sha256_hash,
        page_count=0,
        status=doc_status
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "document_id": doc.id,
        "file_name": doc.file_name,
        "file_size": doc.file_size,
        "page_count": doc.page_count,
        "status": doc.status,
        "is_encrypted": is_encrypted,
        "password_required": password_required,
        "message": "PDF is password-protected. Please enter statement password to proceed." if password_required else "File uploaded successfully and verified."
    }

@router.post("/{document_id}/verify-password")
def verify_document_password(
    document_id: str,
    req: ProcessDocumentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verifies if the submitted password decrypts the uploaded statement."""
    doc = db.query(Document).filter(Document.id == document_id, Document.org_id == current_user.org_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    abs_path = StorageManager.get_absolute_path(doc.storage_path)
    try:
        tdoc = fitz.open(str(abs_path))
        if not tdoc.is_encrypted:
            tdoc.close()
            return {"valid": True, "message": "Document is not encrypted."}

        pwd = req.password or ""
        valid = bool(tdoc.authenticate(pwd))
        tdoc.close()
        if valid:
            return {"valid": True, "message": "Password verified successfully."}
        else:
            return {"valid": False, "message": "Incorrect statement password."}
    except Exception as e:
        return {"valid": False, "message": str(e)}

@router.post("/{document_id}/process", response_model=ProcessingJobStatus)
def trigger_processing(
    document_id: str,
    req: Optional[ProcessDocumentRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Launches async background extraction and validation pipeline with optional password."""
    doc = db.query(Document).filter(Document.id == document_id, Document.org_id == current_user.org_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    pwd = req.password.strip() if req and req.password else None
    abs_path = StorageManager.get_absolute_path(doc.storage_path)

    # Check encryption requirement
    if ExtractionPipeline.check_pdf_encryption(str(abs_path)):
        if not pwd:
            raise HTTPException(
                status_code=400,
                detail="Statement PDF is password-protected. Please enter statement password."
            )
        try:
            tdoc = fitz.open(str(abs_path))
            if not tdoc.authenticate(pwd):
                tdoc.close()
                raise HTTPException(
                    status_code=400,
                    detail="Incorrect statement password. Please verify and try again."
                )
            tdoc.close()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Cannot authenticate document: {e}")

    job_id = JobManager.create_job(document_id)
    JobManager.start_processing_task(job_id, document_id, password=pwd)

    job_status = JobManager.get_job_status(job_id)
    return job_status

@router.get("/jobs/{job_id}", response_model=ProcessingJobStatus)
def get_job_progress(job_id: str, current_user: User = Depends(get_current_user)):
    """Polls real-time progress of asynchronous extraction job."""
    status_info = JobManager.get_job_status(job_id)
    if not status_info:
        raise HTTPException(status_code=404, detail="Processing job not found.")
    return status_info

@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    client_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists uploaded documents with processing status."""
    q = db.query(Document).filter(Document.org_id == current_user.org_id)
    if client_id:
        q = q.filter(Document.client_id == client_id)
    return q.order_by(Document.uploaded_at.desc()).all()

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Gets details for a single document."""
    doc = db.query(Document).filter(Document.id == document_id, Document.org_id == current_user.org_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc
