import unittest
from decimal import Decimal
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from app.core.database import SessionLocal, init_db
from app.models.organization import Organization
from app.models.user import User
from app.models.client import Client
from app.models.document import Document
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.extraction.pipeline import ExtractionPipeline
from app.calculations.engine import CalculationEngine
from app.exports.excel_generator import ExcelExportService

class TestEndToEndPDFWorkflow(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.test_pdf_path = Path("test_sbi_statement.pdf")
        
        # Build synthetic SBI PDF using reportlab
        doc = SimpleDocTemplate(str(cls.test_pdf_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("<b>STATE BANK OF INDIA</b>", styles["Title"]))
        story.append(Paragraph("Account Statement: <b>XXXXXX4812</b>", styles["Normal"]))
        story.append(Paragraph("Customer: Acme Solutions Pvt Ltd | Period: 01/04/2025 to 30/04/2025", styles["Normal"]))
        story.append(Spacer(1, 15))

        table_data = [
            ["Txn Date", "Value Date", "Description", "Ref No./Cheque No.", "Debit", "Credit", "Balance"],
            ["01/04/2025", "01/04/2025", "BY TRANSFER / CLIENT SETTLEMENT", "RTGS10293", "", "2,00,000.00", "5,00,000.00"],
            ["05/04/2025", "05/04/2025", "NEFT DR-CBIC GST PAYMENT CHALLAN", "GST881920", "28,500.00", "", "4,71,500.00"],
            ["10/04/2025", "10/04/2025", "UPI/DR/1920/AMAZON/AWS CLOUD", "UPI992019", "12,400.00", "", "4,59,100.00"],
            ["15/04/2025", "15/04/2025", "ACH DR-OFFICE RENT NARIMAN PT", "ACH441029", "50,000.00", "", "4,09,100.00"],
            ["25/04/2025", "25/04/2025", "INT.PAID SAVINGS BANK", "INT99182", "", "3,200.00", "4,12,300.00"]
        ]

        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.navy),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        story.append(t)
        doc.build(story)

    @classmethod
    def tearDownClass(cls):
        if cls.test_pdf_path.exists():
            cls.test_pdf_path.unlink()

    def test_pipeline_on_real_pdf(self):
        # 1. Run Extraction Pipeline
        result = ExtractionPipeline.process_pdf(str(self.test_pdf_path))
        
        self.assertEqual(result["bank_name"], "State Bank of India")
        self.assertEqual(result["account_number"], "XXXXXX4812")
        self.assertEqual(result["total_transactions"], 5)
        self.assertEqual(result["reconciliation_status"], "RECONCILED")
        self.assertEqual(result["total_credits"], Decimal("203200.00"))
        self.assertEqual(result["total_debits"], Decimal("90900.00"))
        self.assertEqual(result["net_movement"], Decimal("112300.00"))
        self.assertEqual(result["closing_balance"], Decimal("412300.00"))

        # Verify Narration NLP on extracted rows
        txns = result["transactions"]
        gst_txn = next(t for t in txns if "GST" in t["narration"])
        self.assertEqual(gst_txn["category"], "Tax")
        self.assertEqual(gst_txn["subcategory"], "GST")

        aws_txn = next(t for t in txns if "AMAZON" in t["narration"])
        self.assertEqual(aws_txn["payment_mode"], "UPI")

if __name__ == "__main__":
    unittest.main()
