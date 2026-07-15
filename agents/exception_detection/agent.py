import uuid
from decimal import Decimal
from typing import Any

from agents.base import BaseAgent
from shared.schemas.agent_outputs import ExceptionCategory, ExceptionDetail, ExceptionSeverity


class ExceptionDetectionAgent(BaseAgent):
    name = "ExceptionDetectionAgent"
    description = "Detects all invoice exceptions with risk scoring and detailed reasoning"

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        extracted = context.get("extracted_invoice", {})
        po_result = context.get("po_match_result", {})
        policy_result = context.get("policy_validation", {})
        contract_clauses = context.get("contract_clauses", [])
        pricing_limits = context.get("pricing_limits", {})

        exceptions: list[ExceptionDetail] = []

        for mismatch in po_result.get("mismatches", []):
            exc = self._mismatch_to_exception(mismatch, extracted, contract_clauses, pricing_limits)
            if exc:
                exceptions.append(exc)

        for violation in policy_result.get("violations", []):
            exceptions.append(
                ExceptionDetail(
                    exception_id=str(uuid.uuid4()),
                    category=ExceptionCategory.POLICY_VIOLATION,
                    severity=ExceptionSeverity(violation.get("severity", "medium")),
                    title=f"Policy Violation: {violation['policy']}",
                    description=violation["violation"],
                    reasoning=f"Finance Policy Agent detected: {violation['violation']}",
                    confidence=0.91,
                    policy_reference=violation["policy"],
                    suggested_resolution="Review with Finance Manager and obtain policy exception if needed",
                    business_impact="Payment processing delayed pending policy review",
                )
            )

        if not extracted.get("po_number") and Decimal(str(extracted.get("total_amount", 0))) > 1000:
            exceptions.append(
                ExceptionDetail(
                    exception_id=str(uuid.uuid4()),
                    category=ExceptionCategory.MISSING_PO,
                    severity=ExceptionSeverity.HIGH,
                    title="Missing Purchase Order Reference",
                    description="Invoice exceeds $1,000 threshold but no PO number found",
                    reasoning=(
                        "Procurement Policy PROC-001 requires a valid PO for all invoices "
                        "exceeding $1,000. No PO reference was extracted from this invoice."
                    ),
                    confidence=0.94,
                    policy_reference="PROC-001",
                    suggested_resolution="Request PO from requester or reject invoice",
                    business_impact="Cannot process payment without PO validation",
                    financial_impact=Decimal(str(extracted.get("total_amount", 0))),
                )
            )

        duplicate_check = context.get("duplicate_check", {})
        if duplicate_check.get("is_duplicate"):
            exceptions.append(
                ExceptionDetail(
                    exception_id=str(uuid.uuid4()),
                    category=ExceptionCategory.DUPLICATE_INVOICE,
                    severity=ExceptionSeverity.CRITICAL,
                    title="Potential Duplicate Invoice",
                    description=f"Invoice {extracted.get('invoice_number')} may be a duplicate",
                    reasoning=duplicate_check.get("reasoning", "Matching invoice number and vendor found"),
                    confidence=duplicate_check.get("confidence", 0.85),
                    evidence=duplicate_check.get("evidence", []),
                    suggested_resolution="Verify with vendor before processing",
                    business_impact="Risk of double payment",
                    estimated_loss=Decimal(str(extracted.get("total_amount", 0))),
                )
            )

        risk_score = self._calculate_risk(exceptions)
        insight = self._create_insight(
            reasoning=(
                f"Detected {len(exceptions)} exception(s) with overall risk score {risk_score:.0f}/100. "
                + (exceptions[0].reasoning if exceptions else "No exceptions detected — invoice is clean.")
            ),
            confidence=0.89,
            evidence=[e.title for e in exceptions],
            business_impact=f"{len(exceptions)} issues require resolution",
            financial_impact=sum(e.financial_impact for e in exceptions),
            estimated_loss=sum(e.estimated_loss for e in exceptions),
            next_action="Generate recommendations" if exceptions else "Auto-approve eligible",
        )

        return {"exceptions": exceptions, "risk_factors": risk_score, "insight": insight}

    def _mismatch_to_exception(
        self, mismatch: dict, extracted: dict, clauses: list, pricing_limits: dict
    ) -> ExceptionDetail | None:
        type_map = {
            "price_mismatch": ExceptionCategory.PRICE_MISMATCH,
            "quantity_mismatch": ExceptionCategory.QUANTITY_MISMATCH,
            "currency_mismatch": ExceptionCategory.CURRENCY_MISMATCH,
            "missing_po": ExceptionCategory.MISSING_PO,
            "amount_mismatch": ExceptionCategory.PRICE_MISMATCH,
            "delivery_mismatch": ExceptionCategory.DELIVERY_MISMATCH,
        }
        category = type_map.get(mismatch["type"])
        if not category:
            return None

        pricing_clause = pricing_limits.get("clause_reference", "Clause 4.2")
        financial_impact = Decimal(str(mismatch.get("financial_impact", 0)))

        reasoning = mismatch["description"]
        if category == ExceptionCategory.PRICE_MISMATCH and financial_impact > 0:
            inv_num = extracted.get("invoice_number", "N/A")
            reasoning = (
                f"Invoice {inv_num} exceeds the contractual unit price, resulting in a projected "
                f"overpayment of {extracted.get('currency', 'USD')} {financial_impact:,.2f}. "
                f"{pricing_clause} limits price revisions to "
                f"{pricing_limits.get('max_price_increase_pct', 3)}% without written approval. "
                "Recommend escalation to Procurement Manager."
            )

        return ExceptionDetail(
            exception_id=str(uuid.uuid4()),
            category=category,
            severity=ExceptionSeverity(mismatch.get("severity", "medium")),
            title=mismatch["type"].replace("_", " ").title(),
            description=mismatch["description"],
            reasoning=reasoning,
            confidence=0.87,
            contract_clause=pricing_clause if category == ExceptionCategory.PRICE_MISMATCH else None,
            suggested_resolution="Contact vendor for credit note or obtain procurement approval",
            business_impact="Overpayment risk if approved without review",
            financial_impact=financial_impact,
            estimated_loss=financial_impact,
            expected_value=mismatch.get("expected"),
            actual_value=mismatch.get("actual"),
        )

    def _calculate_risk(self, exceptions: list[ExceptionDetail]) -> float:
        if not exceptions:
            return 0.0
        severity_weights = {"low": 10, "medium": 25, "high": 50, "critical": 80}
        total = sum(severity_weights.get(e.severity.value, 20) for e in exceptions)
        return min(100.0, total)
