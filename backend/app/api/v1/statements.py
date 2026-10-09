from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from decimal import Decimal
from app.core.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.models.review import ReviewItem
from app.schemas.statement import StatementResponse, StatementSummaryResponse
from app.schemas.transaction import TransactionResponse, PaginatedTransactionsResponse
from app.schemas.analytics import FinancialOverview
from app.schemas.reconciliation import ReconciliationReport, MultiAccountConsolidationRequest, MultiAccountConsolidationResponse
from app.calculations.engine import CalculationEngine
from app.validation.balance_validator import BalanceValidator
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[StatementResponse])
def list_statements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists all statements for the current tenant organization."""
    return db.query(Statement).join(Document).filter(
        Document.org_id == current_user.org_id
    ).order_by(Statement.created_at.desc()).all()

@router.get("/{statement_id}", response_model=StatementResponse)
def get_statement(
    statement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetches statement record with tenant security."""
    statement = db.query(Statement).join(Document).filter(
        (Statement.id == statement_id) | (Statement.document_id == statement_id),
        Document.org_id == current_user.org_id
    ).first()
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found.")
    return statement

@router.get("/{statement_id}/transactions", response_model=PaginatedTransactionsResponse)
def get_statement_transactions(
    statement_id: str,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    transaction_type: Optional[str] = None,  # ALL, DEBIT, CREDIT
    payment_mode: Optional[str] = None,
    category: Optional[str] = None,
    validation_status: Optional[str] = None,
    search: Optional[str] = None,
    is_anomaly: Optional[bool] = None,
    is_duplicate: Optional[bool] = None,
    sort_by: Optional[str] = "transaction_date",
    sort_dir: Optional[str] = "asc",
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Server-side virtualized spreadsheet query endpoint with high-performance filtering and sorting."""
    # Tenant verification
    statement = db.query(Statement).join(Document).filter(
        Statement.id == statement_id,
        Document.org_id == current_user.org_id
    ).first()
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found.")

    query = db.query(Transaction).filter(Transaction.statement_id == statement_id)

    # 1. Filters
    if date_from:
        query = query.filter(Transaction.transaction_date >= date_from)
    if date_to:
        query = query.filter(Transaction.transaction_date <= date_to)

    if transaction_type == "DEBIT":
        query = query.filter(Transaction.debit_amount > 0)
    elif transaction_type == "CREDIT":
        query = query.filter(Transaction.credit_amount > 0)

    if min_amount is not None:
        query = query.filter((Transaction.debit_amount >= min_amount) | (Transaction.credit_amount >= min_amount))
    if max_amount is not None:
        query = query.filter((Transaction.debit_amount <= max_amount) & (Transaction.credit_amount <= max_amount))

    if payment_mode:
        query = query.filter(Transaction.payment_mode == payment_mode.upper())
    if category:
        query = query.filter(Transaction.category == category)
    if validation_status:
        query = query.filter(Transaction.validation_status == validation_status)

    if is_anomaly is not None:
        query = query.filter(Transaction.is_anomaly == is_anomaly)
    if is_duplicate is not None:
        query = query.filter(Transaction.is_potential_duplicate == is_duplicate)

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            (Transaction.narration.ilike(search_pattern)) |
            (Transaction.reference_number.ilike(search_pattern)) |
            (Transaction.cheque_number.ilike(search_pattern)) |
            (Transaction.counterparty.ilike(search_pattern)) |
            (Transaction.upi_id.ilike(search_pattern))
        )

    # 2. Aggregates for the filtered set
    all_filtered = query.all()
    total_count = len(all_filtered)
    total_debits = sum([t.debit_amount for t in all_filtered], Decimal("0.00"))
    total_credits = sum([t.credit_amount for t in all_filtered], Decimal("0.00"))
    net_amt = total_credits - total_debits

    # 3. Sorting
    sort_column = getattr(Transaction, sort_by or "transaction_date", Transaction.transaction_date)
    if sort_dir == "desc":
        query = query.order_by(sort_column.desc(), Transaction.source_row.desc())
    else:
        query = query.order_by(sort_column.asc(), Transaction.source_row.asc())

    # 4. Pagination
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "total_debits": total_debits,
        "total_credits": total_credits,
        "net_amount": net_amt
    }

@router.get("/{statement_id}/analytics", response_model=FinancialOverview)
def get_statement_analytics(
    statement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Computes comprehensive financial intelligence, monthly Indian FY trends, and tax analytics."""
    statement = db.query(Statement).join(Document).filter(
        Statement.id == statement_id,
        Document.org_id == current_user.org_id
    ).first()
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found.")

    txns = db.query(Transaction).filter(Transaction.statement_id == statement_id).order_by(Transaction.transaction_date).all()
    
    metrics = CalculationEngine.compute_summary_metrics(txns)
    monthly_trends = CalculationEngine.compute_monthly_analysis(txns)
    daily_analysis = CalculationEngine.compute_daily_analysis(txns)
    payment_modes = CalculationEngine.compute_payment_modes(txns)
    categories = CalculationEngine.compute_categories(txns)
    top_txns = CalculationEngine.compute_top_transactions(txns, limit=10)
    tax_summary = CalculationEngine.compute_tax_summary(txns)

    anomaly_cnt = sum(1 for t in txns if t.is_anomaly)
    duplicate_cnt = sum(1 for t in txns if t.is_potential_duplicate)
    review_cnt = sum(1 for t in txns if t.validation_status == "REVIEW_REQUIRED")

    return {
        "statement_id": statement.id,
        "bank_name": statement.bank_name,
        "period_start": str(statement.period_start) if statement.period_start else None,
        "period_end": str(statement.period_end) if statement.period_end else None,
        "opening_balance": statement.opening_balance,
        "closing_balance": statement.closing_balance,
        "calculated_closing_balance": statement.calculated_closing_balance,
        "balance_discrepancy": statement.balance_discrepancy,
        "reconciliation_status": statement.reconciliation_status,
        "total_credits": metrics["total_credits"],
        "total_debits": metrics["total_debits"],
        "net_movement": metrics["net_movement"],
        "total_transactions": metrics["total_transactions"],
        "debit_count": metrics["debit_count"],
        "credit_count": metrics["credit_count"],
        "largest_credit": metrics["largest_credit"],
        "largest_debit": metrics["largest_debit"],
        "average_transaction": metrics["average_transaction"],
        "median_transaction": metrics["median_transaction"],
        "std_dev_transaction": metrics["std_dev_transaction"],
        "highest_debit_day": daily_analysis.get("highest_debit_day"),
        "highest_credit_day": daily_analysis.get("highest_credit_day"),
        "anomaly_count": anomaly_cnt,
        "potential_duplicate_count": duplicate_cnt,
        "review_required_count": review_cnt,
        "monthly_trends": monthly_trends,
        "payment_modes": payment_modes,
        "top_categories": categories,
        "top_debits": top_txns["top_debits"],
        "top_credits": top_txns["top_credits"],
        "tax_summary": tax_summary
    }

@router.get("/{statement_id}/reconciliation", response_model=ReconciliationReport)
def get_statement_reconciliation(
    statement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculates step-by-step balance continuity and reconciliation report."""
    statement = db.query(Statement).join(Document).filter(
        Statement.id == statement_id,
        Document.org_id == current_user.org_id
    ).first()
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found.")

    txns = db.query(Transaction).filter(Transaction.statement_id == statement_id).order_by(Transaction.transaction_date).all()
    
    is_valid, cum_diff, broken_steps = BalanceValidator.validate_continuity(txns, statement.opening_balance)

    return {
        "statement_id": statement.id,
        "bank_name": statement.bank_name,
        "opening_balance": statement.opening_balance,
        "closing_balance": statement.closing_balance,
        "sum_credits": statement.total_credits,
        "sum_debits": statement.total_debits,
        "expected_closing_balance": statement.calculated_closing_balance,
        "discrepancy": statement.balance_discrepancy,
        "status": statement.reconciliation_status,
        "broken_step_count": len(broken_steps),
        "broken_steps": broken_steps
    }

@router.post("/consolidate", response_model=MultiAccountConsolidationResponse)
def consolidate_statements(
    req: MultiAccountConsolidationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Consolidates multiple bank statements and detects cross-account internal transfers."""
    statements = db.query(Statement).join(Document).filter(
        Statement.id.in_(req.statement_ids),
        Document.org_id == current_user.org_id
    ).all()

    if not statements:
        raise HTTPException(status_code=400, detail="No matching statements found.")

    statements_txns = []
    total_opening = Decimal("0.00")
    total_closing = Decimal("0.00")
    combined_cr = Decimal("0.00")
    combined_dr = Decimal("0.00")
    total_txns = 0
    breakdown = []

    for s in statements:
        txns = db.query(Transaction).filter(Transaction.statement_id == s.id).all()
        statements_txns.append(txns)
        total_opening += s.opening_balance
        total_closing += s.closing_balance
        combined_cr += s.total_credits
        combined_dr += s.total_debits
        total_txns += s.total_transactions
        breakdown.append({
            "statement_id": s.id,
            "bank_name": s.bank_name,
            "account_number": s.account_number_detected or "Masked",
            "opening_balance": float(s.opening_balance),
            "closing_balance": float(s.closing_balance),
            "credits": float(s.total_credits),
            "debits": float(s.total_debits),
            "transactions": s.total_transactions
        })

    internal_transfers = CalculationEngine.detect_internal_transfers(statements_txns)
    transfer_vol = sum([Decimal(str(t["amount"])) for t in internal_transfers], Decimal("0.00"))

    return {
        "account_count": len(statements),
        "total_opening_balance": total_opening,
        "total_closing_balance": total_closing,
        "combined_credits": combined_cr,
        "combined_debits": combined_dr,
        "net_movement": combined_cr - combined_dr,
        "total_transactions": total_txns,
        "detected_internal_transfers_count": len(internal_transfers),
        "internal_transfers_volume": transfer_vol,
        "breakdown_by_bank": breakdown
    }
