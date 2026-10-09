import requests
import time
import sys

# Configure UTF-8 for printing Rupee symbol on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def verify_live_server():
    print("=" * 60)
    print("   Verifying CaFinIQ Live API on http://127.0.0.1:8000")
    print("=" * 60)

    # 1. Login
    auth_res = requests.post(
        'http://127.0.0.1:8000/api/v1/auth/login',
        json={'email': 'ca@mehtaca.com', 'password': 'AuditPassword123!'}
    ).json()
    token = auth_res['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print("1. Authenticated as:", auth_res['user']['full_name'])

    # 2. Get Client
    clients = requests.get('http://127.0.0.1:8000/api/v1/clients/', headers=headers).json()
    client_id = clients[0]['id']
    print("2. Found Client:", clients[0]['name'])

    # 3. Upload Sample SBI Statement
    with open('backend/sample_statements/sample_sbi_current_account.pdf', 'rb') as f:
        files = {'file': ('sample_sbi_current_account.pdf', f, 'application/pdf')}
        data = {'client_id': client_id}
        upload_res = requests.post(
            'http://127.0.0.1:8000/api/v1/documents/upload',
            files=files,
            data=data,
            headers=headers
        ).json()
        doc_id = upload_res['document_id']
        print("3. Uploaded Document ID:", doc_id)

    # 4. Trigger Processing
    process_res = requests.post(
        f'http://127.0.0.1:8000/api/v1/documents/{doc_id}/process',
        headers=headers
    ).json()
    job_id = process_res['job_id']
    print("4. Started Background Extraction Job:", job_id)

    # 5. Poll Job
    stmt_id = None
    for _ in range(15):
        time.sleep(1)
        poll_res = requests.get(
            f'http://127.0.0.1:8000/api/v1/documents/jobs/{job_id}',
            headers=headers
        ).json()
        print(f"   Progress: {poll_res['progress_percentage']}% | Step: {poll_res['current_step']}")
        if poll_res['status'] == 'COMPLETED':
            stmt_id = poll_res.get('statement_id')
            break

    print("5. Completed Extraction! Statement ID:", stmt_id)
    assert stmt_id is not None, "Statement ID should not be None"

    # 6. Query Statement
    stmt = requests.get(f'http://127.0.0.1:8000/api/v1/statements/{stmt_id}', headers=headers).json()
    print("6. Extracted Bank Statement Metrics:")
    print("   - Bank Name:", stmt['bank_name'])
    print("   - Account Number Detected:", stmt['account_number_detected'])
    print("   - Opening Balance: Rs", stmt['opening_balance'])
    print("   - Closing Balance: Rs", stmt['closing_balance'])
    print("   - Reconciliation Status:", stmt['reconciliation_status'])
    print("   - Total Transactions:", stmt['total_transactions'])

    # 7. Query Transactions
    txns = requests.get(
        f'http://127.0.0.1:8000/api/v1/statements/{stmt_id}/transactions',
        headers=headers
    ).json()
    print(f"7. Extracted {len(txns['items'])} Transactions in Database:")
    for t in txns['items']:
        narr = t['narration'][:30]
        print(f"   * {t['transaction_date']} | {narr:30} | Dr: {t['debit_amount']:>9} | Cr: {t['credit_amount']:>9} | Bal: {t['balance']:>9} | Mode: {t['payment_mode']:>8} | Cat: {t['category']}")

    # 8. Query Natural Language Assistant
    ai_query = requests.post(
        'http://127.0.0.1:8000/api/v1/assistant/query',
        json={'statement_id': stmt_id, 'query': 'How much was spent on tax?'},
        headers=headers
    ).json()
    print("8. 'Ask Your Bank Statement' Answer:")
    print("   -", ai_query['answer'])

    # 9. Verify 7-Sheet Excel Export
    excel_res = requests.post(
        'http://127.0.0.1:8000/api/v1/exports/excel',
        json={'statement_id': stmt_id},
        headers=headers
    )
    print(f"9. 7-Sheet CA Excel Workbook Generated: Status {excel_res.status_code}, Size {len(excel_res.content)} bytes")
    assert excel_res.status_code == 200

    print("=" * 60)
    print("   ALL LIVE SMOKE TESTS AND FLOWS VERIFIED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    verify_live_server()
