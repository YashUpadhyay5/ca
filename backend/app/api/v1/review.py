from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.core.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.models.review import ReviewItem
from app.models.audit_log import AuditLog
from app.schemas.export import ReviewItemResponse, ReviewActionRequest
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[dict])
def get_review_queue(
    statement_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves all pending items in the CA review queue."""
    query = db.query(ReviewItem, Transaction).join(Transaction, ReviewItem.transaction_id == Transaction.id)\
              .join(Statement, Transaction.statement_id == Statement.id)\
              .join(Document, Statement.document_id == Document.id)\
              .filter(Document.org_id == current_user.org_id, ReviewItem.status == "PENDING")

    if statement_id:
        query = query.filter(Statement.id == statement_id)

    results = []
    for rev, txn in query.all():
        results.append({
            "id": rev.id,
            "transaction_id": txn.id,
            "statement_id": txn.statement_id,
            "date": str(txn.transaction_date),
            "narration": txn.narration,
            "raw_text": txn.raw_text,
            "debit_amount": float(txn.debit_amount),
            "credit_amount": float(txn.credit_amount),
            "balance": float(txn.balance),
            "issue_code": rev.issue_code,
            "issue_description": rev.issue_description,
            "confidence_score": float(txn.confidence_score),
            "status": rev.status,
            "category": txn.category,
            "payment_mode": txn.payment_mode
        })

    return results

@router.post("/{review_id}/resolve")
def resolve_review_item(
    review_id: str,
    req: ReviewActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resolves review item (ACCEPT, EDIT, REJECT, VERIFY) and logs resolution."""
    rev = db.query(ReviewItem).join(Transaction).join(Statement).join(Document).filter(
        ReviewItem.id == review_id,
        Document.org_id == current_user.org_id
    ).first()

    if not rev:
        raise HTTPException(status_code=404, detail="Review item not found.")

    rev.status = req.action.upper()
    rev.corrected_by = current_user.full_name
    rev.resolution_note = req.resolution_note
    rev.resolved_at = datetime.now(timezone.utc)

    txn = rev.transaction
    if req.category:
        txn.category = req.category
    if req.debit_amount is not None:
        txn.debit_amount = req.debit_amount
    if req.credit_amount is not None:
        txn.credit_amount = req.credit_amount

    txn.validation_status = "VALIDATED" if req.action in ["ACCEPT", "VERIFY"] else "MANUAL_CORRECTED"

    audit = AuditLog(
        org_id=current_user.org_id,
        user_id=current_user.id,
        action=f"REVIEW_{req.action.upper()}",
        entity_name="ReviewItem",
        entity_id=rev.id,
        details=f"Resolved issue {rev.issue_code}. Notes: {req.resolution_note or 'None'}"
    )
    db.add(audit)
    db.commit()

    return {"message": f"Review item resolved with status: {req.action.upper()}."}
