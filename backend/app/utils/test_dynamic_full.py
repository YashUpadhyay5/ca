import pdfplumber
import re
from decimal import Decimal
from datetime import datetime, date
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

pdf_path = r"C:\Users\DELL\Downloads\OpTransactionHistory09-10-2026.pdf"

def dynamic_extract_statement(pdf_file_path):
    all_txns = []
    metadata = {
        "bank_name": "ICICI Bank",
        "account_number": "",
        "customer_name": "",
        "period": ""
    }

    with pdfplumber.open(pdf_file_path) as pdf:
        # Extract metadata from page 1
        p0_text = pdf.pages[0].extract_text() or ""
        
        # Bank detection
        if "ICICI" in p0_text.upper():
            metadata["bank_name"] = "ICICI Bank"
        elif "STATE BANK OF INDIA" in p0_text.upper() or "SBI" in p0_text.upper():
            metadata["bank_name"] = "State Bank of India"
        elif "HDFC" in p0_text.upper():
            metadata["bank_name"] = "HDFC Bank"
            
        # Account number
        acc_m = re.search(r"(?i)(?:account\s*no\.?|a/c\s*no\.?|account\s*number)\s*[:\-]?\s*([0-9Xx*]{9,18})", p0_text)
        if acc_m:
            metadata["account_number"] = acc_m.group(1)
            
        # Customer name
        name_m = re.search(r"(?i)(?:Statement of Transactions in [^\n]+\n)([A-Z\s]{3,35})(?:Your Base Branch|Branch|Address|\n)", p0_text)
        if name_m:
            metadata["customer_name"] = name_m.group(1).strip()
        else:
            # Fallback
            for line in p0_text.split("\n")[:6]:
                if any(w in line for w in ["LAXMAN", "PRASAD", "Mr.", "M/s", "Shri"]):
                    metadata["customer_name"] = line.split("Your Base")[0].strip()
                    break

        # Period
        period_m = re.search(r"(?i)(?:period\s*[:\-]?\s*)([A-Za-z0-9,\s\-]+)(?:\n|$)", p0_text)
        if period_m:
            metadata["period"] = period_m.group(1).strip()

        print(f"Extracted Metadata: Bank={metadata['bank_name']}, Acc={metadata['account_number']}, Client={metadata['customer_name']}, Period={metadata['period']}")

        # Extract transactions across all pages
        for page_idx, page in enumerate(pdf.pages):
            words = page.extract_words()
            if not words:
                continue

            # Identify header top & bottom
            # Headers keywords: S No, Date, Transaction, Remarks, Withdrawal, Deposit, Balance
            header_words = [w for w in words if w['top'] < 300 and any(k in w['text'].upper() for k in [
                'DATE', 'WITHDRAWAL', 'DEPOSIT', 'BALANCE', 'REMARKS', 'PARTICULARS', 'CHEQUE'
            ])]
            
            if header_words:
                header_bottom = max(w['bottom'] for w in header_words)
            else:
                header_bottom = 230

            # Identify footer boundary (e.g. www.icici.bank.in, Legends, Sincerely)
            footer_top = 1000
            for w in words:
                if w['top'] > 300 and any(k in w['text'].lower() for k in [
                    'sincerly', 'legends', 'system generated', 'www.icici', 'dial your bank'
                ]):
                    footer_top = min(footer_top, w['top'])

            # Filter table words
            table_words = [w for w in words if header_bottom <= w['top'] < footer_top]

            # Find row anchors: Date pattern DD.MM.YYYY or DD/MM/YYYY or DD-MM-YYYY
            date_words = [w for w in table_words if re.match(r"^\d{1,2}[./-]\d{1,2}[./-]\d{2,4}$", w['text']) and 45 <= w['x0'] <= 130]
            date_words.sort(key=lambda x: x['top'])

            for i, dw in enumerate(date_words):
                curr_y = dw['top']
                next_y = date_words[i+1]['top'] - 4 if i < len(date_words) - 1 else footer_top
                # Payee line can be slightly above (up to 8 pt)
                prev_bound = curr_y - 8

                row_words = [w for w in table_words if prev_bound <= w['top'] < next_y]

                s_no = ""
                txn_date_str = dw['text']
                chq_no = ""
                remarks_list = []
                dr_str = ""
                cr_str = ""
                bal_str = ""

                for w in row_words:
                    x_mid = (w['x0'] + w['x1']) / 2
                    is_main_line = abs(w['top'] - curr_y) < 8

                    if x_mid < 55 and is_main_line:
                        s_no = w['text']
                    elif 120 <= x_mid < 188 and is_main_line:
                        chq_no = w['text']
                    elif 188 <= x_mid < 395:
                        remarks_list.append(w)
                    elif 395 <= x_mid < 458 and is_main_line:
                        dr_str = w['text']
                    elif 458 <= x_mid < 528 and is_main_line:
                        cr_str = w['text']
                    elif 528 <= x_mid < 600 and is_main_line:
                        bal_str = w['text']

                # Format remarks
                remarks_list.sort(key=lambda x: (round(x['top'] / 4) * 4, x['x0']))
                narration = " ".join([w['text'] for w in remarks_list]).strip()

                # Clean amounts
                dr_val = Decimal(dr_str.replace(",", "")) if dr_str else Decimal("0.00")
                cr_val = Decimal(cr_str.replace(",", "")) if cr_str else Decimal("0.00")
                bal_val = Decimal(bal_str.replace(",", "")) if bal_str else Decimal("0.00")

                # Parse date
                d_obj = None
                for fmt in ["%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y"]:
                    try:
                        d_obj = datetime.strptime(txn_date_str, fmt).date()
                        break
                    except ValueError:
                        pass
                if not d_obj:
                    d_obj = date.today()

                all_txns.append({
                    "s_no": s_no or str(len(all_txns) + 1),
                    "date": d_obj,
                    "narration": narration,
                    "chq_no": chq_no,
                    "debit": dr_val,
                    "credit": cr_val,
                    "balance": bal_val,
                    "page": page_idx + 1
                })

    return metadata, all_txns

metadata, txns = dynamic_extract_statement(pdf_path)
print(f"Total transactions extracted: {len(txns)}")

# Verify Continuity
tot_dr = sum(t["debit"] for t in txns)
tot_cr = sum(t["credit"] for t in txns)
opening = txns[0]["balance"] - txns[0]["credit"] + txns[0]["debit"] if txns else Decimal("0.00")
closing = txns[-1]["balance"] if txns else Decimal("0.00")
expected_closing = opening + tot_cr - tot_dr

print(f"Opening: Rs. {opening}")
print(f"Total In (Credit): Rs. {tot_cr}")
print(f"Total Out (Debit): Rs. {tot_dr}")
print(f"Closing: Rs. {closing}")
print(f"Expected Closing: Rs. {expected_closing}")
print(f"Diff: Rs. {closing - expected_closing} (Reconciled: {closing == expected_closing})")

