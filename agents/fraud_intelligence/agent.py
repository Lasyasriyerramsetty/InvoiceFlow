from decimal import Decimal
from typing import Any

from agents.base import BaseAgent
from ml.fraud_detector import FraudDetector
from shared.schemas.agent_outputs import FraudAssessment


class FraudIntelligenceAgent(BaseAgent):
    name = "FraudIntelligenceAgent"
    description = "ML + AI fraud detection for invoices and vendors"

    def __init__(self) -> None:
        super().__init__()
        self.detector = FraudDetector()

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        extracted = context.get("extracted_invoice", {})
        historical = context.get("historical_invoices", [])

        ml_result = self.detector.analyze(
            invoice_data=extracted,
            historical=historical,
            vendor_trust_score=context.get("vendor_trust_score", 75.0),
        )

        ai_indicators = self._detect_ai_patterns(extracted, context)
        all_indicators = ml_result["indicators"] + ai_indicators
        fraud_confidence = min(1.0, ml_result["score"] / 100 + len(ai_indicators) * 0.1)

        assessment = FraudAssessment(
            is_suspicious=fraud_confidence >= 0.5,
            fraud_confidence=fraud_confidence,
            fraud_types=ml_result.get("fraud_types", []) + [i["type"] for i in ai_indicators],
            indicators=[i["description"] for i in all_indicators],
            reasoning=self._build_reasoning(all_indicators, fraud_confidence),
            recommended_action=(
                "Block payment and escalate to Fraud Investigation Team"
                if fraud_confidence >= 0.7
                else "Enhanced review recommended" if fraud_confidence >= 0.4
                else "No fraud indicators detected"
            ),
        )

        insight = self._create_insight(
            reasoning=assessment.reasoning,
            confidence=0.85,
            evidence=assessment.indicators[:5],
            business_impact="Payment blocked" if assessment.is_suspicious else "Low fraud risk",
            suggested_resolution=assessment.recommended_action,
            next_action="Escalate to Security" if fraud_confidence >= 0.7 else "Continue processing",
        )

        return {"fraud_assessment": assessment, "insight": insight}

    def _detect_ai_patterns(self, extracted: dict, context: dict) -> list[dict]:
        indicators = []
        total = Decimal(str(extracted.get("total_amount", 0)))

        if total > 0 and str(total).endswith("99") or str(total).endswith("00.00"):
            round_count = sum(1 for item in extracted.get("line_items", []) if float(item.get("total_amount", 0)) % 1 == 0)
            if round_count > 2:
                indicators.append({
                    "type": "round_off_fraud",
                    "description": "Multiple line items with suspicious round amounts detected",
                })

        vendor = extracted.get("vendor_name", "").lower()
        suspicious_names = ["test vendor", "cash", "misc", "unknown"]
        if any(s in vendor for s in suspicious_names):
            indicators.append({
                "type": "fake_vendor",
                "description": f"Vendor name '{extracted.get('vendor_name')}' matches suspicious pattern",
            })

        if context.get("split_invoice_detected"):
            indicators.append({
                "type": "split_invoice",
                "description": "Multiple invoices from same vendor just below approval threshold",
            })

        return indicators

    def _build_reasoning(self, indicators: list, confidence: float) -> str:
        if not indicators:
            return "No fraud indicators detected. Invoice passes fraud screening with high confidence."
        indicator_text = "; ".join(i["description"] for i in indicators[:3])
        return (
            f"Fraud analysis identified {len(indicators)} indicator(s) with {confidence:.0%} confidence. "
            f"Key findings: {indicator_text}."
        )
