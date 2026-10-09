import pdfplumber
import re
from datetime import datetime

pdf_path = r"C:\Users\DELL\Downloads\OpTransactionHistory09-10-2026.pdf"

with pdfplumber.open(pdf_path) as pdf:
    print(f"Total Pages: {len(pdf.pages)}")
    all_lines = []
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        lines = text.split("\n") if text else []
        # Find lines starting with a number followed by a date DD.MM.YYYY
        txn_starts = []
        for l_idx, line in enumerate(lines):
            # Check pattern: starts with integer, then date DD.MM.YYYY
            # E.g. "1 13.07.2026" or "12 29.07.2026"
            m = re.match(r"^\s*(\d+)\s+(\d{2}\.\d{2}\.\d{4})\s+", line)
            if m:
                txn_starts.append((m.group(1), m.group(2), line))
        print(f"Page {i+1}: found {len(txn_starts)} transaction anchor lines. Lines range: {[t[0] for t in txn_starts[:3]]} ... {[t[0] for t in txn_starts[-1:]] if txn_starts else ''}")
