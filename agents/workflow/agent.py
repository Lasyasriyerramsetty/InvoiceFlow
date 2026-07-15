from decimal import Decimal
from typing import Any

from agents.base import BaseAgent
from shared.schemas.agent_outputs import WorkflowRoute


class WorkflowAgent(BaseAgent):
    name = "WorkflowAgent"
    description = "Routes invoices to appropriate approvers based on amount and risk"

    ROUTING_RULES = [
        {"role": "AP Clerk", "department": "Accounts Payable", "max_amount": 5000, "max_risk": 20, "sla": 8},
        {"role": "Finance Manager", "department": "Finance", "max_amount": 25000, "max_risk": 50, "sla": 24},
        {"role": "Procurement", "department": "Procurement", "max_amount": 100000, "max_risk": 70, "sla": 48},
        {"role": "Director", "department": "Executive", "max_amount": 500000, "max_risk": 85, "sla": 72},
        {"role": "CFO", "department": "Executive", "max_amount": float("inf"), "max_risk": 100, "sla": 96},
    ]

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        extracted = context.get("extracted_invoice", {})
        risk_score = context.get("risk_score")
        exceptions = context.get("exceptions", [])
        fraud = context.get("fraud_assessment")

        amount = Decimal(str(extracted.get("total_amount", 0)))
        overall_risk = risk_score.overall_score if risk_score and hasattr(risk_score, "overall_score") else context.get("risk_factors", 0)

        routes: list[WorkflowRoute] = []
        priority = 1

        for rule in self.ROUTING_RULES:
            if amount <= Decimal(str(rule["max_amount"])) or overall_risk <= rule["max_risk"]:
                routes.append(
                    WorkflowRoute(
                        approver_role=rule["role"],
                        department=rule["department"],
                        priority=priority,
                        reason=self._build_reason(amount, overall_risk, rule),
                        sla_hours=rule["sla"],
                    )
                )
                priority += 1
                if amount <= Decimal(str(rule["max_amount"])):
                    break

        if any(
            (e.category.value if hasattr(e, "category") else e.get("category")) in ("price_mismatch", "missing_po")
            for e in exceptions
        ):
            routes.append(
                WorkflowRoute(
                    approver_role="Procurement",
                    department="Procurement",
                    priority=1,
                    reason="PO or pricing exception requires procurement review",
                    sla_hours=24,
                )
            )

        if fraud and (fraud.is_suspicious if hasattr(fraud, "is_suspicious") else fraud.get("is_suspicious")):
            routes.insert(
                0,
                WorkflowRoute(
                    approver_role="Legal",
                    department="Legal & Compliance",
                    priority=0,
                    reason="Fraud indicators detected — legal review required",
                    sla_hours=12,
                ),
            )

        routes = sorted(routes, key=lambda r: r.priority)
        insight = self._create_insight(
            reasoning=f"Workflow routed to {len(routes)} approver(s). Primary: {routes[0].approver_role if routes else 'Auto-approve'}.",
            confidence=0.93,
            evidence=[f"{r.approver_role} ({r.department}): {r.reason}" for r in routes],
            next_action=f"Await approval from {routes[0].approver_role}" if routes else "Auto-process payment",
        )

        return {"workflow_routes": routes, "insight": insight}

    def _build_reason(self, amount: Decimal, risk: float, rule: dict) -> str:
        if amount > Decimal(str(rule["max_amount"])):
            return f"Invoice amount {amount:,.2f} exceeds {rule['role']} approval limit"
        if risk > rule["max_risk"]:
            return f"Risk score {risk:.0f} requires {rule['role']} review"
        return f"Standard routing to {rule['role']} per approval matrix"
