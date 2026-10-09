import unittest
from decimal import Decimal
from datetime import date
from app.validation.balance_validator import BalanceValidator
from app.validation.anomaly_detector import AnomalyDetector

class DummyTxn:
    def __init__(self, dt, narr, dr, cr, bal):
        self.transaction_date = dt
        self.narration = narr
        self.debit_amount = Decimal(str(dr))
        self.credit_amount = Decimal(str(cr))
        self.balance = Decimal(str(bal))

class TestFinancialValidation(unittest.TestCase):

    def test_reconciliation_invariant(self):
        # Opening: 100,000, Credits: 50,000, Debits: 30,000 -> Expected Closing: 120,000
        is_rec, exp_close, diff = BalanceValidator.reconcile_statement(
            opening_balance=Decimal("100000.00"),
            closing_balance=Decimal("120000.00"),
            total_credits=Decimal("50000.00"),
            total_debits=Decimal("30000.00")
        )
        self.assertTrue(is_rec)
        self.assertEqual(exp_close, Decimal("120000.00"))
        self.assertEqual(diff, Decimal("0.00"))

    def test_reconciliation_discrepancy_detected(self):
        # Actual closing: 115,000, Expected: 120,000 -> Diff -5,000
        is_rec, exp_close, diff = BalanceValidator.reconcile_statement(
            opening_balance=Decimal("100000.00"),
            closing_balance=Decimal("115000.00"),
            total_credits=Decimal("50000.00"),
            total_debits=Decimal("30000.00")
        )
        self.assertFalse(is_rec)
        self.assertEqual(diff, Decimal("-5000.00"))

    def test_step_continuity(self):
        txns = [
            DummyTxn(date(2025, 4, 1), "Deposit", 0, 10000, 110000),
            DummyTxn(date(2025, 4, 2), "Withdrawal", 5000, 0, 105000),
            DummyTxn(date(2025, 4, 3), "Broken step", 2000, 0, 100000)  # Should have been 103,000!
        ]
        is_valid, cum_diff, broken = BalanceValidator.validate_continuity(txns, Decimal("100000.00"))
        self.assertFalse(is_valid)
        self.assertEqual(len(broken), 1)
        self.assertEqual(broken[0]["row_index"], 3)
        self.assertEqual(broken[0]["expected_balance"], Decimal("103000.00"))

    def test_duplicate_and_anomaly_detection(self):
        raw_list = [
            {"transaction_date": date(2025, 4, 1), "debit_amount": Decimal("5000.00"), "credit_amount": Decimal("0.00"), "narration": "OFFICE EXPENSE VENDOR"},
            {"transaction_date": date(2025, 4, 1), "debit_amount": Decimal("5000.00"), "credit_amount": Decimal("0.00"), "narration": "OFFICE EXPENSE VENDOR"},
            {"transaction_date": date(2025, 4, 5), "debit_amount": Decimal("500000.00"), "credit_amount": Decimal("0.00"), "narration": "ROUND NUMBER TRANSFER"}
        ]
        AnomalyDetector.flag_anomalies(raw_list)
        self.assertTrue(raw_list[0]["is_potential_duplicate"])
        self.assertTrue(raw_list[1]["is_potential_duplicate"])
        self.assertTrue(raw_list[2]["is_anomaly"])

if __name__ == "__main__":
    unittest.main()
