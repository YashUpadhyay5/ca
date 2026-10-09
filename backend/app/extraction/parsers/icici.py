import re
from typing import List, Optional, Dict
from datetime import date
from decimal import Decimal
from app.extraction.parsers.base import BaseBankParser, RawTransaction
from app.extraction.normalizer import DataNormalizer

class ICICIBankParser(BaseBankParser):
    """Adaptive Parser adapter for ICICI Bank statements."""

    @property
    def bank_name(self) -> str:
        return "ICICI Bank"

    def detect(self, sample_text: str) -> bool:
        upper = sample_text.upper()
        return ("ICICI BANK" in upper or "ICIC0" in upper or "ICICIBANK.COM" in upper or "ICICI" in upper)

    def _classify_columns(self, header_row: List[str]) -> Dict[str, int]:
        col_map: Dict[str, int] = {}
        for idx, col in enumerate(header_row):
            c = str(col or "").strip().upper()
            if not c:
                continue
            if any(k in c for k in ["S NO", "SL NO", "SR NO"]) or c == "NO.":
                col_map["s_no"] = idx
            elif any(k in c for k in ["VALUE DATE", "VAL DATE", "VAL DT"]):
                col_map["val_date"] = idx
            elif any(k in c for k in ["TRANSACTION DATE", "TXN DATE", "DATE"]):
                col_map["date"] = idx
            elif any(k in c for k in ["CHEQUE NUMBER", "CHQ NO", "CHEQUE", "CHQ", "REF NO", "REF"]):
                col_map["chq"] = idx
            elif any(k in c for k in ["TRANSACTION REMARKS", "REMARKS", "PARTICULARS", "DESCRIPTION", "NARRATION"]):
                col_map["narration"] = idx
            elif any(k in c for k in ["WITHDRAWAL AMOUNT", "WITHDRAWAL", "DEBIT", "DR AMT", "DR"]):
                col_map["debit"] = idx
            elif any(k in c for k in ["DEPOSIT AMOUNT", "DEPOSIT", "CREDIT", "CR AMT", "CR"]):
                col_map["credit"] = idx
            elif any(k in c for k in ["BALANCE", "CLOSING BAL", "BAL"]):
                col_map["balance"] = idx
        return col_map

    def parse_page_table(self, table: List[List[str]], page_number: int) -> List[RawTransaction]:
        transactions: List[RawTransaction] = []
        if not table or len(table) < 2:
            return transactions

        header_idx = -1
        col_map: Dict[str, int] = {}

        for i, row in enumerate(table[:10]):
            classified = self._classify_columns(row)
            if "date" in classified and ("debit" in classified or "credit" in classified or "balance" in classified):
                header_idx = i
                col_map = classified
                break

        current_txn: Optional[RawTransaction] = None
        start_row = header_idx + 1 if header_idx != -1 else 0

        for row_idx, row in enumerate(table[start_row:], start=start_row):
            if not row or not any(row):
                continue

            cleaned = [str(c or "").strip() for c in row]
            row_str = " ".join(cleaned).upper()
            if any(k in row_str for k in ["PAGE NO", "LEGEND", "TOTALS", "SINCERELY", "SYSTEM GENERATED"]):
                continue

            # Determine date
            txn_date: Optional[date] = None
            date_idx = col_map.get("date")

            if date_idx is not None and date_idx < len(cleaned):
                txn_date = DataNormalizer.parse_date(cleaned[date_idx])
            else:
                # Fallback: check col 0 or col 1
                d0 = DataNormalizer.parse_date(cleaned[0]) if cleaned else None
                if d0:
                    txn_date = d0
                    date_idx = 0
                elif len(cleaned) > 1:
                    d1 = DataNormalizer.parse_date(cleaned[1])
                    if d1:
                        txn_date = d1
                        date_idx = 1

            if txn_date:
                # Transaction row start
                val_date = txn_date
                val_idx = col_map.get("val_date")
                if val_idx is not None and val_idx < len(cleaned):
                    vd = DataNormalizer.parse_date(cleaned[val_idx])
                    if vd:
                        val_date = vd

                # Cheque / Ref
                chq_idx = col_map.get("chq")
                chq_num = None
                if chq_idx is not None and chq_idx < len(cleaned):
                    raw_chq = cleaned[chq_idx].strip()
                    if raw_chq and not any(k in raw_chq.upper() for k in ["UPI", "IMPS", "NEFT"]):
                        chq_num = raw_chq

                # Narration
                narr_idx = col_map.get("narration")
                if narr_idx is not None and narr_idx < len(cleaned):
                    narration = cleaned[narr_idx]
                else:
                    # Positional fallback
                    if len(cleaned) >= 7 and date_idx == 1:
                        narration = cleaned[3]
                    elif len(cleaned) >= 6 and date_idx == 0:
                        narration = cleaned[1]
                    else:
                        narration = " ".join(cleaned[2:-3]) if len(cleaned) > 5 else cleaned[1]

                # Debit
                deb_idx = col_map.get("debit")
                if deb_idx is not None and deb_idx < len(cleaned):
                    debit_val = DataNormalizer.parse_currency(cleaned[deb_idx])
                elif len(cleaned) >= 7 and date_idx == 1:
                    debit_val = DataNormalizer.parse_currency(cleaned[4])
                elif len(cleaned) >= 6 and date_idx == 0:
                    debit_val = DataNormalizer.parse_currency(cleaned[3])
                else:
                    debit_val = Decimal("0.00")

                # Credit
                cred_idx = col_map.get("credit")
                if cred_idx is not None and cred_idx < len(cleaned):
                    credit_val = DataNormalizer.parse_currency(cleaned[cred_idx])
                elif len(cleaned) >= 7 and date_idx == 1:
                    credit_val = DataNormalizer.parse_currency(cleaned[5])
                elif len(cleaned) >= 6 and date_idx == 0:
                    credit_val = DataNormalizer.parse_currency(cleaned[4])
                else:
                    credit_val = Decimal("0.00")

                # Balance
                bal_idx = col_map.get("balance")
                if bal_idx is not None and bal_idx < len(cleaned):
                    bal_val = DataNormalizer.parse_currency(cleaned[bal_idx])
                elif len(cleaned) >= 7 and date_idx == 1:
                    bal_val = DataNormalizer.parse_currency(cleaned[6])
                elif len(cleaned) >= 6 and date_idx == 0:
                    bal_val = DataNormalizer.parse_currency(cleaned[5])
                else:
                    bal_val = Decimal("0.00")

                current_txn = RawTransaction(
                    transaction_date=txn_date,
                    value_date=val_date,
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
                # Continuation row for narration
                if current_txn and cleaned:
                    cont_text = " ".join([c for c in cleaned if c])
                    if cont_text and not any(k in cont_text.upper() for k in ["TOTAL", "OPENING BAL", "CLOSING BAL", "SINCERELY", "LEGEND"]):
                        current_txn.narration += f" {cont_text}"
                        current_txn.raw_text += f"\n{cont_text}"

        return transactions
