import unittest
from decimal import Decimal
from app.extraction.parsers.sbi import SBIBankParser
from app.extraction.parsers.hdfc import HDFCBankParser
from app.extraction.parsers.icici import ICICIBankParser
from app.extraction.parsers.axis import AxisBankParser
from app.extraction.parsers.generic import GenericBankParser
from app.extraction.narration_nlp import NarrationNLP

class TestBankParsers(unittest.TestCase):

    def test_sbi_parser(self):
        parser = SBIBankParser()
        self.assertTrue(parser.detect("STATE BANK OF INDIA - ACCOUNT STATEMENT"))
        
        sample_table = [
            ["Txn Date", "Value Date", "Description", "Ref No./Cheque No.", "Debit", "Credit", "Balance"],
            ["01/04/2025", "01/04/2025", "TRANSFER TO 34918239/SALARY", "TRANSFER", "", "1,50,000.00", "2,50,000.00"],
            ["03/04/2025", "03/04/2025", "UPI/DR/12345/AMAZON/Axis", "UPI12345", "4,500.00", "", "2,45,500.00"],
            ["", "", "Continuation of previous txn description", "", "", "", ""]
        ]
        txns = parser.parse_page_table(sample_table, page_number=1)
        self.assertEqual(len(txns), 2)
        self.assertEqual(txns[0].credit_amount, Decimal("150000.00"))
        self.assertEqual(txns[1].debit_amount, Decimal("4500.00"))
        self.assertIn("Continuation", txns[1].narration)

    def test_hdfc_parser(self):
        parser = HDFCBankParser()
        self.assertTrue(parser.detect("HDFC BANK LIMITED - STATEMENT OF ACCOUNTS"))

        sample_table = [
            ["Date", "Narration", "Chq./Ref.No.", "Value Dt", "Withdrawal Amt.", "Deposit Amt.", "Closing Balance"],
            ["05/05/2025", "NEFT DR-TAX PAYMENT-GST 3B", "N12345678", "05/05/2025", "45,000.00", "", "5,55,000.00"],
            ["10/05/2025", "UPI-SWIGGY-BANGALORE", "UPI98765", "10/05/2025", "850.00", "", "5,54,150.00"]
        ]
        txns = parser.parse_page_table(sample_table, page_number=1)
        self.assertEqual(len(txns), 2)
        self.assertEqual(txns[0].debit_amount, Decimal("45000.00"))
        self.assertEqual(txns[1].debit_amount, Decimal("850.00"))

    def test_narration_nlp(self):
        # UPI VPA extraction
        res_upi = NarrationNLP.parse("UPI/DR/48192019/RAHUL@OKSBI/AMAZON PAY")
        self.assertEqual(res_upi["payment_mode"], "UPI")
        self.assertEqual(res_upi["upi_id"], "rahul@oksbi")
        self.assertEqual(res_upi["merchant"], "Amazon")

        # GST detection
        res_gst = NarrationNLP.parse("NEFT DR-CBIC GST PAYMENT CHALLAN 280")
        self.assertEqual(res_gst["payment_mode"], "NEFT")
        self.assertEqual(res_gst["category"], "Tax")
        self.assertEqual(res_gst["subcategory"], "GST")

        # Salary detection
        res_sal = NarrationNLP.parse("ACH CR-SALARY FOR APRIL 2025")
        self.assertEqual(res_sal["category"], "Salary")

if __name__ == "__main__":
    unittest.main()
