from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal

class BalanceStepItem(BaseModel):
    row_index: int
    date: str
    narration: str
    debit: Decimal
    credit: Decimal
    previous_balance: Decimal
    expected_balance: Decimal
    reported_balance: Decimal
    difference: Decimal
    is_continuity_broken: bool

class ReconciliationReport(BaseModel):
    statement_id: str
    bank_name: str
    opening_balance: Decimal
    closing_balance: Decimal
    sum_credits: Decimal
    sum_debits: Decimal
    expected_closing_balance: Decimal
    discrepancy: Decimal
    status: str  # RECONCILED, DISCREPANCY_DETECTED
    broken_step_count: int
    broken_steps: List[BalanceStepItem]

class MultiAccountConsolidationRequest(BaseModel):
    statement_ids: List[str]

class MultiAccountConsolidationResponse(BaseModel):
    account_count: int
    total_opening_balance: Decimal
    total_closing_balance: Decimal
    combined_credits: Decimal
    combined_debits: Decimal
    net_movement: Decimal
    total_transactions: int
    detected_internal_transfers_count: int
    internal_transfers_volume: Decimal
    breakdown_by_bank: List[dict]
