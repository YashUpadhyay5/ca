import pdfplumber
import re
from decimal import Decimal
from datetime import datetime

pdf_path = r"C:\Users\DELL\Downloads\OpTransactionHistory09-10-2026.pdf"

def parse_statement(pdf_file):
    transactions = []
    
    with pdfplumber.open(pdf_file) as pdf:
        print(f"Opened PDF with {len(pdf.pages)} pages")
        
        for page_idx, page in enumerate(pdf.pages):
            words = page.extract_words()
            if not words:
                continue
                
            # Find the table header on this page
            # Look for words like 'Transaction', 'Withdrawal', 'Deposit', 'Balance'
            header_y = None
            for w in words:
                if w['text'] in ['Withdrawal', 'Deposit', 'Balance', 'Remarks'] and w['top'] < 300:
                    header_y = max(header_y or 0, w['bottom'])
            
            if not header_y:
                header_y = 150 # default fallback
                
            # Filter words below header
            table_words = [w for w in words if w['top'] > header_y]
            
            # Find row anchors: S.No (integer) at x0 < 55, and Date DD.MM.YYYY or DD/MM/YYYY at 50 < x0 < 120
            # Let's find all words that are dates
            date_words = []
            for w in table_words:
                if re.match(r"^\d{2}[./-]\d{2}[./-]\d{4}$", w['text']) and 50 <= w['x0'] <= 120:
                    date_words.append(w)
            
            # Sort date words by top
            date_words.sort(key=lambda x: x['top'])
            
            # Each date word defines a transaction row!
            # The row spans from just above the date (or previous date's bottom) to the next date's top
            for i, d_word in enumerate(date_words):
                curr_y = d_word['top']
                # Determine vertical window for this transaction
                # A row might have payee text starting up to 10 points above the date
                prev_bound = date_words[i-1]['top'] + 15 if i > 0 else header_y
                next_bound = date_words[i+1]['top'] - 6 if i < len(date_words) - 1 else 1000
                
                # Words in this transaction's vertical band
                # Payee line is usually at curr_y - 8 to curr_y
                # Date and amounts are at curr_y - 2 to curr_y + 8
                # Narration lines are at curr_y to next_bound
                row_words = [w for w in table_words if (curr_y - 8 <= w['top'] < next_bound)]
                
                # Columns:
                # S No: x < 55
                # Date: 55 <= x < 120
                # Cheque No: 120 <= x < 188
                # Remarks: 188 <= x < 395
                # Withdrawal (Debit): 395 <= x < 458
                # Deposit (Credit): 458 <= x < 528
                # Balance: 528 <= x < 600
                
                s_no = ""
                txn_date = d_word['text']
                chq_no = ""
                remarks_words = []
                withdrawal_str = ""
                deposit_str = ""
                balance_str = ""
                
                for w in row_words:
                    x_mid = (w['x0'] + w['x1']) / 2
                    if x_mid < 55 and abs(w['top'] - curr_y) < 8:
                        s_no = w['text']
                    elif 120 <= x_mid < 188 and abs(w['top'] - curr_y) < 8:
                        chq_no = w['text']
                    elif 188 <= x_mid < 395:
                        remarks_words.append(w)
                    elif 395 <= x_mid < 458 and abs(w['top'] - curr_y) < 8:
                        withdrawal_str = w['text']
                    elif 458 <= x_mid < 528 and abs(w['top'] - curr_y) < 8:
                        deposit_str = w['text']
                    elif 528 <= x_mid < 600 and abs(w['top'] - curr_y) < 8:
                        balance_str = w['text']
                
                # Sort remarks words by top, then x0
                remarks_words.sort(key=lambda x: (round(x['top'] / 4) * 4, x['x0']))
                # Group into lines
                remarks_lines = []
                curr_line = []
                last_line_y = None
                for rw in remarks_words:
                    if last_line_y is None or abs(rw['top'] - last_line_y) < 5:
                        curr_line.append(rw['text'])
                        last_line_y = rw['top']
                    else:
                        remarks_lines.append(" ".join(curr_line))
                        curr_line = [rw['text']]
                        last_line_y = rw['top']
                if curr_line:
                    remarks_lines.append(" ".join(curr_line))
                
                full_narration = " ".join(remarks_lines).strip()
                
                # Clean amounts
                dr = Decimal(withdrawal_str.replace(",", "")) if withdrawal_str else Decimal("0.00")
                cr = Decimal(deposit_str.replace(",", "")) if deposit_str else Decimal("0.00")
                bal = Decimal(balance_str.replace(",", "")) if balance_str else Decimal("0.00")
                
                transactions.append({
                    "s_no": s_no,
                    "date": txn_date,
                    "chq_no": chq_no,
                    "narration": full_narration,
                    "withdrawal": dr,
                    "deposit": cr,
                    "balance": bal,
                    "page": page_idx + 1
                })

    return transactions

txns = parse_statement(pdf_path)
print(f"\nTotal extracted transactions: {len(txns)}")
print(f"First 5 transactions:")
for t in txns[:5]:
    print(" ", t)
print(f"Last 5 transactions:")
for t in txns[-5:]:
    print(" ", t)

# Validation check: verify continuous balances
tot_dr = sum(t["withdrawal"] for t in txns)
tot_cr = sum(t["deposit"] for t in txns)
print(f"\nTotal Withdrawals: {tot_dr}")
print(f"Total Deposits: {tot_cr}")
print(f"Net Movement: {tot_cr - tot_dr}")
if txns:
    print(f"Opening Balance (deduced): {txns[0]['balance'] - txns[0]['deposit'] + txns[0]['withdrawal']}")
    print(f"Closing Balance (final txn): {txns[-1]['balance']}")
