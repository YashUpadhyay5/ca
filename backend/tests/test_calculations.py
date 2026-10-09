import unittest
from decimal import Decimal
from datetime import date
from app.calculations.engine import CalculationEngine

class MockTxn:
    def __init__(self, id_val, dt, dr, cr, bal, mode="UPI", cat="Shopping", subcat=None, counterparty="Vendor"):
        self.id = id_val
        self.transaction_date = dt
        self.debit_amount = Decimal(str(dr))
        self.credit_amount = Decimal(str(cr))
        self.balance = Decimal(str(bal))
        self.payment_mode = mode
        self.category = cat
        self.subcategory = subcat
        self.counterparty = counterparty
        self.narration = f"Txn {cat}"

class TestCalculationEngine(unittest.TestCase):

    def setUp(self):
        self.txns = [
            MockTxn("1", date(2025, 4, 1), 0, 100000, 100000, mode="NEFT", cat="Salary"),
            MockTxn("2", date(2025, 4, 5), 25000, 0, 75000, mode="TRANSFER", cat="Rent"),
            MockTxn("3", date(2025, 4, 10), 15000, 0, 60000, mode="NEFT", cat="Tax", subcat="GST"),
            MockTxn("4", date(2025, 5, 2), 2000, 0, 58000, mode="UPI", cat="Food"),
            MockTxn("5", date(2025, 5, 15), 50000, 0, 8000, mode="RTGS", cat="EMI"),
        ]

    def test_summary_metrics(self):
        metrics = CalculationEngine.compute_summary_metrics(self.txns)
        self.assertEqual(metrics["total_credits"], Decimal("100000.00"))
        self.assertEqual(metrics["total_debits"], Decimal("92000.00"))
        self.assertEqual(metrics["net_movement"], Decimal("8000.00"))
        self.assertEqual(metrics["total_transactions"], 5)
        self.assertEqual(metrics["largest_debit"], Decimal("50000.00"))

    def test_monthly_analysis(self):
        monthly = CalculationEngine.compute_monthly_analysis(self.txns)
        self.assertEqual(len(monthly), 2)
        # April (Fiscal Month 1)
        self.assertEqual(monthly[0]["month_name"], "Apr 2025")
        self.assertEqual(monthly[0]["credits"], Decimal("100000.00"))
        self.assertEqual(monthly[0]["debits"], Decimal("40000.00"))
        # May (Fiscal Month 2)
        self.assertEqual(monthly[1]["month_name"], "May 2025")
        self.assertEqual(monthly[1]["debits"], Decimal("52000.00"))

    def test_tax_summary(self):
        tax = CalculationEngine.compute_tax_summary(self.txns)
        gst_item = next((item for item in tax if item["tax_type"] == "GST"), None)
        self.assertIsNotNone(gst_item)
        self.assertEqual(gst_item["total_paid"], Decimal("15000.00"))
        self.assertEqual(gst_item["transaction_count"], 1)

if __name__ == "__main__":
    unittest.main()
