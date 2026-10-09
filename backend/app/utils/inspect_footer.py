import pdfplumber

pdf_path = r"C:\Users\DELL\Downloads\OpTransactionHistory09-10-2026.pdf"

with pdfplumber.open(pdf_path) as pdf:
    p13 = pdf.pages[13]
    words = p13.extract_words()
    for w in sorted(words, key=lambda x: (x['top'], x['x0'])):
        if 200 <= w['top'] <= 500:
            print(f"top={w['top']:.1f} x0={w['x0']:.1f} text={w['text']}")
