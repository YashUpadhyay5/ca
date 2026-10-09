import re
from typing import List, Optional, Dict
from datetime import date
from decimal import Decimal
from app.extraction.parsers.base import BaseBankParser, RawTransaction
from app.extraction.normalizer import DataNormalizer

class GenericBankParser(BaseBankParser):
    """Adaptive Universal Parser for Indian Bank Statements using heuristic column alignment."""

    @property
    def bank_name(self) -> str:
        return "Generic Indian Bank"

    def detect(self, sample_text: str) -> bool:
        return True

    def _classify_columns(self, header_row: List[str]) -> Dict[str, int]:
        col_map: Dict[str, int] = {}
        for idx, col in enumerate(header_row):
            c = str(col or "").strip().upper()
            if not c:
                continue

            if any(k in c for k in ["S NO", "SL NO", "SR NO"]) or c == "NO.":
                col_map["s_no"] = idx
            elif any(k in c for k in ["VALUE DATE", "VAL DATE", "VAL DT", "VALUE DT"]):
                col_map["val_date"] = idx
            elif any(k in c for k in ["TXN DATE", "TRANS DATE", "POSTING DATE", "TRAN DATE", "TRANSACTION DATE"]) or (c == "DATE" and "date" not in col_map):
                col_map["date"] = idx
            elif any(k in c for k in ["NARRATION", "PARTICULAR", "DESCRIPTION", "REMARK", "DETAILS", "TRANSACTION REMARKS"]):
                col_map["narration"] = idx
            elif any(k in c for k in ["CHQ", "CHEQUE", "REF NO", "REF.", "UTR", "RRN", "TRANSACTION ID", "CHEQUE NUMBER"]):
                col_map["ref"] = idx
            elif any(k in c for k in ["WITHDRAWAL", "DEBIT", "DR AMT", "DR."]):
                col_map["debit"] = idx
            elif any(k in c for k in ["DEPOSIT", "CREDIT", "CR AMT", "CR."]):
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

        # 1. Look for header row in top 15 rows
        for i, row in enumerate(table[:15]):
            detected = self._classify_columns(row)
            if "date" in detected and ("debit" in detected or "credit" in detected or "balance" in detected):
                header_idx = i
                col_map = detected
                break

        if header_idx == -1 or "date" not in col_map:
            col_map = {
                "date": 0,
                "narration": 1 if len(table[0]) > 1 else 0,
                "debit": len(table[0]) - 3 if len(table[0]) >= 4 else -1,
                "credit": len(table[0]) - 2 if len(table[0]) >= 4 else -1,
                "balance": len(table[0]) - 1 if len(table[0]) >= 3 else -1
            }
            header_idx = 0

        current_txn: Optional[RawTransaction] = None

        for row_idx, row in enumerate(table[header_idx + 1:], start=header_idx + 1):
            if not row or not any(row):
                continue

            cleaned = [str(c or "").strip() for c in row]
            row_str = " ".join(cleaned).upper()
            if any(k in row_str for k in ["PAGE NO", "STATEMENT SUMMARY", "CONTINUED ON NEXT PAGE", "TOTAL", "SINCERELY", "SYSTEM GENERATED"]):
                continue

            date_idx = col_map.get("date", 0)
            candidate_date_str = cleaned[date_idx] if date_idx < len(cleaned) else ""
            parsed_date = DataNormalizer.parse_date(candidate_date_str)

            # Fallback: check col 1 if col 0 was not a date
            if not parsed_date and len(cleaned) > 1:
                alt_d = DataNormalizer.parse_date(cleaned[1])
                if alt_d:
                    parsed_date = alt_d
                    date_idx = 1

            if parsed_date:
                narration_idx = col_map.get("narration")
                narration = cleaned[narration_idx] if narration_idx is not None and narration_idx < len(cleaned) else ""

                ref_idx = col_map.get("ref")
                ref_num = cleaned[ref_idx] if ref_idx is not None and ref_idx < len(cleaned) else None

                val_idx = col_map.get("val_date")
                val_date = None
                if val_idx is not None and val_idx < len(cleaned):
                    val_date = DataNormalizer.parse_date(cleaned[val_idx])

                deb_idx = col_map.get("debit")
                debit_val = Decimal("0.00")
                if deb_idx is not None and 0 <= deb_idx < len(cleaned):
                    debit_val = DataNormalizer.parse_currency(cleaned[deb_idx])

                cred_idx = col_map.get("credit")
                credit_val = Decimal("0.00")
                if cred_idx is not None and 0 <= cred_idx < len(cleaned):
                    credit_val = DataNormalizer.parse_currency(cleaned[cred_idx])

                bal_idx = col_map.get("balance")
                bal_val = Decimal("0.00")
                if bal_idx is not None and 0 <= bal_idx < len(cleaned):
                    bal_val = DataNormalizer.parse_currency(cleaned[bal_idx])

                current_txn = RawTransaction(
                    transaction_date=parsed_date,
                    value_date=val_date or parsed_date,
                    narration=narration,
                    raw_text=" | ".join(cleaned),
                    reference_number=ref_num,
                    cheque_number=ref_num if ref_num and ref_num.isdigit() and len(ref_num) == 6 else None,
                    debit_amount=debit_val,
                    credit_amount=credit_val,
                    balance=bal_val,
                    source_page=page_number,
                    source_row=row_idx,
                    confidence_score=Decimal("0.95")
                )
                transactions.append(current_txn)
            else:
                if current_txn and cleaned:
                    cont_text = " ".join([c for c in cleaned if c])
                    if cont_text and not any(k in cont_text.upper() for k in ["OPENING BALANCE", "CLOSING BALANCE", "SINCERELY", "LEGEND"]):
                        current_txn.narration += f" {cont_text}"
                        current_txn.raw_text += f"\n{cont_text}"

        return transactions
