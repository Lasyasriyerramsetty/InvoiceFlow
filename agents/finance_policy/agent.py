from decimal import Decimal
from typing import Any

from agents.base import BaseAgent


class FinancePolicyAgent(BaseAgent):
    name = "FinancePolicyAgent"
    description = "Validates approval policies, GST, currency, procurement and budget rules"

    POLICIES = {
        "approval_thresholds": [
            {"max_amount": 5000, "approver": "AP Clerk", "auto_approve": True},
            {"max_amount": 25000, "approver": "Finance Manager", "auto_approve": False},
            {"max_amount": 100000, "approver": "Director", "auto_approve": False},
            {"max_amount": float("inf"), "approver": "CFO", "auto_approve": False},
        ],
        "gst_required_countries": ["IN"],
        "max_invoice_age_days": 90,
        "blocked_currencies": [],
        "vendor_spend_limit": 500000,
    }

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        extracted = context.get("extracted_invoice", {})
        violations = []

        total = Decimal(str(extracted.get("total_amount", 0)))
        currency = extracted.get("currency", "USD")
        gst = extracted.get("gst_number")
        country = context.get("vendor_country", "US")

        required_approver = self._get_required_approver(total)
        if currency in self.POLICIES["blocked_currencies"]:
            violations.append({
                "policy": "Currency Policy FIN-003",
                "violation": f"Currency {currency} is not approved for payment",
                "severity": "critical",
            })

        if country in self.POLICIES["gst_required_countries"] and not gst:
            violations.append({
                "policy": "GST Compliance Policy FIN-012",
                "violation": "GST number required for Indian vendors but not found on invoice",
                "severity": "high",
            })

        if total > Decimal("100000"):
            violations.append({
                "policy": "High-Value Approval Policy FIN-001",
                "violation": f"Invoice amount {currency} {total:,.2f} requires CFO approval",
                "severity": "high",
            })

        budget_remaining = context.get("budget_remaining", Decimal("1000000"))
        if total > budget_remaining:
            violations.append({
                "policy": "Budget Policy FIN-008",
                "violation": f"Invoice exceeds department budget by {total - budget_remaining:,.2f}",
                "severity": "high",
            })

        vendor_spend = context.get("vendor_ytd_spend", Decimal("0"))
        if vendor_spend + total > Decimal(str(self.POLICIES["vendor_spend_limit"])):
            violations.append({
                "policy": "Vendor Spend Limit Policy PROC-005",
                "violation": "Vendor annual spend limit would be exceeded",
                "severity": "medium",
            })

        compliance_score = max(0, 100 - len(violations) * 20)
        insight = self._create_insight(
            reasoning=(
                f"Policy validation complete. {len(violations)} violation(s) found. "
                f"Required approver: {required_approver}. Compliance score: {compliance_score}%."
            ),
            confidence=0.92,
            evidence=[v["violation"] for v in violations],
            policy_references=[v["policy"] for v in violations],
            suggested_resolution="Resolve policy violations before approval" if violations else "Policy compliant",
            next_action=f"Route to {required_approver}" if violations else "Proceed to exception detection",
        )

        return {
            "policy_validation": {
                "violations": violations,
                "required_approver": required_approver,
                "compliance_score": compliance_score,
                "auto_approve_eligible": not violations and total <= Decimal("5000"),
            },
            "insight": insight,
        }

    def _get_required_approver(self, amount: Decimal) -> str:
        for threshold in self.POLICIES["approval_thresholds"]:
            if amount <= Decimal(str(threshold["max_amount"])):
                return threshold["approver"]
        return "CFO"
