from decimal import Decimal
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class FraudDetector:
    """Hybrid ML + rule-based fraud detection engine."""

    APPROVAL_THRESHOLDS = [5000, 25000, 100000]

    def analyze(
        self,
        invoice_data: dict[str, Any],
        historical: list[dict] | None = None,
        vendor_trust_score: float = 75.0,
    ) -> dict[str, Any]:
        historical = historical or []
        indicators: list[dict] = []
        score = 0.0
        fraud_types: list[str] = []

        total = Decimal(str(invoice_data.get("total_amount", 0)))
        invoice_number = invoice_data.get("invoice_number", "")
        vendor = invoice_data.get("vendor_name", "")

        if self._is_duplicate(invoice_number, vendor, historical):
            indicators.append({"type": "duplicate", "description": f"Duplicate invoice {invoice_number} detected in history"})
            fraud_types.append("duplicate_invoice")
            score += 35

        if self._is_split_invoice(total, historical, vendor):
            indicators.append({"type": "split", "description": "Potential split invoice pattern detected near approval threshold"})
            fraud_types.append("split_invoice")
            score += 30

        if vendor_trust_score < 50:
            indicators.append({"type": "vendor_risk", "description": f"Vendor trust score {vendor_trust_score} is below threshold"})
            fraud_types.append("untrusted_vendor")
            score += 25

        if self._has_round_amount_anomaly(invoice_data):
            indicators.append({"type": "round_amount", "description": "Suspicious round-number line items detected"})
            fraud_types.append("round_off_fraud")
            score += 15

        if self._detect_amount_anomaly(total, historical):
            indicators.append({"type": "anomaly", "description": "Invoice amount significantly deviates from vendor historical average"})
            fraud_types.append("amount_anomaly")
            score += 20

        benford_violation = self._benford_analysis(total)
        if benford_violation:
            indicators.append({"type": "benford", "description": "Amount distribution violates Benford's Law pattern"})
            fraud_types.append("statistical_anomaly")
            score += 10

        return {
            "score": min(100, score),
            "indicators": indicators,
            "fraud_types": fraud_types,
            "is_fraudulent": score >= 50,
        }

    def _is_duplicate(self, invoice_number: str, vendor: str, historical: list) -> bool:
        for inv in historical:
            if inv.get("invoice_number") == invoice_number and inv.get("vendor_name", "").lower() == vendor.lower():
                return True
        return False

    def _is_split_invoice(self, total: Decimal, historical: list, vendor: str) -> bool:
        for threshold in self.APPROVAL_THRESHOLDS:
            lower = Decimal(str(threshold * 0.85))
            upper = Decimal(str(threshold * 0.99))
            if lower <= total <= upper:
                recent = [
                    h for h in historical
                    if h.get("vendor_name", "").lower() == vendor.lower()
                    and lower <= Decimal(str(h.get("total_amount", 0))) <= upper
                ]
                if len(recent) >= 2:
                    return True
        return False

    def _has_round_amount_anomaly(self, invoice_data: dict) -> bool:
        line_items = invoice_data.get("line_items", [])
        round_count = sum(
            1 for item in line_items
            if float(item.get("total_amount", 0)) % 1000 == 0 and float(item.get("total_amount", 0)) > 0
        )
        return round_count >= 2

    def _detect_amount_anomaly(self, total: Decimal, historical: list) -> bool:
        if not historical:
            return False
        amounts = [Decimal(str(h.get("total_amount", 0))) for h in historical if h.get("total_amount")]
        if not amounts:
            return False
        avg = sum(amounts) / len(amounts)
        if avg == 0:
            return False
        deviation = abs(total - avg) / avg
        return deviation > 2.0

    def _benford_analysis(self, amount: Decimal) -> bool:
        if amount <= 0:
            return False
        first_digit = int(str(amount).replace(".", "").lstrip("0")[0]) if amount >= 1 else 0
        suspicious_digits = {8, 9}
        return first_digit in suspicious_digits and amount > Decimal("50000")
