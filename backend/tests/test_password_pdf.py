import unittest
from decimal import Decimal
from pathlib import Path
import fitz
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from app.extraction.pipeline import ExtractionPipeline
from app.exports.excel_generator import ExcelExportService

class TestPasswordProtectedPDF(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.plain_pdf = Path("test_plain_temp.pdf")
        cls.encrypted_pdf = Path("test_encrypted_statement.pdf")
        cls.password = "Hdfc@2026"

        # 1. Build plain PDF
        doc = SimpleDocTemplate(str(cls.plain_pdf), pagesize=letter)
        styles = getSampleStyleSheet()
        story = [
            Paragraph("<b>HDFC BANK STATEMENT</b>", styles["Title"]),
            Paragraph("Customer: Acme Trading LLP | Account: XXXXXX9921", styles["Normal"]),
            Spacer(1, 20),
            Table([
                ["Date", "Narration", "Ref No", "Debit", "Credit", "Balance"],
                ["01/04/2025", "OPENING BALANCE", "", "", "50,000.00", "50,000.00"],
                ["10/04/2025", "UPI/OFFICE RENT", "UPI1234", "15,000.00", "", "35,000.00"],
            ], style=[("GRID", (0, 0), (-1, -1), 1, colors.black)])
        ]
        doc.build(story)

        # 2. Encrypt PDF using PyMuPDF
        fitz_doc = fitz.open(str(cls.plain_pdf))
        # Encrypt with owner and user password
        perm = fitz.PDF_PERM_ACCESSIBILITY | fitz.PDF_PERM_PRINT
        fitz_doc.save(
            str(cls.encrypted_pdf),
            encryption=fitz.PDF_ENCRYPT_AES_256,
            owner_pw="OwnerSecret123",
            user_pw=cls.password,
            permissions=perm
        )
        fitz_doc.close()

    @classmethod
    def tearDownClass(cls):
        if cls.plain_pdf.exists():
            cls.plain_pdf.unlink()
        if cls.encrypted_pdf.exists():
            cls.encrypted_pdf.unlink()
        unlocked = Path("test_encrypted_statement_unlocked.pdf")
        if unlocked.exists():
            unlocked.unlink()

    def test_encryption_detection(self):
        # 1. Verify detection
        is_enc = ExtractionPipeline.check_pdf_encryption(str(self.encrypted_pdf))
        self.assertTrue(is_enc)

    def test_missing_password_raises(self):
        # 2. Attempt process without password -> Must raise ValueError with PASSWORD_REQUIRED
        with self.assertRaises(ValueError) as ctx:
            ExtractionPipeline.process_pdf(str(self.encrypted_pdf))
        self.assertIn("PASSWORD_REQUIRED", str(ctx.exception))

    def test_wrong_password_raises(self):
        # 3. Attempt process with wrong password -> Must raise ValueError with INVALID_PASSWORD
        with self.assertRaises(ValueError) as ctx:
            ExtractionPipeline.process_pdf(str(self.encrypted_pdf), password="WrongPassword999")
        self.assertIn("INVALID_PASSWORD", str(ctx.exception))

    def test_correct_password_unlocks_and_extracts(self):
        # 4. Attempt process with correct password -> Must succeed, decrypt and extract!
        result = ExtractionPipeline.process_pdf(str(self.encrypted_pdf), password=self.password)
        self.assertIsNotNone(result)
        self.assertIn("transactions", result)
        self.assertGreaterEqual(len(result["transactions"]), 1)
        self.assertEqual(result["bank_name"], "HDFC Bank")

if __name__ == "__main__":
    unittest.main()
