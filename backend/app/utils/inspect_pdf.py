import pdfplumber
import json

pdf_path = r"C:\Users\DELL\Downloads\OpTransactionHistory09-10-2026.pdf"

with pdfplumber.open(pdf_path) as pdf:
    p0 = pdf.pages[0]
    words = p0.extract_words()
    
    # Print words sorted by vertical position (top) then horizontal (x0)
    print(f"Total words on page 1: {len(words)}")
    for w in sorted(words, key=lambda x: (x['top'], x['x0'])):
        if 80 <= w['top'] <= 280:
            print(f"{w['text']:<25} top={w['top']:6.1f} x0={w['x0']:6.1f} x1={w['x1']:6.1f}")
