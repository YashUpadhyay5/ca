import csv
from typing import List, Any
from pathlib import Path
from app.config import settings

class CSVExportService:
    """Fast, clean CSV Export Service for complete or filtered transaction sets."""

    @classmethod
    def generate_transactions_csv(cls, transactions: List[Any], filename_prefix: str = "transactions") -> Path:
        """Generates clean RFC 4180 standard CSV containing canonical transactions."""
        csv_filename = f"{filename_prefix}_{len(transactions)}_records.csv"
        csv_path = settings.EXPORTS_DIR / csv_filename

        fieldnames = [
            "S.No", "Date", "Value Date", "Description / Narration", "Cheque / Ref No",
            "Withdrawal (Debit INR)", "Deposit (Credit INR)", "Balance (INR)", "Payment Mode",
            "Category", "Counterparty", "UPI ID", "Source Page"
        ]

        with open(csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(fieldnames)

            for idx, t in enumerate(transactions, start=1):
                writer.writerow([
                    idx,
                    str(t.transaction_date),
                    str(t.value_date or t.transaction_date),
                    t.narration,
                    t.cheque_number or t.reference_number or "",
                    f"{float(t.debit_amount):.2f}" if t.debit_amount else "0.00",
                    f"{float(t.credit_amount):.2f}" if t.credit_amount else "0.00",
                    f"{float(t.balance):.2f}" if t.balance is not None else "0.00",
                    t.payment_mode or "TRANSFER",
                    t.category or "Miscellaneous",
                    t.counterparty or "",
                    t.upi_id or "",
                    t.source_page or 1
                ])

        return csv_path
