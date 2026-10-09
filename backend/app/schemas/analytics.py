from pydantic import BaseModel
from typing import List, Optional, Dict
from decimal import Decimal

class MonthlySummaryItem(BaseModel):
    month_name: str
    year: int
    fiscal_month_index: int
    credits: Decimal
    debits: Decimal
    net_movement: Decimal
    transaction_count: int
    average_transaction: Decimal

class PaymentModeItem(BaseModel):
    mode: str
    count: int
    total_amount: Decimal
    percentage: float

class CategoryItem(BaseModel):
    category: str
    debit_amount: Decimal
    credit_amount: Decimal
    transaction_count: int
    percentage_of_debit: float

class TopTransactionItem(BaseModel):
    id: str
    date: str
    narration: str
    amount: Decimal
    transaction_type: str
    payment_mode: str
    counterparty: Optional[str] = None
    category: str

class TaxItem(BaseModel):
    tax_type: str  # GST, TDS, ADVANCE_TAX, SELF_ASSESSMENT_TAX, PROFESSIONAL_TAX
    total_paid: Decimal
    transaction_count: int
    transactions: List[TopTransactionItem]

class FinancialOverview(BaseModel):
    statement_id: str
    bank_name: str
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    opening_balance: Decimal
    closing_balance: Decimal
    calculated_closing_balance: Decimal
    balance_discrepancy: Decimal
    reconciliation_status: str
    total_credits: Decimal
    total_debits: Decimal
    net_movement: Decimal
    total_transactions: int
    debit_count: int
    credit_count: int
    largest_credit: Decimal
    largest_debit: Decimal
    average_transaction: Decimal
    median_transaction: Decimal
    std_dev_transaction: Decimal
    highest_debit_day: Optional[str] = None
    highest_credit_day: Optional[str] = None
    anomaly_count: int
    potential_duplicate_count: int
    review_required_count: int
    monthly_trends: List[MonthlySummaryItem]
    payment_modes: List[PaymentModeItem]
    top_categories: List[CategoryItem]
    top_debits: List[TopTransactionItem]
    top_credits: List[TopTransactionItem]
    tax_summary: List[TaxItem]
