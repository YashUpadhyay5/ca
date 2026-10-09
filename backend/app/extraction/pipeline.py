import fitz  # PyMuPDF
from decimal import Decimal
from typing import Dict, Any, List, Optional
from datetime import date
import re

from app.extraction.parsers.base import BaseBankParser, RawTransaction
from app.extraction.parsers.sbi import SBIBankParser
from app.extraction.parsers.hdfc import HDFCBankParser
from app.extraction.parsers.icici import ICICIBankParser
from app.extraction.parsers.axis import AxisBankParser, KotakBankParser
from app.extraction.parsers.generic import GenericBankParser
from app.extraction.table_detector import TableDetector
from app.extraction.ocr_engine import OCREngine
from app.extraction.narration_nlp import NarrationNLP
from app.extraction.confidence import ConfidenceScorer
from app.validation.balance_validator import BalanceValidator
from app.validation.anomaly_detector import AnomalyDetector

class ExtractionPipeline:
    """Orchestrates end-to-end PDF processing, Bank detection, Extraction, Validation, and Lineage."""

    PARSER_REGISTRY: List[BaseBankParser] = [
        SBIBankParser(),
        HDFCBankParser(),
        ICICIBankParser(),
        AxisBankParser(),
        KotakBankParser(),
        GenericBankParser()  # Fallback
    ]

    @classmethod
    def detect_bank_parser(cls, sample_text: str) -> BaseBankParser:
        """Selects parser adapter based on header/footer bank signatures."""
        for parser in cls.PARSER_REGISTRY:
            if parser.detect(sample_text):
                return parser
        return GenericBankParser()

    @classmethod
    def extract_account_number(cls, header_text: str) -> Optional[str]:
        """Heuristically extracts bank account number from statement header."""
        match = re.search(r"(?i)(?:a/c|acct|account)[\s\w.:-]*?([0-9Xx*]{9,18})", header_text)
        if match:
            raw = match.group(1).replace(" ", "")
            # Mask to show only last 4 digits
            if len(raw) >= 4:
                return f"XXXXXX{raw[-4:]}"
        return None

    @classmethod
    def extract_customer_name(cls, header_text: str) -> Optional[str]:
        """Heuristically extracts account holder or customer name from header."""
        for pattern in [
            r"(?i)(?:customer name|account name|name of account holder|client name|account holder)\s*[:\-]\s*([^\n\r]+)",
            r"(?i)(?:m/s\.?|shri|smt\.?|mr\.?|ms\.?)\s+([A-Za-z0-9 .,&'/\-]+)",
            r"(?i)(?:Statement of Transactions in [^\n]+\n\s*)([A-Z\s]{3,40})(?:\s+Your Base Branch|Branch|Address|\n)",
        ]:
            match = re.search(pattern, header_text)
            if match:
                name = match.group(1).strip()
                name = re.sub(r"(?i)\s+(?:period|account|branch|date|statement|ifsc|cif|address|your base).*", "", name).strip()
                if len(name) > 3 and not any(k in name.upper() for k in ["STATEMENT", "ACCOUNT NO", "BRANCH", "NUMBER"]):
                    return name[:80]
        return None

    @classmethod
    def check_pdf_encryption(cls, file_path: str) -> bool:
        """Checks if target PDF requires password decryption."""
        try:
            doc = fitz.open(file_path)
            is_enc = doc.is_encrypted
            doc.close()
            return is_enc
        except Exception:
            return False

    @classmethod
    def process_pdf(cls, file_path: str, password: Optional[str] = None, progress_callback=None) -> Dict[str, Any]:
        """
        Executes complete extraction pipeline on target PDF file.
        Handles password-protected PDFs by authenticating and saving an unlocked working copy.
        Returns full structured statement dataset with audit lineage and validation.
        """
        doc = fitz.open(file_path)
        if doc.is_encrypted:
            if not password:
                doc.close()
                raise ValueError("PASSWORD_REQUIRED: Statement PDF is password protected.")
            auth_ok = doc.authenticate(password)
            if not auth_ok:
                doc.close()
                raise ValueError("INVALID_PASSWORD: Incorrect statement password.")
            
            # Save unencrypted working copy so downstream pdfplumber & OCR run smoothly
            unlocked_file_path = file_path.replace(".pdf", "_unlocked.pdf")
            doc.save(unlocked_file_path)
            doc.close()
            file_path = unlocked_file_path
            doc = fitz.open(file_path)

        total_pages = len(doc)
        
        # 1. Inspect first page for bank detection and metadata
        first_page_text = doc[0].get_text() if total_pages > 0 else ""
        selected_parser = cls.detect_bank_parser(first_page_text)
        detected_acc_no = cls.extract_account_number(first_page_text)
        detected_customer_name = cls.extract_customer_name(first_page_text)

        raw_txns: List[RawTransaction] = []
        is_any_page_scanned = False

        # 2. Iterate through pages
        for page_num in range(1, total_pages + 1):
            if progress_callback:
                progress_callback(
                    step=f"Extracting transactions from page {page_num}/{total_pages}",
                    pct=int(10 + (page_num / total_pages) * 60)
                )

            fitz_page = doc[page_num - 1]
            page_is_scanned = OCREngine.is_page_scanned(fitz_page)
            if page_is_scanned:
                is_any_page_scanned = True

            tables = []
            ocr_conf = 1.0

            if not page_is_scanned:
                # Digital extraction
                tables = TableDetector.extract_tables_pdfplumber(file_path, page_num)
                if not tables:
                    tables = [TableDetector.extract_text_pymupdf_fallback(file_path, page_num)]
            else:
                # OCR extraction
                table_ocr, ocr_conf = OCREngine.ocr_page(doc, page_num)
                if table_ocr:
                    tables = [table_ocr]

            # Parse each extracted table using the selected parser adapter
            for tbl in tables:
                if tbl and len(tbl) > 1:
                    page_txns = selected_parser.parse_page_table(tbl, page_num)
                    for pt in page_txns:
                        # Adjust confidence for scanned pages
                        if page_is_scanned:
                            pt.confidence_score = Decimal(str(round(float(pt.confidence_score) * ocr_conf, 2)))
                    raw_txns.extend(page_txns)

        doc.close()

        if progress_callback:
            progress_callback(step="Normalizing transactions & analyzing narrations", pct=75)

        # 3. Normalize and enrich transactions
        normalized_txns = []
        for raw in raw_txns:
            # NLP on narration
            nlp_meta = NarrationNLP.parse(raw.narration)
            
            # Use raw reference/cheque if NLP didn't find one
            final_ref = nlp_meta.get("reference_number") or raw.reference_number
            final_chq = nlp_meta.get("cheque_number") or raw.cheque_number

            # Determine confidence
            has_valid_date = raw.transaction_date is not None
            has_narration = len(raw.narration.strip()) > 3
            has_amount = (raw.debit_amount > 0 or raw.credit_amount > 0)
            has_balance = raw.balance > 0

            conf = ConfidenceScorer.evaluate(
                has_valid_date=has_valid_date,
                has_narration=has_narration,
                has_amount=has_amount,
                has_balance=has_balance,
                balance_continuous=True,
                is_scanned=is_any_page_scanned,
                ocr_confidence=float(raw.confidence_score)
            )

            txn_dict = {
                "transaction_date": raw.transaction_date or date.today(),
                "value_date": raw.value_date or raw.transaction_date or date.today(),
                "narration": raw.narration,
                "raw_text": raw.raw_text,
                "reference_number": final_ref,
                "cheque_number": final_chq,
                "debit_amount": raw.debit_amount,
                "credit_amount": raw.credit_amount,
                "balance": raw.balance,
                "payment_mode": nlp_meta.get("payment_mode", "TRANSFER"),
                "category": nlp_meta.get("category", "Miscellaneous"),
                "subcategory": nlp_meta.get("subcategory"),
                "counterparty": nlp_meta.get("counterparty"),
                "upi_id": nlp_meta.get("upi_id"),
                "source_page": raw.source_page,
                "source_row": raw.source_row,
                "confidence_score": conf,
                "validation_status": "VALIDATED" if conf >= Decimal("0.90") else "REVIEW_REQUIRED",
                "is_internal_transfer": False,
                "is_potential_duplicate": False,
                "is_anomaly": False,
                "notes": None
            }
            normalized_txns.append(txn_dict)

        # Sort chronologically
        normalized_txns.sort(key=lambda x: x["transaction_date"])

        if progress_callback:
            progress_callback(step="Validating financial balances and continuity", pct=85)

        # 4. Opening and Closing Balances
        opening_bal = Decimal("0.00")
        closing_bal = Decimal("0.00")
        if normalized_txns:
            first_txn = normalized_txns[0]
            # Deduced Opening Balance = First Balance - First Credit + First Debit
            if first_txn["balance"] > 0:
                opening_bal = (first_txn["balance"] - first_txn["credit_amount"] + first_txn["debit_amount"]).quantize(Decimal("0.01"))
            closing_bal = normalized_txns[-1]["balance"]

        # 5. Financial Validation
        tot_credits = sum([t["credit_amount"] for t in normalized_txns], Decimal("0.00"))
        tot_debits = sum([t["debit_amount"] for t in normalized_txns], Decimal("0.00"))
        net_movement = tot_credits - tot_debits

        is_reconciled, expected_closing, discrepancy = BalanceValidator.reconcile_statement(
            opening_balance=opening_bal,
            closing_balance=closing_bal,
            total_credits=tot_credits,
            total_debits=tot_debits
        )

        # Continuity check
        # Convert dicts into dummy object for validator
        class DummyTxn:
            def __init__(self, d):
                self.debit_amount = d["debit_amount"]
                self.credit_amount = d["credit_amount"]
                self.balance = d["balance"]
                self.transaction_date = d["transaction_date"]
                self.narration = d["narration"]

        dummy_list = [DummyTxn(d) for d in normalized_txns]
        continuity_ok, cum_diff, broken_steps = BalanceValidator.validate_continuity(dummy_list, opening_bal)

        # 6. Flag Anomalies and Duplicates
        AnomalyDetector.flag_anomalies(normalized_txns)

        # 7. Generate Review Items for discrepancies or low confidence
        review_items = []
        for idx, t in enumerate(normalized_txns):
            issues = []
            if t["confidence_score"] < Decimal("0.90"):
                issues.append(("LOW_CONFIDENCE", f"Extraction confidence ({t['confidence_score'] * 100}%) is below 90% threshold."))
            if t["is_potential_duplicate"]:
                issues.append(("DUPLICATE_SUSPICION", "Potential duplicate transaction found with identical date, amount, and narration."))
            if t["is_anomaly"]:
                issues.append(("ANOMALY_FLAG", "Large round number or unusually high cash movement detected."))

            for code, desc in issues:
                review_items.append({
                    "transaction_index": idx,
                    "issue_code": code,
                    "issue_description": desc,
                    "status": "PENDING"
                })

        # Add balance continuity broken steps to review
        for step in broken_steps:
            row_idx = step["row_index"] - 1
            if 0 <= row_idx < len(normalized_txns):
                normalized_txns[row_idx]["validation_status"] = "REVIEW_REQUIRED"
                review_items.append({
                    "transaction_index": row_idx,
                    "issue_code": "BALANCE_CONTINUITY_BREAK",
                    "issue_description": f"Balance mismatch of ₹{step['difference']}. Expected ₹{step['expected_balance']}, reported ₹{step['reported_balance']}.",
                    "status": "PENDING"
                })

        period_start = normalized_txns[0]["transaction_date"] if normalized_txns else None
        period_end = normalized_txns[-1]["transaction_date"] if normalized_txns else None

        avg_conf = (sum([t["confidence_score"] for t in normalized_txns]) / len(normalized_txns)) if normalized_txns else Decimal("1.00")

        return {
            "bank_name": selected_parser.bank_name,
            "account_number": detected_acc_no,
            "customer_name": detected_customer_name,
            "parser_used": selected_parser.bank_name,
            "total_pages": total_pages,
            "is_scanned": is_any_page_scanned,
            "period_start": period_start,
            "period_end": period_end,
            "opening_balance": opening_bal,
            "closing_balance": closing_bal,
            "calculated_closing_balance": expected_closing,
            "balance_discrepancy": discrepancy,
            "reconciliation_status": "RECONCILED" if (is_reconciled and continuity_ok) else "DISCREPANCY_DETECTED",
            "total_transactions": len(normalized_txns),
            "total_credits": tot_credits,
            "total_debits": tot_debits,
            "net_movement": net_movement,
            "confidence_avg": avg_conf.quantize(Decimal("0.01")),
            "transactions": normalized_txns,
            "review_items": review_items,
            "broken_steps": broken_steps
        }
