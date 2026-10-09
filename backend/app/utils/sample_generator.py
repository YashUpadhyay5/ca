from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def generate_sample_statements(target_dir: Path):
    """Generates realistic sample bank statement PDFs for demonstration and testing."""
    target_dir.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()

    # 1. SBI Sample Statement
    sbi_path = target_dir / "sample_sbi_current_account.pdf"
    doc_sbi = SimpleDocTemplate(str(sbi_path), pagesize=letter)
    story_sbi = [
        Paragraph("<b>STATE BANK OF INDIA</b>", styles["Title"]),
        Paragraph("<b>Commercial Branch, Nariman Point, Mumbai</b>", styles["Normal"]),
        Paragraph("Account No: <b>38920192841</b> | IFSC: SBIN0001822", styles["Normal"]),
        Paragraph("Account Name: <b>Acme Solutions Pvt Ltd</b>", styles["Normal"]),
        Paragraph("Statement Period: <b>01/04/2025 to 30/04/2025</b>", styles["Normal"]),
        Spacer(1, 15)
    ]
    sbi_table = [
        ["Txn Date", "Value Date", "Description", "Ref No./Cheque No.", "Debit", "Credit", "Balance"],
        ["01/04/2025", "01/04/2025", "BY TRANSFER / CLIENT SETTLEMENT INFOSYS", "RTGS10293", "", "4,50,000.00", "7,50,000.00"],
        ["05/04/2025", "05/04/2025", "NEFT DR-CBIC GST PAYMENT CHALLAN 280", "GST881920", "42,500.00", "", "7,07,500.00"],
        ["08/04/2025", "08/04/2025", "UPI/DR/1920/AMAZON/AWS CLOUD HOSTING", "UPI992019", "18,400.00", "", "6,89,100.00"],
        ["10/04/2025", "10/04/2025", "ACH DR-OFFICE RENT NARIMAN POINT", "ACH441029", "85,000.00", "", "6,04,100.00"],
        ["15/04/2025", "15/04/2025", "SALARY PAYMENT APRIL 2025 STAFF", "NEFT49102", "2,10,000.00", "", "3,94,100.00"],
        ["20/04/2025", "20/04/2025", "UPI/DR/8812/SWIGGY/TEAM LUNCH", "UPI391029", "3,450.00", "", "3,90,650.00"],
        ["22/04/2025", "22/04/2025", "SELF CHEQUE CASH WITHDRAWAL", "CHQ001245", "45,000.00", "", "3,45,650.00"],
        ["25/04/2025", "25/04/2025", "INT.PAID SAVINGS BANK", "INT99182", "", "4,850.00", "3,50,500.00"],
        ["28/04/2025", "28/04/2025", "UPI/DR/9920/RELIANCE PETROL PUMP", "UPI552910", "4,200.00", "", "3,46,300.00"],
        ["30/04/2025", "30/04/2025", "INCOME TAX ADVANCE TAX CHALLAN 280", "ITR991029", "50,000.00", "", "2,96,300.00"]
    ]
    t_sbi = Table(sbi_table)
    t_sbi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.navy),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story_sbi.append(t_sbi)
    doc_sbi.build(story_sbi)

    # 2. HDFC Sample Statement
    hdfc_path = target_dir / "sample_hdfc_current_account.pdf"
    doc_hdfc = SimpleDocTemplate(str(hdfc_path), pagesize=letter)
    story_hdfc = [
        Paragraph("<b>HDFC BANK LIMITED</b>", styles["Title"]),
        Paragraph("<b>Corporate Banking Division, Fort, Mumbai</b>", styles["Normal"]),
        Paragraph("Account No: <b>50200049182910</b> | IFSC: HDFC0000240", styles["Normal"]),
        Paragraph("Account Name: <b>Acme Solutions Pvt Ltd</b>", styles["Normal"]),
        Paragraph("Statement Period: <b>01/04/2025 to 30/04/2025</b>", styles["Normal"]),
        Spacer(1, 15)
    ]
    hdfc_table = [
        ["Date", "Narration", "Chq./Ref.No.", "Value Dt", "Withdrawal Amt.", "Deposit Amt.", "Closing Balance"],
        ["02/04/2025", "NEFT CR-TCS VENDOR SETTLEMENT", "N88291029", "02/04/2025", "", "3,50,000.00", "5,50,000.00"],
        ["07/04/2025", "TDS DEDUCTED SECTION 194J", "TDS441920", "07/04/2025", "35,000.00", "", "5,15,000.00"],
        ["12/04/2025", "UPI-ZERODHA BROKING-INVESTMENT", "UPI881923", "12/04/2025", "50,000.00", "", "4,65,000.00"],
        ["18/04/2025", "HDFC LOAN EMI REPAYMENT", "EMI991024", "18/04/2025", "32,500.00", "", "4,32,500.00"],
        ["26/04/2025", "ELECTRICITY BILL TATA POWER", "EB4910291", "26/04/2025", "8,400.00", "", "4,24,100.00"],
        ["30/04/2025", "SMS CHARGES & AMC FEES", "CHG102931", "30/04/2025", "1,180.00", "", "4,22,920.00"]
    ]
    t_hdfc = Table(hdfc_table)
    t_hdfc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.navy),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story_hdfc.append(t_hdfc)
    doc_hdfc.build(story_hdfc)

    return [sbi_path, hdfc_path]

if __name__ == "__main__":
    generate_sample_statements(Path("sample_statements"))
    print("Generated sample statements successfully!")
