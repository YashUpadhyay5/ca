import re
from typing import List, Optional
from datetime import date
from decimal import Decimal
from app.extraction.parsers.base import BaseBankParser, RawTransaction
from app.extraction.normalizer import DataNormalizer

class SBIBankParser(BaseBankParser):
    """Parser adapter for State Bank of India (SBI) statements."""

    @property
    def bank_name(self) -> str:
        return "State Bank of India"

    def detect(self, sample_text: str) -> bool:
        upper = sample_text.upper()
        return ("STATE BANK OF INDIA" in upper or "SBIN0" in upper or "WWW.ONLINESBI.COM" in upper)

    def parse_page_table(self, table: List[List[str]], page_number: int) -> List[RawTransaction]:
        transactions: List[RawTransaction] = []
        if not table or len(table) < 2:
            return transactions

        header_idx = -1
        # Detect header row
        for i, row in enumerate(table[:10]):
            row_str = " ".join([str(c) for c in row if c]).upper()
            if ("TXN DATE" in row_str or "DATE" in row_str) and ("DEBIT" in row_str or "WITHDRAWAL" in row_str or "BALANCE" in row_str):
                header_idx = i
                break

        if header_idx == -1:
            header_idx = 0  # Fallback to first row

        current_txn: Optional[RawTransaction] = None

        for row_idx, row in enumerate(table[header_idx + 1:], start=header_idx + 1):
            if not row or not any(row):
                continue

            cleaned_cells = [str(c or "").strip() for c in row]
            # Skip empty or repeated header rows on subsequent pages
            row_str = " ".join(cleaned_cells).upper()
            if "TXN DATE" in row_str or "PAGE NO" in row_str or "STATEMENT OF ACCOUNT" in row_str:
                continue

            # SBI usually has: Txn Date | Value Date | Description | Ref No./Cheque No. | Debit | Credit | Balance
            # Or 6 columns: Date | Description | Ref/Chq | Debit | Credit | Balance
            txn_date = None
            first_cell = cleaned_cells[0] if len(cleaned_cells) > 0 else ""
            parsed_date = DataNormalizer.parse_date(first_cell)

            if parsed_date:
                # New transaction line
                txn_date = parsed_date
                val_date = None
                narration = ""
                ref_num = None
                debit_val = Decimal("0.00")
                credit_val = Decimal("0.00")
                bal_val = Decimal("0.00")

                if len(cleaned_cells) >= 7:
                    val_date = DataNormalizer.parse_date(cleaned_cells[1])
                    narration = cleaned_cells[2]
                    ref_num = cleaned_cells[3] or None
                    debit_val = DataNormalizer.parse_currency(cleaned_cells[4])
                    credit_val = DataNormalizer.parse_currency(cleaned_cells[5])
                    bal_val = DataNormalizer.parse_currency(cleaned_cells[6])
                elif len(cleaned_cells) == 6:
                    narration = cleaned_cells[1]
                    ref_num = cleaned_cells[2] or None
                    debit_val = DataNormalizer.parse_currency(cleaned_cells[3])
                    credit_val = DataNormalizer.parse_currency(cleaned_cells[4])
                    bal_val = DataNormalizer.parse_currency(cleaned_cells[5])
                elif len(cleaned_cells) == 5:
                    narration = cleaned_cells[1]
                    debit_val = DataNormalizer.parse_currency(cleaned_cells[2])
                    credit_val = DataNormalizer.parse_currency(cleaned_cells[3])
                    bal_val = DataNormalizer.parse_currency(cleaned_cells[4])

                current_txn = RawTransaction(
                    transaction_date=txn_date,
                    value_date=val_date or txn_date,
                    narration=narration,
                    raw_text=" | ".join(cleaned_cells),
                    reference_number=ref_num,
                    cheque_number=None,
                    debit_amount=debit_val,
                    credit_amount=credit_val,
                    balance=bal_val,
                    source_page=page_number,
                    source_row=row_idx,
                    confidence_score=Decimal("0.98")
                )
                transactions.append(current_txn)
            else:
                # Continuation row for previous transaction's narration
                if current_txn and cleaned_cells:
                    cont_text = " ".join([c for c in cleaned_cells if c])
                    if cont_text and not any(k in cont_text.upper() for k in ["OPENING BALANCE", "CLOSING BALANCE", "TOTAL"]):
                        current_txn.narration += f" {cont_text}"
                        current_txn.raw_text += f"\n{cont_text}"

        return transactions
