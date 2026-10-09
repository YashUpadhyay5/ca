import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple

class DataNormalizer:
    """Enterprise normalizer for Indian banking dates, currency formats, and numerical values."""

    DATE_PATTERNS = [
        # DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY
        r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})$",
        # DD/MM/YY or DD-MM-YY
        r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{2})$",
        # YYYY-MM-DD
        r"^(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})$",
        # DD-Mon-YYYY or DD Mon YYYY (e.g. 05-Apr-2024, 15 Oct 2025)
        r"^(\d{1,2})[- ]([A-Za-z]{3})[- ](\d{4})$",
        # DD-Mon-YY
        r"^(\d{1,2})[- ]([A-Za-z]{3})[- ](\d{2})$",
    ]

    MONTH_MAP = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
    }

    @classmethod
    def parse_date(cls, raw_date_str: str) -> Optional[date]:
        """
        Parses Indian bank date string into datetime.date.
        Prioritizes DD/MM/YYYY over MM/DD/YYYY standard for Indian banks.
        """
        if not raw_date_str:
            return None
        
        cleaned = " ".join(raw_date_str.strip().replace("\n", " ").split())
        
        # 1. Match DD-Mon-YYYY (e.g., 01-Jan-2025)
        match_mon = re.match(r"^(\d{1,2})[- /]([A-Za-z]{3})[- /](\d{2,4})$", cleaned, re.IGNORECASE)
        if match_mon:
            day = int(match_mon.group(1))
            mon_str = match_mon.group(2).lower()
            year_val = int(match_mon.group(3))
            if year_val < 100:
                year_val += 2000
            month = cls.MONTH_MAP.get(mon_str)
            if month:
                try:
                    return date(year_val, month, day)
                except ValueError:
                    pass

        # 2. Match DD/MM/YYYY or DD-MM-YYYY
        match_ddmmyyyy = re.match(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})$", cleaned)
        if match_ddmmyyyy:
            p1 = int(match_ddmmyyyy.group(1))
            p2 = int(match_ddmmyyyy.group(2))
            year = int(match_ddmmyyyy.group(3))
            if year < 100:
                year += 2000
            
            # Indian banking standard: p1 is day, p2 is month
            try:
                return date(year, p2, p1)
            except ValueError:
                # Fallback if p1 was month (e.g. some foreign banks in India)
                try:
                    return date(year, p1, p2)
                except ValueError:
                    pass

        # 3. Match YYYY-MM-DD
        match_iso = re.match(r"^(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})$", cleaned)
        if match_iso:
            try:
                return date(int(match_iso.group(1)), int(match_iso.group(2)), int(match_iso.group(3)))
            except ValueError:
                pass

        return None

    @classmethod
    def parse_currency(cls, raw_amount: str) -> Decimal:
        """
        Cleans and parses monetary strings into exact Decimal.
        Handles: ₹, Rs, commas (1,00,000.00), CR/DR indicators, and negative brackets.
        """
        if not raw_amount:
            return Decimal("0.00")
        
        val_str = str(raw_amount).strip()
        if not val_str or val_str.lower() in ("-", "--", "nil", "none", "nan"):
            return Decimal("0.00")

        # Strip symbols
        val_str = re.sub(r"[₹$€£\s]", "", val_str)
        val_str = re.sub(r"(?i)rs\.?", "", val_str)
        val_str = re.sub(r"(?i)inr", "", val_str)

        # Detect negative in parentheses e.g. (1,500.00)
        is_negative = False
        if val_str.startswith("(") and val_str.endswith(")"):
            is_negative = True
            val_str = val_str[1:-1]
        elif val_str.startswith("-"):
            is_negative = True
            val_str = val_str[1:]

        # Strip CR / DR if trailing
        val_str = re.sub(r"(?i)(cr|dr)\.?$", "", val_str).strip()

        # Remove Indian thousands grouping commas (e.g. 10,00,000.50 -> 1000000.50)
        val_str = val_str.replace(",", "")

        try:
            dec = Decimal(val_str).quantize(Decimal("0.01"))
            return -dec if is_negative else dec
        except (InvalidOperation, ValueError):
            m = re.search(r"(\d+(?:\.\d{1,2})?)", val_str)
            if m:
                try:
                    dec = Decimal(m.group(1)).quantize(Decimal("0.01"))
                    return -dec if is_negative else dec
                except Exception:
                    pass
            return Decimal("0.00")

    @classmethod
    def detect_debit_credit_balance(
        cls, 
        withdrawal_col: str, 
        deposit_col: str, 
        balance_col: str
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """Extracts exact debit, credit, and running balance from cell strings."""
        debit = cls.parse_currency(withdrawal_col)
        credit = cls.parse_currency(deposit_col)
        balance = cls.parse_currency(balance_col)
        return debit, credit, balance
