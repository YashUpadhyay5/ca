from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

class StatementResponse(BaseModel):
    id: str
    document_id: str
    bank_account_id: Optional[str] = None
    bank_name: str
    account_number_detected: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    opening_balance: Decimal
    closing_balance: Decimal
    calculated_closing_balance: Decimal
    balance_discrepancy: Decimal
    reconciliation_status: str
    total_transactions: int
    total_credits: Decimal
    total_debits: Decimal
    net_movement: Decimal
    parser_used: str
    confidence_avg: Decimal
    created_at: datetime

    class Config:
        from_attributes = True

class StatementSummaryResponse(BaseModel):
    statement: StatementResponse
    opening_balance: Decimal
    closing_balance: Decimal
    total_credits: Decimal
    total_debits: Decimal
    net_movement: Decimal
    total_transactions: int
    largest_credit: Decimal
    largest_debit: Decimal
    average_transaction: Decimal
    median_transaction: Decimal
    reconciliation_status: str
    discrepancy: Decimal
