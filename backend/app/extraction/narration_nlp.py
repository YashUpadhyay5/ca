import re
from typing import Dict, Any, Optional

class NarrationNLP:
    """Intelligent parser for Indian bank narrations, payment modes, VPAs, and tax classifications."""

    UPI_PATTERN = re.compile(r"([a-zA-Z0-9.\-_]{2,50}@[a-zA-Z0-9]{2,30})", re.IGNORECASE)
    CHEQUE_PATTERN = re.compile(r"\b(?:CHQ|CHEQUE|CHQNO)[/:\s.-]*(\d{6})\b", re.IGNORECASE)
    REF_PATTERN = re.compile(r"\b(?:REF|UTR|RRN|TXN|ID)[/:\s.-]*([A-Z0-9]{8,22})\b", re.IGNORECASE)

    # Common Indian Merchants
    MERCHANTS = [
        "AMAZON", "FLIPKART", "SWIGGY", "ZOMATO", "UBER", "OLA", "BLINKIT", "ZEPTO",
        "BIGBASKET", "MYNTRA", "AJIO", "MAKEMYTRIP", "IRCTC", "BOOKMYSHOW", "RELIANCE",
        "DMART", "APOLLO", "PHARMEASY", "TATA", "AIRTEL", "JIO", "VODAFONE", "BESCOM",
        "MAHAVITARAN", "INDIAN OIL", "HPCL", "BPCL", "ZERODHA", "GROWW", "ANGEL ONE",
        "CRED", "PAYTM", "PHONEPE", "GOOGLE PAY", "POLICYBAZAAR", "NYKAA"
    ]

    # Category matching rules
    CATEGORY_RULES = [
        # Tax & Govt Payments
        (r"(?i)\b(?:GST|GSTIN|CBIC|GOODS AND SERVICES TAX)\b", "Tax", "GST"),
        (r"(?i)\b(?:TDS|TAX DEDUCTED AT SOURCE)\b", "Tax", "TDS"),
        (r"(?i)\b(?:INCOME TAX|ITR|CHALLAN 280|CHALLAN 281|ADVANCE TAX|SELF ASSESSMENT)\b", "Tax", "Income Tax"),
        (r"(?i)\b(?:PROFESSIONAL TAX|PTAX|MUNICIPAL TAX|PROPERTY TAX)\b", "Tax", "Local Tax"),
        
        # Payroll & Compensation
        (r"(?i)\b(?:SALARY|PAYROLL|WAGES|STIPEND|BONUS|INCENTIVE)\b", "Salary", "Payroll"),
        
        # Financial / Debt
        (r"(?i)\b(?:EMI|LOAN|HOME LOAN|AUTO LOAN|BAJAJ FIN|HDFC LTD|ICICI HFC)\b", "EMI", "Loan Repayment"),
        (r"(?i)\b(?:INSURANCE|LIC|HDFC LIFE|ICICI PRU|MAX LIFE|STAR HEALTH|MEDICLAIM)\b", "Insurance", "Premium"),
        (r"(?i)\b(?:MUTUAL FUND|SIP|ZERODHA|GROWW|NSE|BSE|KFINTECH|CAMS|SECURITIES)\b", "Investment", "Equities & MF"),
        (r"(?i)\b(?:INTEREST|INT\.PAID|INT\.COLL|INT CREDIT)\b", "Interest", "Bank Interest"),
        (r"(?i)\b(?:CHG|CHARGES|ANNUAL FEE|SMS CHG|DEBIT CARD AMC|MIN BAL|SERVICE CHG)\b", "Bank Charges", "Bank Fees"),
        
        # Operations & Living
        (r"(?i)\b(?:RENT|LEASE|MAINTENANCE|SOCIETY)\b", "Rent", "Property Rent"),
        (r"(?i)\b(?:ELECTRICITY|BESCOM|TNEB|MSEDCL|WATER|GAS|PIPED GAS|BROADBAND|AIRTEL|JIO FIBER)\b", "Utilities", "Utility Bills"),
        (r"(?i)\b(?:PETROL|DIESEL|HPCL|BPCL|IOCL|INDIAN OIL|SHELL|CNG|FUEL)\b", "Fuel", "Transportation Fuel"),
        (r"(?i)\b(?:UBER|OLA|IRCTC|INDIAN RAILWAY|INDIGO|AIR INDIA|VISTARA|MAKEMYTRIP|RED BUS)\b", "Travel", "Commute & Travel"),
        (r"(?i)\b(?:SWIGGY|ZOMATO|RESTAURANT|CAFE|MCDONALDS|DOMINOS|STARBUCKS)\b", "Food", "Dining & Ordering"),
        (r"(?i)\b(?:AMAZON|FLIPKART|MYNTRA|AJIO|BLINKIT|ZEPTO|BIGBASKET|DMART|SHOPPING)\b", "Shopping", "E-Commerce"),
        (r"(?i)\b(?:CASH WDL|ATM WDL|ATM CASH|CASH DEP|SELF CHEQUE|BY CASH)\b", "Cash", "Cash Transaction"),
    ]

    @classmethod
    def parse(cls, narration: str) -> Dict[str, Any]:
        """Deep analysis of narration line into metadata and classification."""
        clean_text = " ".join(narration.replace("\n", " ").split()).strip()
        result = {
            "payment_mode": "TRANSFER",
            "category": "Miscellaneous",
            "subcategory": None,
            "counterparty": None,
            "merchant": None,
            "upi_id": None,
            "cheque_number": None,
            "reference_number": None
        }

        if not clean_text:
            return result

        upper = clean_text.upper()

        # 1. Detect Payment Mode
        if upper.startswith("UPI") or "/UPI/" in upper or " UPI " in upper or "@" in upper:
            result["payment_mode"] = "UPI"
        elif upper.startswith("NEFT") or "/NEFT/" in upper or " NEFT " in upper:
            result["payment_mode"] = "NEFT"
        elif upper.startswith("RTGS") or "/RTGS/" in upper or " RTGS " in upper:
            result["payment_mode"] = "RTGS"
        elif upper.startswith("IMPS") or "/IMPS/" in upper or " IMPS " in upper:
            result["payment_mode"] = "IMPS"
        elif "ATM" in upper or "NWD" in upper or "EAW" in upper:
            result["payment_mode"] = "ATM"
        elif "POS" in upper or "EDC" in upper:
            result["payment_mode"] = "POS"
        elif "CHQ" in upper or "CHEQUE" in upper or "CTS" in upper:
            result["payment_mode"] = "CHEQUE"
        elif "CASH" in upper or "CWDR" in upper or "CDP" in upper:
            result["payment_mode"] = "CASH"
        elif "NACH" in upper or "ACH" in upper:
            result["payment_mode"] = "NACH"
        elif "ECS" in upper:
            result["payment_mode"] = "ECS"
        elif "CARD" in upper or "VISA" in upper or "MASTERCARD" in upper:
            result["payment_mode"] = "CARD"
        elif "INT.PD" in upper or "INTEREST" in upper:
            result["payment_mode"] = "INTEREST"
        elif "CHG" in upper or "FEE" in upper:
            result["payment_mode"] = "BANK_CHARGES"

        # 2. Extract UPI ID
        upi_match = cls.UPI_PATTERN.search(clean_text)
        if upi_match:
            result["upi_id"] = upi_match.group(1).lower()

        # 3. Extract Cheque Number
        chq_match = cls.CHEQUE_PATTERN.search(clean_text)
        if chq_match:
            result["cheque_number"] = chq_match.group(1)

        # 4. Extract Reference Number
        ref_match = cls.REF_PATTERN.search(clean_text)
        if ref_match:
            result["reference_number"] = ref_match.group(1)

        # 5. Extract Merchant
        for m in cls.MERCHANTS:
            if m in upper:
                result["merchant"] = m.title()
                result["counterparty"] = m.title()
                break

        # 6. Extract Counterparty from typical Indian UPI / IMPS strings
        # Example format: UPI/DR/123456/PAYEE_NAME/Bank... or NEFT/AXN1234/PAYEE_NAME
        if not result["counterparty"]:
            tokens = [t.strip() for t in re.split(r"[/:\-_|]", clean_text) if len(t.strip()) > 2]
            for token in tokens:
                token_clean = token.strip()
                # If looks like a name (alphabetic, not a transaction keyword, length > 3)
                if token_clean.isalpha() and len(token_clean) > 3 and token_clean.upper() not in [
                    "UPI", "NEFT", "RTGS", "IMPS", "TRANSFER", "BANK", "PAYMENT", "DR", "CR", "XX", "XXX"
                ]:
                    result["counterparty"] = token_clean.title()
                    break

        # 7. Categorization & Tax Analysis
        for pattern, cat, subcat in cls.CATEGORY_RULES:
            if re.search(pattern, clean_text):
                result["category"] = cat
                result["subcategory"] = subcat
                break

        return result
