from decimal import Decimal
from typing import Optional, List, Dict, Any

class ConfidenceScorer:
    """Calculates multi-dimensional confidence score for extracted bank transactions."""

    @classmethod
    def evaluate(
        cls,
        has_valid_date: bool,
        has_narration: bool,
        has_amount: bool,
        has_balance: bool,
        balance_continuous: bool,
        is_scanned: bool,
        ocr_confidence: float = 1.0,
        unusual_chars: bool = False
    ) -> Decimal:
        """
        Computes composite confidence score from 0.00 to 1.00.
        Weight factors:
        - Date Validity: 20%
        - Narration Clarity: 20%
        - Amount Validity: 25%
        - Running Balance Continuity: 25%
        - Text/OCR Quality: 10%
        """
        score = 0.0

        if has_valid_date:
            score += 0.20
        if has_narration:
            score += 0.20
        if has_amount:
            score += 0.25
        if has_balance:
            score += 0.10
        if balance_continuous:
            score += 0.15
        
        # OCR / Text quality adjustments
        text_quality = ocr_confidence if is_scanned else 1.0
        if unusual_chars:
            text_quality -= 0.2
        score += max(0.0, text_quality) * 0.10

        final_dec = Decimal(str(round(min(1.0, max(0.0, score)), 2)))
        return final_dec

    @classmethod
    def determine_validation_status(cls, confidence: Decimal, balance_discrepancy: bool) -> str:
        """Categorizes transaction into VALIDATED or REVIEW_REQUIRED."""
        if balance_discrepancy or confidence < Decimal("0.90"):
            return "REVIEW_REQUIRED"
        return "VALIDATED"
