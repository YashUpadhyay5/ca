from decimal import Decimal
import math
from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import date

class CalculationEngine:
    """Centralized high-precision Decimal financial analysis and mathematical computation engine."""

    INDIAN_FISCAL_MONTHS = [
        ("Apr", 4), ("May", 5), ("Jun", 6), ("Jul", 7), ("Aug", 8), ("Sep", 9),
        ("Oct", 10), ("Nov", 11), ("Dec", 12), ("Jan", 1), ("Feb", 2), ("Mar", 3)
    ]

    @classmethod
    def compute_summary_metrics(cls, transactions: List[Any]) -> Dict[str, Any]:
        """Calculates basic and financial summary indicators."""
        if not transactions:
            return {
                "total_credits": Decimal("0.00"),
                "total_debits": Decimal("0.00"),
                "net_movement": Decimal("0.00"),
                "total_transactions": 0,
                "debit_count": 0,
                "credit_count": 0,
                "largest_credit": Decimal("0.00"),
                "largest_debit": Decimal("0.00"),
                "average_transaction": Decimal("0.00"),
                "median_transaction": Decimal("0.00"),
                "std_dev_transaction": Decimal("0.00")
            }

        debits = [Decimal(str(t.debit_amount)) for t in transactions if Decimal(str(t.debit_amount)) > 0]
        credits = [Decimal(str(t.credit_amount)) for t in transactions if Decimal(str(t.credit_amount)) > 0]
        all_amounts = debits + credits

        tot_credits = sum(credits, Decimal("0.00"))
        tot_debits = sum(debits, Decimal("0.00"))
        net = tot_credits - tot_debits

        largest_cr = max(credits) if credits else Decimal("0.00")
        largest_dr = max(debits) if debits else Decimal("0.00")

        # Average
        avg_amt = (sum(all_amounts) / len(all_amounts)).quantize(Decimal("0.01")) if all_amounts else Decimal("0.00")

        # Median
        sorted_amts = sorted(all_amounts)
        n = len(sorted_amts)
        if n == 0:
            median_amt = Decimal("0.00")
        elif n % 2 == 1:
            median_amt = sorted_amts[n // 2]
        else:
            median_amt = ((sorted_amts[n // 2 - 1] + sorted_amts[n // 2]) / 2).quantize(Decimal("0.01"))

        # Standard Deviation
        if n > 1:
            variance = sum([(x - avg_amt) ** 2 for x in sorted_amts]) / (n - 1)
            std_dev = Decimal(str(round(math.sqrt(float(variance)), 2)))
        else:
            std_dev = Decimal("0.00")

        return {
            "total_credits": tot_credits,
            "total_debits": tot_debits,
            "net_movement": net,
            "total_transactions": len(transactions),
            "debit_count": len(debits),
            "credit_count": len(credits),
            "largest_credit": largest_cr,
            "largest_debit": largest_dr,
            "average_transaction": avg_amt,
            "median_transaction": median_amt,
            "std_dev_transaction": std_dev
        }

    @classmethod
    def compute_monthly_analysis(cls, transactions: List[Any]) -> List[Dict[str, Any]]:
        """Groups transactions by month in chronological and Indian FY sequence."""
        # Key: (year, month)
        grouped = defaultdict(lambda: {"credits": Decimal("0.00"), "debits": Decimal("0.00"), "count": 0})

        for t in transactions:
            dt = t.transaction_date
            if dt:
                key = (dt.year, dt.month)
                grouped[key]["credits"] += Decimal(str(t.credit_amount))
                grouped[key]["debits"] += Decimal(str(t.debit_amount))
                grouped[key]["count"] += 1

        results = []
        month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        sorted_keys = sorted(grouped.keys())
        for idx, (yr, mo) in enumerate(sorted_keys):
            d = grouped[(yr, mo)]
            tot_flow = d["credits"] + d["debits"]
            avg = (tot_flow / d["count"]).quantize(Decimal("0.01")) if d["count"] > 0 else Decimal("0.00")
            
            # Fiscal month index (Apr = 1, Mar = 12)
            fiscal_idx = (mo - 3) if mo >= 4 else (mo + 9)

            results.append({
                "month_name": f"{month_names[mo]} {yr}",
                "year": yr,
                "fiscal_month_index": fiscal_idx,
                "credits": d["credits"],
                "debits": d["debits"],
                "net_movement": d["credits"] - d["debits"],
                "transaction_count": d["count"],
                "average_transaction": avg
            })

        return results

    @classmethod
    def compute_daily_analysis(cls, transactions: List[Any]) -> Dict[str, Any]:
        """Calculates daily aggregates and identifies peak transaction days."""
        daily_debits = defaultdict(Decimal)
        daily_credits = defaultdict(Decimal)

        for t in transactions:
            dt = str(t.transaction_date)
            daily_debits[dt] += Decimal(str(t.debit_amount))
            daily_credits[dt] += Decimal(str(t.credit_amount))

        peak_debit_day = max(daily_debits.items(), key=lambda x: x[1])[0] if daily_debits else None
        peak_credit_day = max(daily_credits.items(), key=lambda x: x[1])[0] if daily_credits else None

        return {
            "highest_debit_day": peak_debit_day,
            "highest_credit_day": peak_credit_day
        }

    @classmethod
    def compute_payment_modes(cls, transactions: List[Any]) -> List[Dict[str, Any]]:
        """Calculates breakdown by payment mode (UPI, NEFT, RTGS, IMPS, Cash, etc.)."""
        counts = defaultdict(int)
        volumes = defaultdict(lambda: Decimal("0.00"))
        total_vol = Decimal("0.00")

        for t in transactions:
            mode = t.payment_mode or "TRANSFER"
            amt = Decimal(str(t.debit_amount)) + Decimal(str(t.credit_amount))
            counts[mode] += 1
            volumes[mode] += amt
            total_vol += amt

        results = []
        for mode, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            vol = volumes[mode]
            pct = float((vol / total_vol) * 100) if total_vol > 0 else 0.0
            results.append({
                "mode": mode,
                "count": count,
                "total_amount": vol,
                "percentage": round(pct, 2)
            })

        return results

    @classmethod
    def compute_categories(cls, transactions: List[Any]) -> List[Dict[str, Any]]:
        """Calculates spending breakdown by category with % of debit."""
        cat_debits = defaultdict(lambda: Decimal("0.00"))
        cat_credits = defaultdict(lambda: Decimal("0.00"))
        cat_counts = defaultdict(int)
        total_debits = Decimal("0.00")

        for t in transactions:
            cat = t.category or "Miscellaneous"
            dr = Decimal(str(t.debit_amount))
            cr = Decimal(str(t.credit_amount))
            cat_debits[cat] += dr
            cat_credits[cat] += cr
            cat_counts[cat] += 1
            total_debits += dr

        results = []
        for cat, dr_vol in sorted(cat_debits.items(), key=lambda x: x[1], reverse=True):
            pct = float((dr_vol / total_debits) * 100) if total_debits > 0 else 0.0
            results.append({
                "category": cat,
                "debit_amount": dr_vol,
                "credit_amount": cat_credits[cat],
                "transaction_count": cat_counts[cat],
                "percentage_of_debit": round(pct, 2)
            })

        return results

    @classmethod
    def compute_top_transactions(cls, transactions: List[Any], limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """Finds top debits and top credits."""
        debits = [t for t in transactions if Decimal(str(t.debit_amount)) > 0]
        credits = [t for t in transactions if Decimal(str(t.credit_amount)) > 0]

        top_dr = sorted(debits, key=lambda x: Decimal(str(x.debit_amount)), reverse=True)[:limit]
        top_cr = sorted(credits, key=lambda x: Decimal(str(x.credit_amount)), reverse=True)[:limit]

        def to_dict(t, is_debit=True):
            return {
                "id": str(t.id),
                "date": str(t.transaction_date),
                "narration": t.narration,
                "amount": Decimal(str(t.debit_amount if is_debit else t.credit_amount)),
                "transaction_type": "DEBIT" if is_debit else "CREDIT",
                "payment_mode": t.payment_mode,
                "counterparty": t.counterparty or t.narration[:30],
                "category": t.category
            }

        return {
            "top_debits": [to_dict(t, True) for t in top_dr],
            "top_credits": [to_dict(t, False) for t in top_cr]
        }

    @classmethod
    def compute_tax_summary(cls, transactions: List[Any]) -> List[Dict[str, Any]]:
        """Identifies GST, TDS, Advance Tax, Self Assessment, and Professional Tax."""
        tax_groups = {
            "GST": [],
            "TDS": [],
            "Income Tax": [],
            "Local Tax": []
        }

        for t in transactions:
            if t.category == "Tax":
                sub = t.subcategory or "Income Tax"
                if sub in tax_groups:
                    tax_groups[sub].append(t)
                else:
                    tax_groups["Income Tax"].append(t)

        results = []
        for tax_type, items in tax_groups.items():
            tot = sum([Decimal(str(i.debit_amount)) for i in items], Decimal("0.00"))
            results.append({
                "tax_type": tax_type,
                "total_paid": tot,
                "transaction_count": len(items),
                "transactions": [
                    {
                        "id": str(i.id),
                        "date": str(i.transaction_date),
                        "narration": i.narration,
                        "amount": Decimal(str(i.debit_amount)),
                        "transaction_type": "DEBIT",
                        "payment_mode": i.payment_mode,
                        "counterparty": i.counterparty,
                        "category": "Tax"
                    } for i in items
                ]
            })

        return results

    @classmethod
    def detect_internal_transfers(cls, statements_txns: List[List[Any]]) -> List[Dict[str, Any]]:
        """
        Cross-account internal transfer detection:
        Identifies reciprocal debit and credit pairs occurring within +/- 2 days for the same amount across different accounts.
        """
        internal_transfers = []
        if len(statements_txns) < 2:
            return internal_transfers

        # Flatten all transactions with their origin statement index
        indexed_txns = []
        for s_idx, txns in enumerate(statements_txns):
            for t in txns:
                indexed_txns.append((s_idx, t))

        matched_ids = set()

        for i in range(len(indexed_txns)):
            s_i, t_i = indexed_txns[i]
            if t_i.id in matched_ids:
                continue

            dr_i = Decimal(str(t_i.debit_amount))
            if dr_i <= 0:
                continue

            # Look for reciprocal credit in other statement
            for j in range(len(indexed_txns)):
                s_j, t_j = indexed_txns[j]
                if s_i == s_j or t_j.id in matched_ids:
                    continue

                cr_j = Decimal(str(t_j.credit_amount))
                if cr_j == dr_i:
                    day_diff = abs((t_i.transaction_date - t_j.transaction_date).days)
                    if day_diff <= 2:
                        # Reciprocal transfer detected!
                        matched_ids.add(t_i.id)
                        matched_ids.add(t_j.id)
                        internal_transfers.append({
                            "debit_txn_id": str(t_i.id),
                            "credit_txn_id": str(t_j.id),
                            "amount": dr_i,
                            "date": str(t_i.transaction_date),
                            "narration_out": t_i.narration,
                            "narration_in": t_j.narration
                        })
                        break

        return internal_transfers
