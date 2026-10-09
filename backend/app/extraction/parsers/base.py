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
