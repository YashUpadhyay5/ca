from decimal import Decimal
from typing import List, Tuple, Dict, Any

class BalanceValidator:
    """Verifies strict balance continuity and statement-level financial reconciliation."""

    @classmethod
    def validate_continuity(
        cls, 
        transactions: List[Any], 
        opening_balance: Decimal
    ) -> Tuple[bool, Decimal, List[Dict[str, Any]]]:
        """
        Validates step-by-step continuity:
        Balance[t] == Balance[t-1] + Credit[t] - Debit[t]
        Returns: (is_valid, cumulative_discrepancy, list_of_broken_steps)
        """
        if not transactions:
            return True, Decimal("0.00"), []

        broken_steps: List[Dict[str, Any]] = []
        running_expected = opening_balance

        for idx, txn in enumerate(transactions):
            debit = Decimal(str(txn.debit_amount))
            credit = Decimal(str(txn.credit_amount))
            reported_balance = Decimal(str(txn.balance))

            step_expected = running_expected + credit - debit
            diff = abs(reported_balance - step_expected)

            # Allow 0.05 tolerance for rounding
            if diff > Decimal("0.05") and reported_balance != Decimal("0.00"):
                broken_steps.append({
                    "row_index": idx + 1,
                    "date": str(txn.transaction_date),
                    "narration": txn.narration,
                    "debit": debit,
                    "credit": credit,
                    "previous_balance": running_expected,
                    "expected_balance": step_expected,
                    "reported_balance": reported_balance,
                    "difference": reported_balance - step_expected,
                    "is_continuity_broken": True
                })
                # Resync running balance to reported balance for subsequent steps
                running_expected = reported_balance
            else:
                running_expected = reported_balance if reported_balance != Decimal("0.00") else step_expected

        is_reconciled = len(broken_steps) == 0
        total_diff = sum([abs(step["difference"]) for step in broken_steps], Decimal("0.00"))
        return is_reconciled, total_diff, broken_steps

    @classmethod
    def reconcile_statement(
        cls, 
        opening_balance: Decimal, 
        closing_balance: Decimal, 
        total_credits: Decimal, 
        total_debits: Decimal
    ) -> Tuple[bool, Decimal, Decimal]:
        """
        Statement invariant:
        Expected Closing = Opening + Total Credits - Total Debits
        Returns: (is_reconciled, expected_closing_balance, difference)
        """
        expected_closing = (opening_balance + total_credits - total_debits).quantize(Decimal("0.01"))
        difference = (closing_balance - expected_closing).quantize(Decimal("0.01"))
        is_reconciled = abs(difference) <= Decimal("0.05")
        return is_reconciled, expected_closing, difference
