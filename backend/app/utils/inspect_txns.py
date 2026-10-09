import pdfplumber

pdf_path = r"C:\Users\DELL\Downloads\OpTransactionHistory09-10-2026.pdf"

with pdfplumber.open(pdf_path) as pdf:
    p0 = pdf.pages[0]
    words = p0.extract_words()
    # Between top=350 and top=450 (transactions 4 and 5)
    t_words = [w for w in words if 350 <= w['top'] <= 440]
    for w in sorted(t_words, key=lambda x: (round(x['top'], 1), x['x0'])):
        print(f"top={w['top']:5.1f} bot={w['bottom']:5.1f} x0={w['x0']:5.1f} x1={w['x1']:5.1f} text={w['text']}")
