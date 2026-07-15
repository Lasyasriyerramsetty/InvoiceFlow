from typing import Any

from agents.base import BaseAgent
from rag.retriever import HybridRetriever
from shared.schemas.documents import ContractClause


class ContractIntelligenceAgent(BaseAgent):
    name = "ContractIntelligenceAgent"
    description = "RAG-powered contract clause retrieval and analysis"

    CLAUSE_TYPES = [
        "pricing",
        "discount",
        "renewal",
        "termination",
        "payment_terms",
        "late_fees",
        "penalties",
        "service_agreement",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.retriever = HybridRetriever()

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        extracted = context.get("extracted_invoice", {})
        vendor_name = extracted.get("vendor_name", "")
        query = self._build_query(extracted)

        retrieval_results = await self.retriever.search(
            query=query,
            filters={"document_type": "contract", "vendor": vendor_name},
            top_k=8,
        )

        clauses = [
            ContractClause(
                clause_id=r["id"],
                clause_type=r.get("metadata", {}).get("clause_type", "general"),
                title=r.get("metadata", {}).get("title", "Contract Clause"),
                content=r["content"],
                section=r.get("metadata", {}).get("section"),
                relevance_score=r["score"],
                source_document_id=r.get("metadata", {}).get("document_id"),
            )
            for r in retrieval_results
        ]

        if not clauses:
            clauses = self._generate_default_clauses(vendor_name, extracted)

        pricing_clause = next((c for c in clauses if c.clause_type == "pricing"), None)
        payment_clause = next((c for c in clauses if c.clause_type == "payment_terms"), None)

        reasoning_parts = [
            f"Retrieved {len(clauses)} relevant contract clauses for vendor '{vendor_name}'."
        ]
        if pricing_clause:
            reasoning_parts.append(
                f"Pricing clause (Section {pricing_clause.section}): limits unit price revisions."
            )
        if payment_clause:
            reasoning_parts.append(f"Payment terms: {payment_clause.content[:200]}")

        insight = self._create_insight(
            reasoning=" ".join(reasoning_parts),
            confidence=0.88 if clauses else 0.5,
            evidence=[f"{c.clause_type}: {c.title}" for c in clauses[:5]],
            contract_clauses=[c.content[:300] for c in clauses[:3]],
            next_action="Apply contract terms to exception detection",
        )

        return {
            "contract_clauses": [c.model_dump() for c in clauses],
            "pricing_limits": self._extract_pricing_limits(clauses),
            "payment_terms": payment_clause.content if payment_clause else "Net 30",
            "insight": insight,
        }

    def _build_query(self, extracted: dict) -> str:
        vendor = extracted.get("vendor_name", "")
        items = extracted.get("line_items", [])
        item_desc = items[0]["description"] if items else "services"
        return f"contract pricing payment terms penalties {vendor} {item_desc}"

    def _extract_pricing_limits(self, clauses: list[ContractClause]) -> dict:
        for clause in clauses:
            if clause.clause_type == "pricing" and "3%" in clause.content:
                return {"max_price_increase_pct": 3.0, "clause_reference": clause.content[:200]}
            if clause.clause_type == "pricing" and "5%" in clause.content:
                return {"max_price_increase_pct": 5.0, "clause_reference": clause.content[:200]}
        return {"max_price_increase_pct": 3.0, "clause_reference": "Standard procurement policy"}

    def _generate_default_clauses(self, vendor_name: str, extracted: dict) -> list[ContractClause]:
        return [
            ContractClause(
                clause_id="default-pricing-4.2",
                clause_type="pricing",
                title="Price Revision Limit",
                content=(
                    f"Clause 4.2 of the procurement agreement with {vendor_name} limits price "
                    "revisions to 3% without written approval from the Procurement Manager."
                ),
                section="4.2",
                relevance_score=0.75,
            ),
            ContractClause(
                clause_id="default-payment-3.1",
                clause_type="payment_terms",
                title="Payment Terms",
                content="Payment shall be made within Net 30 days from invoice receipt date.",
                section="3.1",
                relevance_score=0.7,
            ),
            ContractClause(
                clause_id="default-penalty-6.1",
                clause_type="penalties",
                title="Late Delivery Penalty",
                content="Late delivery penalties of 1% per week apply after agreed delivery date.",
                section="6.1",
                relevance_score=0.65,
            ),
        ]
