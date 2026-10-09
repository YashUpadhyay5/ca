import re
from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.transaction import Transaction

class SafeQueryAssistant:
    """Natural Language CA Assistant that safely translates user queries into structured filters."""

    @classmethod
    def answer_query(cls, db: Session, statement_id: str, prompt: str) -> Dict[str, Any]:
        """Parses natural text question and executes mathematically validated query."""
        p_lower = prompt.lower().strip()
        query = db.query(Transaction).filter(Transaction.statement_id == statement_id)

        intent = "LIST"
        applied_filters = []
        explanation = ""

        # 1. Filter: Amount threshold e.g. "above 1 lakh", "above 50,000", "over 100000"
        lakh_match = re.search(r"(?:above|greater than|over|more than|>)\s*(?:₹|rs\.?)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|lacs|lakhs)", p_lower)
        if lakh_match:
            amt = Decimal(lakh_match.group(1)) * Decimal("100000")
            query = query.filter((Transaction.debit_amount >= amt) | (Transaction.credit_amount >= amt))
            applied_filters.append(f"Amount >= ₹{amt:,.2f}")

        num_match = re.search(r"(?:above|greater than|over|more than|>)\s*(?:₹|rs\.?)?\s*(\d[\d,]+)", p_lower)
        if num_match and not lakh_match:
            raw_n = num_match.group(1).replace(",", "")
            amt = Decimal(raw_n)
            query = query.filter((Transaction.debit_amount >= amt) | (Transaction.credit_amount >= amt))
            applied_filters.append(f"Amount >= ₹{amt:,.2f}")

        # 2. Filter: Payment mode
        if "upi" in p_lower:
            query = query.filter(Transaction.payment_mode == "UPI")
            applied_filters.append("Payment Mode = UPI")
        elif "neft" in p_lower:
            query = query.filter(Transaction.payment_mode == "NEFT")
            applied_filters.append("Payment Mode = NEFT")
        elif "rtgs" in p_lower:
            query = query.filter(Transaction.payment_mode == "RTGS")
            applied_filters.append("Payment Mode = RTGS")
        elif "imps" in p_lower:
            query = query.filter(Transaction.payment_mode == "IMPS")
            applied_filters.append("Payment Mode = IMPS")
        elif "cash" in p_lower:
            query = query.filter(Transaction.payment_mode == "CASH")
            applied_filters.append("Payment Mode = CASH")
        elif "cheque" in p_lower or "chq" in p_lower:
            query = query.filter(Transaction.payment_mode == "CHEQUE")
            applied_filters.append("Payment Mode = CHEQUE")

        # 3. Filter: Debit / Credit
        if "debit" in p_lower or "spent" in p_lower or "expense" in p_lower or "withdrawal" in p_lower:
            query = query.filter(Transaction.debit_amount > 0)
            applied_filters.append("Direction = DEBIT")
        elif "credit" in p_lower or "deposit" in p_lower or "income" in p_lower or "inflow" in p_lower:
            query = query.filter(Transaction.credit_amount > 0)
            applied_filters.append("Direction = CREDIT")

        # 4. Search keyword / merchant
        merchant_search = re.search(r"(?:containing|for|merchant|at)\s+([a-zA-Z0-9]+)", p_lower)
        if merchant_search:
            kw = merchant_search.group(1).strip()
            if kw not in ["all", "any", "the", "march", "april", "debit", "credit", "upi"]:
                query = query.filter(Transaction.narration.ilike(f"%{kw}%"))
                applied_filters.append(f"Narration contains '{kw}'")

        # 5. Question Intent Analysis
        txns = query.all()
        total_count = len(txns)
        total_dr = sum([t.debit_amount for t in txns], Decimal("0.00"))
        total_cr = sum([t.credit_amount for t in txns], Decimal("0.00"))

        if "largest" in p_lower or "maximum" in p_lower or "highest" in p_lower:
            if "debit" in p_lower or "expense" in p_lower:
                top_item = max(txns, key=lambda x: x.debit_amount, default=None)
                if top_item:
                    explanation = f"The largest debit is ₹{top_item.debit_amount:,.2f} on {top_item.transaction_date} ({top_item.narration})."
                else:
                    explanation = "No matching debit transactions found."
            else:
                top_item = max(txns, key=lambda x: max(x.debit_amount, x.credit_amount), default=None)
                if top_item:
                    amt = max(top_item.debit_amount, top_item.credit_amount)
                    explanation = f"The largest transaction is ₹{amt:,.2f} on {top_item.transaction_date} ({top_item.narration})."
                else:
                    explanation = "No transactions found."
        elif "how much" in p_lower or "total" in p_lower or "sum" in p_lower:
            if "debit" in p_lower or "spent" in p_lower or "expense" in p_lower:
                explanation = f"Total debit outflow for this filter is ₹{total_dr:,.2f} across {total_count} transactions."
            elif "credit" in p_lower or "deposit" in p_lower:
                explanation = f"Total credit inflow for this filter is ₹{total_cr:,.2f} across {total_count} transactions."
            else:
                explanation = f"Total volume is ₹{(total_dr + total_cr):,.2f} (Debits: ₹{total_dr:,.2f}, Credits: ₹{total_cr:,.2f}) across {total_count} transactions."
        else:
            explanation = f"Found {total_count} transactions matching your query (Debits: ₹{total_dr:,.2f}, Credits: ₹{total_cr:,.2f})."

        # Return sample items
        sample_items = [
            {
                "id": t.id,
                "date": str(t.transaction_date),
                "narration": t.narration,
                "debit": float(t.debit_amount),
                "credit": float(t.credit_amount),
                "balance": float(t.balance),
                "payment_mode": t.payment_mode,
                "category": t.category
            } for t in txns[:20]
        ]

        return {
            "query": prompt,
            "answer": explanation,
            "applied_filters": applied_filters,
            "matched_count": total_count,
            "total_debit": float(total_dr),
            "total_credit": float(total_cr),
            "transactions": sample_items
        }
