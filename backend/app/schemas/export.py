from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from decimal import Decimal

class ExportFilterOptions(BaseModel):
    statement_id: str
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    transaction_type: Optional[str] = "ALL"
    payment_mode: Optional[str] = None
    category: Optional[str] = None
    include_summary_sheet: bool = True
    include_monthly_sheet: bool = True
    include_payment_modes_sheet: bool = True
    include_categories_sheet: bool = True
    include_reconciliation_sheet: bool = True
    include_review_sheet: bool = True

class ReviewItemResponse(BaseModel):
    id: str
    transaction_id: str
    issue_code: str
    issue_description: str
    status: str
    corrected_by: Optional[str] = None
    resolution_note: Optional[str] = None

    class Config:
        from_attributes = True

class ReviewActionRequest(BaseModel):
    action: str  # ACCEPT, EDIT, REJECT, VERIFY
    category: Optional[str] = None
    debit_amount: Optional[Decimal] = None
    credit_amount: Optional[Decimal] = None
    resolution_note: Optional[str] = None
