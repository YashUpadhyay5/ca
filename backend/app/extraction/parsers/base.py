from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import date
from decimal import Decimal

@dataclass
class RawTransaction:
    transaction_date: Optional[date]
    value_date: Optional[date]
    narration: str
    raw_text: str
    reference_number: Optional[str]
    cheque_number: Optional[str]
    debit_amount: Decimal
    credit_amount: Decimal
    balance: Decimal
    source_page: int
    source_row: int
    confidence_score: Decimal = Decimal("1.00")
    metadata: Optional[Dict[str, Any]] = None

class BaseBankParser(ABC):
    """Abstract Base Class for all Bank Statement Parser Adapters."""

    def __init__(self):
        self.current_col_map: Optional[Dict[str, int]] = None
        self.last_txn: Optional[RawTransaction] = None

    def reset(self):
        """Resets document-level parser state for a new statement extraction."""
        self.current_col_map = None
        self.last_txn = None

    @property
    @abstractmethod
    def bank_name(self) -> str:
        """Name of the bank handled by this parser."""
        pass

    @abstractmethod
    def detect(self, sample_text: str) -> bool:
        """Determines if the PDF belongs to this bank."""
        pass

    @abstractmethod
    def parse_page_table(self, table: List[List[str]], page_number: int) -> List[RawTransaction]:
        """Parses extracted 2D table grid from a page into RawTransaction objects."""
        pass

    @classmethod
    def infer_columns_from_data(cls, table: List[List[str]]) -> Dict[str, int]:
        """
        Dynamically infers column mapping directly from data patterns when header row
        is absent, obscured, or non-standard across any Indian bank statement.
        """
        from app.extraction.normalizer import DataNormalizer
        col_map: Dict[str, int] = {}
        if not table or len(table) < 2:
            return col_map

        num_cols = max(len(row) for row in table[:15] if row)
        date_candidates = {}
        currency_candidates = {}
        text_lengths = {c: 0 for c in range(num_cols)}

        sample_rows = [r for r in table[:20] if r and any(r)]
        total_samples = len(sample_rows)
        if total_samples == 0:
            return col_map

        for row in sample_rows:
            for c_idx in range(min(num_cols, len(row))):
                val = str(row[c_idx] or "").strip()
                if not val:
                    continue
                # Date check
                if DataNormalizer.parse_date(val):
                    date_candidates[c_idx] = date_candidates.get(c_idx, 0) + 1
                
                # Currency check
                curr = DataNormalizer.parse_currency(val)
                if curr > 0:
                    currency_candidates[c_idx] = currency_candidates.get(c_idx, 0) + 1

                # Length for narration
                text_lengths[c_idx] += len(val)

        # 1. Identify Date Column(s)
        sorted_dates = sorted(
            [c for c, count in date_candidates.items() if count >= max(1, total_samples // 3)],
            key=lambda c: date_candidates[c],
            reverse=True
        )
        if sorted_dates:
            col_map["date"] = sorted_dates[0]
            if len(sorted_dates) > 1:
                col_map["val_date"] = sorted_dates[1]

        # 2. Identify Currency Columns (Debit, Credit, Balance)
        valid_curr_cols = sorted(
            [c for c, count in currency_candidates.items() if count >= max(1, total_samples // 3) and c != col_map.get("date")],
            key=lambda c: c
        )

        if len(valid_curr_cols) >= 3:
            col_map["debit"] = valid_curr_cols[-3]
            col_map["credit"] = valid_curr_cols[-2]
            col_map["balance"] = valid_curr_cols[-1]
        elif len(valid_curr_cols) == 2:
            col_map["debit"] = valid_curr_cols[0]
            col_map["balance"] = valid_curr_cols[1]
        elif len(valid_curr_cols) == 1:
            col_map["balance"] = valid_curr_cols[0]

        # 3. Identify Narration Column (longest remaining text column)
        reserved = set(col_map.values())
        remaining = [c for c in range(num_cols) if c not in reserved]
        if remaining:
            longest_col = max(remaining, key=lambda c: text_lengths.get(c, 0))
            col_map["narration"] = longest_col
            reserved.add(longest_col)

        # 4. Identify Ref / Chq Column (any remaining column with medium text / numeric IDs)
        for c in range(num_cols):
            if c not in reserved:
                col_map["chq"] = c
                break

        return col_map
