import unittest
from datetime import date
from decimal import Decimal
from app.extraction.normalizer import DataNormalizer

class TestDataNormalizer(unittest.TestCase):

    def test_parse_indian_dates(self):
        # DD/MM/YYYY
        self.assertEqual(DataNormalizer.parse_date("15/08/2025"), date(2025, 8, 15))
        # DD-MM-YYYY
        self.assertEqual(DataNormalizer.parse_date("01-04-2024"), date(2024, 4, 1))
        # DD.MM.YYYY
        self.assertEqual(DataNormalizer.parse_date("31.12.2023"), date(2023, 12, 31))
        # DD-Mon-YYYY
        self.assertEqual(DataNormalizer.parse_date("05-Apr-2025"), date(2025, 4, 5))
        # DD Mon YYYY
        self.assertEqual(DataNormalizer.parse_date("26 Jan 2026"), date(2026, 1, 26))

    def test_parse_indian_currency(self):
        # Standard with comma
        self.assertEqual(DataNormalizer.parse_currency("1,50,000.00"), Decimal("150000.00"))
        # Rupee symbol
        self.assertEqual(DataNormalizer.parse_currency("₹ 25,400.50"), Decimal("25400.50"))
        # Rs prefix
        self.assertEqual(DataNormalizer.parse_currency("Rs. 10,000.75"), Decimal("10000.75"))
        # CR / DR tags
        self.assertEqual(DataNormalizer.parse_currency("5,000.00 Cr"), Decimal("5000.00"))
        self.assertEqual(DataNormalizer.parse_currency("4,500.00 Dr"), Decimal("4500.00"))
        # Parentheses negative
        self.assertEqual(DataNormalizer.parse_currency("(1,200.00)"), Decimal("-1200.00"))
        # Nil or empty
        self.assertEqual(DataNormalizer.parse_currency("-"), Decimal("0.00"))
        self.assertEqual(DataNormalizer.parse_currency(""), Decimal("0.00"))

if __name__ == "__main__":
    unittest.main()
