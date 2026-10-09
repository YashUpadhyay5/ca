from decimal import Decimal
from typing import List, Dict, Set
from collections import defaultdict

class AnomalyDetector:
    """Detects potential duplicates, round-number anomalies, and unusual spikes."""

    @classmethod
    def flag_anomalies(cls, transactions: List[dict]) -> None:
        """
        Mutates transaction dicts to set `is_potential_duplicate` and `is_anomaly`.
        """
        if not transactions:
            return

        # 1. Duplicate Detection
        seen_signatures: Dict[str, List[int]] = defaultdict(list)
        for idx, t in enumerate(transactions):
            amt = t.get("debit_amount") or t.get("credit_amount") or Decimal("0.00")
            dt = str(t.get("transaction_date"))
            # Signature: Date + Amount + first 15 chars of narration
            narr_snippet = str(t.get("narration", "")).strip().upper()[:15]
            sig = f"{dt}_{amt}_{narr_snippet}"
            seen_signatures[sig].append(idx)

        for sig, indices in seen_signatures.items():
            if len(indices) > 1:
                for idx in indices:
                    transactions[idx]["is_potential_duplicate"] = True

        # 2. Compute Mean & StdDev for Debits
        debits = [Decimal(str(t.get("debit_amount", 0))) for t in transactions if Decimal(str(t.get("debit_amount", 0))) > 0]
        mean_debit = (sum(debits) / len(debits)) if debits else Decimal("0.00")

        # 3. Anomaly Criteria
        for t in transactions:
            debit = Decimal(str(t.get("debit_amount", 0)))
            credit = Decimal(str(t.get("credit_amount", 0)))
            amt = max(debit, credit)
            mode = t.get("payment_mode", "")

            is_anomaly = False

            # Condition A: Large Cash withdrawal or deposit (> ₹50,000)
            if mode == "CASH" and amt >= Decimal("50000.00"):
                is_anomaly = True

            # Condition B: High outlier (> ₹2,00,000 or > 5x average debit)
            if mean_debit > 0 and debit > max(Decimal("200000.00"), mean_debit * 5):
                is_anomaly = True

            # Condition C: Unusually large round number (> ₹1,00,000 ending in 00000)
            if amt >= Decimal("100000.00") and (amt % Decimal("10000.00") == Decimal("0.00")):
                is_anomaly = True

            t["is_anomaly"] = is_anomaly
