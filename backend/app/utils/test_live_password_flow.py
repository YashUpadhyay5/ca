import requests
import time
import sys
from pathlib import Path
import fitz
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table
from reportlab.lib.styles import getSampleStyleSheet

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def test_live_password_flow():
    print("=" * 70)
    print("   TESTING LIVE PASSWORD-PROTECTED STATEMENT PIPELINE")
    print("=" * 70)

    # 1. Login
    login = requests.post(
        "http://127.0.0.1:8000/api/v1/auth/login",
        json={"email": "ca@mehtaca.com", "password": "AuditPassword123!"}
    ).json()
    token = login["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("1. Logged in as:", login["user"]["full_name"])

    # 2. Generate an encrypted bank statement PDF
    plain_pdf = Path("test_plain_temp.pdf")
    enc_pdf = Path("test_encrypted_live.pdf")
    secret_pwd = "SBI@1234"

    doc = SimpleDocTemplate(str(plain_pdf), pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("<b>STATE BANK OF INDIA</b>", styles["Title"]),
        Paragraph("Customer: Reliance Retail Ltd | Account: XXXXXX4412", styles["Normal"]),
        Table([
            ["Date", "Narration", "Ref No", "Debit", "Credit", "Balance"],
            ["01/04/2025", "OPENING BALANCE", "", "", "1,00,000.00", "1,00,000.00"],
            ["05/04/2025", "NEFT DR-SUPPLIER PAYMENT", "NEFT9921", "25,000.00", "", "75,000.00"],
            ["20/04/2025", "UPI CR-CUSTOMER PAYMENT", "UPI5521", "", "15,000.00", "90,000.00"]
        ])
    ]
    doc.build(story)

    # Encrypt
    f_doc = fitz.open(str(plain_pdf))
    f_doc.save(
        str(enc_pdf),
        encryption=fitz.PDF_ENCRYPT_AES_256,
        owner_pw="Admin123",
        user_pw=secret_pwd
    )
    f_doc.close()
    print("2. Created encrypted PDF statement with password:", secret_pwd)

    # 3. Upload WITHOUT password
    with open(enc_pdf, "rb") as f:
        upload_res = requests.post(
            "http://127.0.0.1:8000/api/v1/documents/upload",
            files={"file": ("test_encrypted_live.pdf", f, "application/pdf")},
            headers=headers
        ).json()
    doc_id = upload_res["document_id"]
    print("3. Uploaded without password. Response:")
    print(f"   • is_encrypted:      {upload_res.get('is_encrypted')}")
    print(f"   • password_required: {upload_res.get('password_required')}")
    print(f"   • status:            {upload_res.get('status')}")
    assert upload_res.get("password_required") is True, "Expected password_required to be True"

    # 4. Test Password Verification API with wrong password
    verify_bad = requests.post(
        f"http://127.0.0.1:8000/api/v1/documents/{doc_id}/verify-password",
        json={"password": "WrongPassword99"},
        headers=headers
    ).json()
    print("4. Tested bad password: valid =", verify_bad.get("valid"))
    assert verify_bad.get("valid") is False, "Expected bad password to fail verification"

    # 5. Test Password Verification API with correct password
    verify_good = requests.post(
        f"http://127.0.0.1:8000/api/v1/documents/{doc_id}/verify-password",
        json={"password": secret_pwd},
        headers=headers
    ).json()
    print("5. Tested good password: valid =", verify_good.get("valid"))
    assert verify_good.get("valid") is True, "Expected correct password to pass verification"

    # 6. Trigger processing with correct password
    proc_res = requests.post(
        f"http://127.0.0.1:8000/api/v1/documents/{doc_id}/process",
        json={"password": secret_pwd},
        headers=headers
    ).json()
    job_id = proc_res["job_id"]
    print("6. Launched extraction job with decryption password. Job ID:", job_id)

    # 7. Poll until complete
    stmt_id = None
    for _ in range(15):
        time.sleep(1)
        j_status = requests.get(f"http://127.0.0.1:8000/api/v1/documents/jobs/{job_id}", headers=headers).json()
        print(f"   Progress: {j_status['progress_percentage']}% | Step: {j_status['current_step']}")
        if j_status["status"] == "COMPLETED":
            stmt_id = j_status["statement_id"]
            break

    assert stmt_id, "Extraction did not complete successfully"
    print("7. Statement successfully decrypted and extracted! Statement ID:", stmt_id)

    # 8. Test 13-Sheet Excel Export
    excel_res = requests.post(
        "http://127.0.0.1:8000/api/v1/exports/excel",
        json={"statement_id": stmt_id},
        headers=headers
    )
    assert excel_res.status_code == 200
    print("8. 13-Sheet Excel Workbook generated and downloaded! Size:", len(excel_res.content), "bytes")

    # Cleanup temp files
    if plain_pdf.exists():
        plain_pdf.unlink()
    if enc_pdf.exists():
        enc_pdf.unlink()
    unlocked_file = Path(f"storage/documents/{doc_id}_unlocked.pdf")
    if unlocked_file.exists():
        unlocked_file.unlink()

    print("=" * 70)
    print("   ALL PASSWORD DETECTION & UNLOCK TESTS PASSED 100%!")
    print("=" * 70)

if __name__ == "__main__":
    test_live_password_flow()
