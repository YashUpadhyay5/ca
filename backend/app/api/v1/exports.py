from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from decimal import Decimal
from app.core.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.models.review import ReviewItem
from app.schemas.export import ExportFilterOptions
from app.calculations.engine import CalculationEngine
from app.exports.excel_generator import ExcelExportService
from app.exports.csv_generator import CSVExportService
from app.validation.balance_validator import BalanceValidator
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/excel")
def export_statement_excel(
    opts: ExportFilterOptions,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates and serves professional 7-sheet openpyxl Excel workbook."""
    statement = db.query(Statement).join(Document).filter(
        Statement.id == opts.statement_id,
        Document.org_id == current_user.org_id
    ).first()
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found.")

    query = db.query(Transaction).filter(Transaction.statement_id == statement.id)

    if opts.date_from:
        query = query.filter(Transaction.transaction_date >= opts.date_from)
    if opts.date_to:
        query = query.filter(Transaction.transaction_date <= opts.date_to)
    if opts.transaction_type == "DEBIT":
        query = query.filter(Transaction.debit_amount > 0)
    elif opts.transaction_type == "CREDIT":
        query = query.filter(Transaction.credit_amount > 0)
    if opts.payment_mode:
        query = query.filter(Transaction.payment_mode == opts.payment_mode)
    if opts.category:
        query = query.filter(Transaction.category == opts.category)

    txns = query.order_by(Transaction.transaction_date).all()
    review_items = db.query(ReviewItem).join(Transaction).filter(Transaction.statement_id == statement.id).all()

    # Calculations for sheets
    overview_metrics = CalculationEngine.compute_summary_metrics(txns)
    overview_metrics["opening_balance"] = statement.opening_balance
    overview_metrics["closing_balance"] = statement.closing_balance
    overview_metrics["calculated_closing_balance"] = statement.calculated_closing_balance
    overview_metrics["balance_discrepancy"] = statement.balance_discrepancy

    monthly_data = CalculationEngine.compute_monthly_analysis(txns)
    payment_modes = CalculationEngine.compute_payment_modes(txns)
    categories = CalculationEngine.compute_categories(txns)

    is_valid, cum_diff, broken_steps = BalanceValidator.validate_continuity(txns, statement.opening_balance)
    recon_report = {"broken_steps": broken_steps}

    client_name = statement.document.client.name if statement.document and statement.document.client else "Client"

    file_path = ExcelExportService.generate_statement_workbook(
        statement=statement,
        transactions=txns,
        overview_metrics=overview_metrics,
        monthly_data=monthly_data,
        payment_modes=payment_modes,
        categories=categories,
        reconciliation_report=recon_report,
        review_items=review_items,
        client_name=client_name
    )

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@router.post("/csv")
def export_statement_csv(
    opts: ExportFilterOptions,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates and serves canonical CSV dataset of filtered transactions."""
    statement = db.query(Statement).join(Document).filter(
        Statement.id == opts.statement_id,
        Document.org_id == current_user.org_id
    ).first()
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found.")

    query = db.query(Transaction).filter(Transaction.statement_id == statement.id)

    if opts.date_from:
        query = query.filter(Transaction.transaction_date >= opts.date_from)
    if opts.date_to:
        query = query.filter(Transaction.transaction_date <= opts.date_to)
    if opts.transaction_type == "DEBIT":
        query = query.filter(Transaction.debit_amount > 0)
    elif opts.transaction_type == "CREDIT":
        query = query.filter(Transaction.credit_amount > 0)
    if opts.payment_mode:
        query = query.filter(Transaction.payment_mode == opts.payment_mode)
    if opts.category:
        query = query.filter(Transaction.category == opts.category)

    txns = query.order_by(Transaction.transaction_date).all()
    file_path = CSVExportService.generate_transactions_csv(txns, filename_prefix=f"{statement.bank_name[:4]}_export")

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="text/csv"
    )
