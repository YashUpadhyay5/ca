from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from app.core.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.models.audit_log import AuditLog
from app.schemas.transaction import TransactionResponse, TransactionUpdate, BulkCategorizeRequest
from app.api.deps import get_current_user

router = APIRouter()

@router.patch("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: str,
    req: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates transaction category, notes, or amounts with immutable audit logging.
    Preserves original extraction lineage.
    """
    txn = db.query(Transaction).join(Statement).join(Document).filter(
        Transaction.id == transaction_id,
        Document.org_id == current_user.org_id
    ).first()

    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    old_state = {
        "category": txn.category,
        "subcategory": txn.subcategory,
        "debit_amount": str(txn.debit_amount),
        "credit_amount": str(txn.credit_amount),
        "notes": txn.notes,
        "validation_status": txn.validation_status
    }

    updated_fields = req.dict(exclude_unset=True)
    reason = updated_fields.pop("reason", "Manual review modification by CA")

    for field, val in updated_fields.items():
        if val is not None:
            setattr(txn, field, val)

    # Set validation status to MANUAL_CORRECTED if modified
    txn.validation_status = "MANUAL_CORRECTED"
    txn.updated_at = datetime.now(timezone.utc)

    # Log audit entry
    new_state = {
        "category": txn.category,
        "subcategory": txn.subcategory,
        "debit_amount": str(txn.debit_amount),
        "credit_amount": str(txn.credit_amount),
        "notes": txn.notes,
        "validation_status": txn.validation_status
    }

    audit = AuditLog(
        org_id=current_user.org_id,
        user_id=current_user.id,
        action="UPDATE_TRANSACTION",
        entity_name="Transaction",
        entity_id=txn.id,
        old_value=old_state,
        new_value=new_state,
        details=f"Reason: {reason}"
    )
    db.add(audit)
    db.commit()
    db.refresh(txn)

    return txn

@router.post("/bulk-categorize")
def bulk_categorize_transactions(
    req: BulkCategorizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk categorizes selected transactions and logs individual audit trails."""
    txns = db.query(Transaction).join(Statement).join(Document).filter(
        Transaction.id.in_(req.transaction_ids),
        Document.org_id == current_user.org_id
    ).all()

    if not txns:
        raise HTTPException(status_code=400, detail="No matching transactions found.")

    for t in txns:
        old_cat = t.category
        t.category = req.category
        if req.subcategory:
            t.subcategory = req.subcategory
        t.validation_status = "MANUAL_CORRECTED"

        audit = AuditLog(
            org_id=current_user.org_id,
            user_id=current_user.id,
            action="BULK_CATEGORIZE",
            entity_name="Transaction",
            entity_id=t.id,
            old_value={"category": old_cat},
            new_value={"category": req.category, "subcategory": req.subcategory},
            details=req.reason
        )
        db.add(audit)

    db.commit()
    return {"message": f"Successfully categorized {len(txns)} transactions to '{req.category}'."}
