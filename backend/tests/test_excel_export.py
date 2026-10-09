import unittest
from decimal import Decimal
from datetime import date
from openpyxl import load_workbook
from app.exports.excel_generator import ExcelExportService

class DummyStatement:
    id = "stmt_test_12345678"
    bank_name = "HDFC Bank"
    account_number_detected = "XXXXXX1234"
    period_start = date(2025, 4, 1)
    period_end = date(2025, 5, 31)
    opening_balance = Decimal("10000.00")
    closing_balance = Decimal("48000.00")
    calculated_closing_balance = Decimal("48000.00")
    balance_discrepancy = Decimal("0.00")
    reconciliation_status = "RECONCILED"
    confidence_avg = Decimal("0.98")
    parser_used = "HDFC Bank Statement Parser"
    document = None

class DummyTxn:
    def __init__(self, idx, dt, narr, dr, cr, bal, mode="UPI", cat="Office"):
        self.id = f"tx_{idx}"
        self.transaction_date = dt
        self.value_date = dt
        self.narration = narr
        self.reference_number = f"REF{idx}"
        self.cheque_number = None
        self.debit_amount = Decimal(str(dr))
        self.credit_amount = Decimal(str(cr))
        self.balance = Decimal(str(bal))
        self.payment_mode = mode
        self.category = cat
        self.subcategory = None
        self.counterparty = "Vendor"
        self.upi_id = None
        self.source_page = 1
        self.confidence_score = Decimal("0.98")
        self.validation_status = "VALIDATED"
        self.notes = None

class TestExcelExport(unittest.TestCase):

    def test_multi_sheet_13_workbook_generation(self):
        stmt = DummyStatement()
        txns = [
            DummyTxn(1, date(2025, 4, 1), "Opening Inflow NEFT", 0, 50000, 60000, "NEFT", "Salary"),
            DummyTxn(2, date(2025, 4, 15), "Vendor Payment UPI", 12000, 0, 48000, "UPI", "Vendor Payment"),
            DummyTxn(3, date(2025, 4, 20), "ATM Cash Withdrawal", 5000, 0, 43000, "ATM", "Cash Withdrawal")
        ]

        overview = {
            "opening_balance": Decimal("10000.00"),
            "closing_balance": Decimal("48000.00"),
            "calculated_closing_balance": Decimal("48000.00"),
            "balance_discrepancy": Decimal("0.00"),
            "total_credits": Decimal("50000.00"),
            "total_debits": Decimal("12000.00"),
            "net_movement": Decimal("38000.00"),
            "total_transactions": 2,
            "debit_count": 1,
            "credit_count": 1,
            "largest_credit": Decimal("50000.00"),
            "largest_debit": Decimal("12000.00"),
            "average_transaction": Decimal("31000.00"),
            "median_transaction": Decimal("31000.00"),
        }

        monthly = [{"month_name": "Apr 2025", "credits": Decimal("50000.00"), "debits": Decimal("12000.00"), "net_movement": Decimal("38000.00"), "transaction_count": 2, "average_transaction": Decimal("31000.00")}]
        payment_modes = [{"mode": "UPI", "count": 1, "total_amount": Decimal("12000.00"), "percentage": 19.35}]
        categories = [{"category": "Vendor Payment", "debit_amount": Decimal("12000.00"), "credit_amount": Decimal("0.00"), "transaction_count": 1, "percentage_of_debit": 100.0}]

        file_path = ExcelExportService.generate_statement_workbook(
            statement=stmt,
            transactions=txns,
            overview_metrics=overview,
            monthly_data=monthly,
            payment_modes=payment_modes,
            categories=categories,
            reconciliation_report={"broken_steps": []},
            review_items=[],
            client_name="Test Enterprise Pvt Ltd"
        )

        self.assertTrue(file_path.exists())

        # Load and verify all 13 sheets exist
        wb = load_workbook(str(file_path))
        expected_sheets = [
            "01_Cover",
            "02_Summary",
            "03_Transactions",
            "04_Above_10000",
            "05_Cash_Transactions",
            "06_Bank_Transfers_RTGS",
            "07_UPI_Transactions",
            "08_Debit_Transactions",
            "09_Credit_Transactions",
            "10_Monthly_Analysis",
            "11_Category_Analysis",
            "12_Reconciliation",
            "13_Reference_Data"
        ]
        self.assertEqual(len(wb.sheetnames), 13)
        for s in expected_sheets:
            self.assertIn(s, wb.sheetnames)

        # Verify tblTransactions Table
        tx_sheet = wb["03_Transactions"]
        self.assertEqual(tx_sheet.cell(row=1, column=1).value, "Transaction ID")
        self.assertEqual(tx_sheet.cell(row=1, column=2).value, "Transaction Date")
        self.assertEqual(tx_sheet.cell(row=1, column=7).value, "Debit")
        self.assertEqual(tx_sheet.cell(row=1, column=8).value, "Credit")
        self.assertEqual(tx_sheet.cell(row=1, column=9).value, "Balance")
        self.assertIn("tblTransactions", tx_sheet.tables)

        # Verify Filtered Sheets Tables
        self.assertIn("tblAbove10K", wb["04_Above_10000"].tables)
        self.assertIn("tblCashTxns", wb["05_Cash_Transactions"].tables)
        self.assertIn("tblTransfers", wb["06_Bank_Transfers_RTGS"].tables)
        self.assertIn("tblUPITxns", wb["07_UPI_Transactions"].tables)
        self.assertIn("tblDebits", wb["08_Debit_Transactions"].tables)
        self.assertIn("tblCredits", wb["09_Credit_Transactions"].tables)

        # Verify formulas in 02_Summary
        summary_sheet = wb["02_Summary"]
        self.assertEqual(summary_sheet["C8"].value, "=SUM(tblTransactions[Credit])")
        self.assertEqual(summary_sheet["C9"].value, "=SUM(tblTransactions[Debit])")

        # Cleanup created test file
        if file_path.exists():
            file_path.unlink()

if __name__ == "__main__":
    unittest.main()
