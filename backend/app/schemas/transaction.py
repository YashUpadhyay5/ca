from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

class TransactionResponse(BaseModel):
    id: str
    statement_id: str
    transaction_date: date
    value_date: Optional[date] = None
    narration: str
    raw_text: str
    reference_number: Optional[str] = None
    cheque_number: Optional[str] = None
    debit_amount: Decimal
    credit_amount: Decimal
    balance: Decimal
    payment_mode: str
    category: str
    subcategory: Optional[str] = None
    counterparty: Optional[str] = None
    upi_id: Optional[str] = None
    source_page: int
    source_row: int
    confidence_score: Decimal
    validation_status: str
    is_internal_transfer: bool
    is_potential_duplicate: bool
    is_anomaly: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TransactionUpdate(BaseModel):
    category: Optional[str] = None
    subcategory: Optional[str] = None
    debit_amount: Optional[Decimal] = None
    credit_amount: Optional[Decimal] = None
    payment_mode: Optional[str] = None
    counterparty: Optional[str] = None
    validation_status: Optional[str] = None
    notes: Optional[str] = None
    reason: Optional[str] = Field(None, description="Audit reason for modifying financial transaction")

class BulkCategorizeRequest(BaseModel):
    transaction_ids: List[str]
    category: str
    subcategory: Optional[str] = None
    reason: Optional[str] = "Bulk categorization by auditor"

class TransactionFilterParams(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    transaction_type: Optional[str] = None  # ALL, DEBIT, CREDIT
    payment_mode: Optional[str] = None
    category: Optional[str] = None
    validation_status: Optional[str] = None
    search: Optional[str] = None
    is_anomaly: Optional[bool] = None
    is_duplicate: Optional[bool] = None
    sort_by: Optional[str] = "transaction_date"  # transaction_date, debit_amount, credit_amount, balance, confidence_score
    sort_dir: Optional[str] = "asc"  # asc, desc
    page: int = 1
    page_size: int = 50

class PaginatedTransactionsResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    total_debits: Decimal
    total_credits: Decimal
    net_amount: Decimal
