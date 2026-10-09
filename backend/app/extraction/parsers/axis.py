import re
from typing import List, Optional
from datetime import date
from decimal import Decimal
from app.extraction.parsers.base import BaseBankParser, RawTransaction
from app.extraction.normalizer import DataNormalizer

class AxisBankParser(BaseBankParser):
    """Parser adapter for Axis Bank statements."""

    @property
    def bank_name(self) -> str:
        return "Axis Bank"

    def detect(self, sample_text: str) -> bool:
        upper = sample_text.upper()
        return ("AXIS BANK" in upper or "UTIB0" in upper or "AXISBANK.COM" in upper)

    def parse_page_table(self, table: List[List[str]], page_number: int) -> List[RawTransaction]:
        transactions: List[RawTransaction] = []
        if not table or len(table) < 2:
            return transactions

        header_idx = -1
        for i, row in enumerate(table[:10]):
            row_str = " ".join([str(c) for c in row if c]).upper()
            if ("TRAN DATE" in row_str or "DATE" in row_str) and ("PARTICULARS" in row_str or "PARTICULAR" in row_str):
                header_idx = i
                break

        if header_idx == -1:
            header_idx = 0

        current_txn: Optional[RawTransaction] = None

        for row_idx, row in enumerate(table[header_idx + 1:], start=header_idx + 1):
            if not row or not any(row):
                continue

            cleaned = [str(c or "").strip() for c in row]
            row_str = " ".join(cleaned).upper()
            if "STATEMENT SUMMARY" in row_str or "PAGE NO" in row_str:
                continue

            parsed_date = DataNormalizer.parse_date(cleaned[0]) if cleaned else None

            if parsed_date:
                txn_date = parsed_date
                val_date = None
                narration = ""
                chq_num = None
                debit_val = Decimal("0.00")
                credit_val = Decimal("0.00")
                bal_val = Decimal("0.00")

                # Tran Date | Chq No | Particulars | Debit | Credit | Balance
                if len(cleaned) >= 6:
                    chq_num = cleaned[1] or None
                    narration = cleaned[2]
                    debit_val = DataNormalizer.parse_currency(cleaned[3])
                    credit_val = DataNormalizer.parse_currency(cleaned[4])
                    bal_val = DataNormalizer.parse_currency(cleaned[5])
                elif len(cleaned) == 5:
                    narration = cleaned[1]
                    debit_val = DataNormalizer.parse_currency(cleaned[2])
                    credit_val = DataNormalizer.parse_currency(cleaned[3])
                    bal_val = DataNormalizer.parse_currency(cleaned[4])

                current_txn = RawTransaction(
                    transaction_date=txn_date,
                    value_date=txn_date,
                    narration=narration,
                    raw_text=" | ".join(cleaned),
                    reference_number=chq_num,
                    cheque_number=chq_num if chq_num and chq_num.isdigit() else None,
                    debit_amount=debit_val,
                    credit_amount=credit_val,
                    balance=bal_val,
                    source_page=page_number,
                    source_row=row_idx,
                    confidence_score=Decimal("0.98")
                )
                transactions.append(current_txn)
            else:
                if current_txn and cleaned:
                    cont_text = " ".join([c for c in cleaned if c])
                    if cont_text and not any(k in cont_text.upper() for k in ["OPENING BAL", "CLOSING BAL", "TOTAL"]):
                        current_txn.narration += f" {cont_text}"
                        current_txn.raw_text += f"\n{cont_text}"

        return transactions


class KotakBankParser(BaseBankParser):
    """Parser adapter for Kotak Mahindra Bank statements."""

    @property
    def bank_name(self) -> str:
        return "Kotak Mahindra Bank"

    def detect(self, sample_text: str) -> bool:
        upper = sample_text.upper()
        return ("KOTAK" in upper or "KKBK0" in upper or "KOTAK MAHINDRA" in upper)

    def parse_page_table(self, table: List[List[str]], page_number: int) -> List[RawTransaction]:
        transactions: List[RawTransaction] = []
        if not table or len(table) < 2:
            return transactions

        header_idx = -1
        for i, row in enumerate(table[:10]):
            row_str = " ".join([str(c) for c in row if c]).upper()
            if "DATE" in row_str and ("NARRATION" in row_str or "DESCRIPTION" in row_str):
                header_idx = i
                break

        if header_idx == -1:
            header_idx = 0

        current_txn: Optional[RawTransaction] = None

        for row_idx, row in enumerate(table[header_idx + 1:], start=header_idx + 1):
            if not row or not any(row):
                continue

            cleaned = [str(c or "").strip() for c in row]
            row_str = " ".join(cleaned).upper()
            if "PAGE NO" in row_str or "KOTAK MAHINDRA BANK" in row_str:
                continue

            # Sl No | Date | Description | Chq/Ref | Debit | Credit | Balance
            parsed_date = None
            date_cell_idx = 0
            if len(cleaned) > 1 and cleaned[0].isdigit():
                # First col is serial number
                parsed_date = DataNormalizer.parse_date(cleaned[1])
                date_cell_idx = 1
            else:
                parsed_date = DataNormalizer.parse_date(cleaned[0])
                date_cell_idx = 0

            if parsed_date:
                txn_date = parsed_date
                rem_cells = cleaned[date_cell_idx + 1:]
                narration = rem_cells[0] if len(rem_cells) > 0 else ""
                ref_num = rem_cells[1] if len(rem_cells) > 1 else None
                
                # Assume last 3 cells or subcells are debit, credit, balance
                debit_val = Decimal("0.00")
                credit_val = Decimal("0.00")
                bal_val = Decimal("0.00")

                if len(rem_cells) >= 5:
                    debit_val = DataNormalizer.parse_currency(rem_cells[2])
                    credit_val = DataNormalizer.parse_currency(rem_cells[3])
                    bal_val = DataNormalizer.parse_currency(rem_cells[4])
                elif len(rem_cells) >= 4:
                    debit_val = DataNormalizer.parse_currency(rem_cells[1])
                    credit_val = DataNormalizer.parse_currency(rem_cells[2])
                    bal_val = DataNormalizer.parse_currency(rem_cells[3])

                current_txn = RawTransaction(
                    transaction_date=txn_date,
                    value_date=txn_date,
                    narration=narration,
                    raw_text=" | ".join(cleaned),
                    reference_number=ref_num,
                    cheque_number=ref_num if ref_num and ref_num.isdigit() else None,
                    debit_amount=debit_val,
                    credit_amount=credit_val,
                    balance=bal_val,
                    source_page=page_number,
                    source_row=row_idx,
                    confidence_score=Decimal("0.98")
                )
                transactions.append(current_txn)
            else:
                if current_txn and cleaned:
                    cont_text = " ".join([c for c in cleaned if c])
                    if cont_text and not any(k in cont_text.upper() for k in ["OPENING BAL", "CLOSING BAL"]):
                        current_txn.narration += f" {cont_text}"
                        current_txn.raw_text += f"\n{cont_text}"

        return transactions
