from decimal import Decimal
from typing import Any

from agents.base import BaseAgent
from shared.schemas.agent_outputs import RecommendationResult, RiskLevel, RiskScore


class RecommendationAgent(BaseAgent):
    name = "RecommendationAgent"
    description = "Generates AI explanations, resolutions, and approval recommendations"

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        exceptions = context.get("exceptions", [])
        extracted = context.get("extracted_invoice", {})
        fraud = context.get("fraud_assessment")
        policy = context.get("policy_validation", {})
        insights = context.get("all_insights", [])

        total_impact = sum(
            Decimal(str(e.financial_impact if hasattr(e, "financial_impact") else e.get("financial_impact", 0)))
            for e in exceptions
        )

        if exceptions:
            primary = exceptions[0]
            exc_reasoning = primary.reasoning if hasattr(primary, "reasoning") else primary.get("reasoning", "")
            summary = exc_reasoning
            approval_rec = "Reject or escalate for manual review"
            escalation = "Procurement Manager"
        else:
            summary = (
                f"Invoice {extracted.get('invoice_number')} from {extracted.get('vendor_name')} "
                f"for {extracted.get('currency')} {Decimal(str(extracted.get('total_amount', 0))):,.2f} "
                "passed all validation checks. Recommend auto-approval."
            )
            approval_rec = "Auto-approve"
            escalation = None

        if fraud and (fraud.is_suspicious if hasattr(fraud, "is_suspicious") else fraud.get("is_suspicious")):
            approval_rec = "Block payment — fraud investigation required"
            escalation = "Fraud Investigation Team"

        resolution_steps = self._build_resolution_steps(exceptions, policy)
        risk_score = self._build_risk_score(context, exceptions, fraud)

        recommendation = RecommendationResult(
            summary=summary,
            approval_recommendation=approval_rec,
            escalation_recommendation=escalation,
            confidence=0.88 if not exceptions else 0.82,
            business_impact=self._assess_business_impact(exceptions),
            financial_impact=total_impact,
            resolution_steps=resolution_steps,
            insights=insights,
        )

        insight = self._create_insight(
            reasoning=summary,
            confidence=recommendation.confidence,
            suggested_resolution=approval_rec,
            business_impact=recommendation.business_impact,
            financial_impact=total_impact,
            next_action=escalation or "Process payment",
        )

        return {"recommendation": recommendation, "risk_score": risk_score, "insight": insight}

    def _build_resolution_steps(self, exceptions: list, policy: dict) -> list[str]:
        steps = []
        for exc in exceptions[:5]:
            resolution = exc.suggested_resolution if hasattr(exc, "suggested_resolution") else exc.get("suggested_resolution", "")
            if resolution:
                steps.append(resolution)
        if policy.get("violations"):
            steps.append(f"Obtain approval from {policy.get('required_approver', 'Finance Manager')}")
        if not steps:
            steps = ["Verify invoice details", "Approve for payment", "Schedule payment per terms"]
        return steps

    def _build_risk_score(self, context: dict, exceptions: list, fraud) -> RiskScore:
        po_score = context.get("po_match_result", {}).get("match_score", 100)
        compliance = context.get("policy_validation", {}).get("compliance_score", 100)
        fraud_score = 0.0
        if fraud:
            fraud_score = (fraud.fraud_confidence if hasattr(fraud, "fraud_confidence") else fraud.get("fraud_confidence", 0)) * 100

        exception_risk = context.get("risk_factors", 0)
        overall = min(100, (exception_risk * 0.4) + (fraud_score * 0.3) + ((100 - po_score) * 0.2) + ((100 - compliance) * 0.1))

        level = RiskLevel.MINIMAL
        if overall >= 80:
            level = RiskLevel.CRITICAL
        elif overall >= 60:
            level = RiskLevel.HIGH
        elif overall >= 40:
            level = RiskLevel.MEDIUM
        elif overall >= 20:
            level = RiskLevel.LOW

        return RiskScore(
            overall_score=overall,
            risk_level=level,
            fraud_score=fraud_score,
            compliance_score=compliance,
            matching_score=po_score,
            factors=[e.title if hasattr(e, "title") else e.get("title", "") for e in exceptions[:5]],
            heatmap_data={
                "price": 30 if any("price" in str(e) for e in exceptions) else 5,
                "fraud": fraud_score,
                "compliance": 100 - compliance,
                "matching": 100 - po_score,
            },
        )

    def _assess_business_impact(self, exceptions: list) -> str:
        if not exceptions:
            return "No business impact — invoice ready for processing"
        critical = sum(1 for e in exceptions if (e.severity.value if hasattr(e, "severity") else e.get("severity")) == "critical")
        if critical:
            return f"{critical} critical exception(s) — immediate attention required"
        return f"{len(exceptions)} exception(s) may delay payment processing by 2-5 business days"
