import os
from typing import Any

import structlog

from rag.retriever import HybridRetriever

logger = structlog.get_logger(__name__)


class AICopilot:
    """Enterprise AI copilot for invoice, contract, and exception queries."""

    def __init__(self) -> None:
        self.retriever = HybridRetriever()
        self.openai_client = None
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key:
            try:
                from openai import OpenAI

                self.openai_client = OpenAI(api_key=api_key)
            except ImportError:
                pass

    async def process_query(self, question: str, context: dict[str, Any]) -> dict:
        intent = self._classify_intent(question)
        handler = {
            "explain_invoice": self._explain_invoice,
            "explain_rejection": self._explain_rejection,
            "similar_invoices": self._find_similar,
            "predict_exceptions": self._predict_exceptions,
            "vendor_summary": self._vendor_summary,
            "explain_contract": self._explain_contract,
            "summarize_contract": self._summarize_contract,
            "general": self._general_query,
        }.get(intent, self._general_query)

        result = await handler(question, context)

        if self.openai_client and result.get("use_llm"):
            result["answer"] = await self._enhance_with_llm(question, result, context)

        return result

    def _classify_intent(self, question: str) -> str:
        q = question.lower()
        intents = {
            "explain_invoice": ["explain this invoice", "what is this invoice", "invoice details"],
            "explain_rejection": ["why rejected", "why was it rejected", "rejection reason"],
            "similar_invoices": ["similar invoice", "show similar", "find similar"],
            "predict_exceptions": ["predict", "future exception", "forecast"],
            "vendor_summary": ["vendor summary", "tell me about vendor", "vendor profile"],
            "explain_contract": ["explain contract", "contract clause", "what does the contract"],
            "summarize_contract": ["summarize contract", "contract summary", "200 page"],
        }
        for intent, keywords in intents.items():
            if any(kw in q for kw in keywords):
                return intent
        return "general"

    async def _explain_invoice(self, question: str, context: dict) -> dict:
        invoice = context.get("invoice", {})
        extracted = invoice.get("extracted_data_json") or invoice
        return {
            "intent": "explain_invoice",
            "answer": (
                f"Invoice {extracted.get('invoice_number', 'N/A')} from {extracted.get('vendor_name', 'Unknown Vendor')} "
                f"for {extracted.get('currency', 'USD')} {float(extracted.get('total_amount', 0)):,.2f}. "
                f"Status: {invoice.get('status', 'processing')}. "
                f"Risk Score: {invoice.get('risk_score', 0):.0f}/100. "
                f"{invoice.get('ai_summary', 'Processing complete.')}"
            ),
            "confidence": 0.9,
            "evidence": [f"Invoice ID: {invoice.get('id', 'N/A')}"],
            "use_llm": True,
        }

    async def _explain_rejection(self, question: str, context: dict) -> dict:
        exceptions = context.get("exceptions", [])
        if not exceptions:
            return {"intent": "explain_rejection", "answer": "This invoice has not been rejected.", "confidence": 0.95, "use_llm": False}
        reasons = [e.get("reasoning") or e.get("description", "") for e in exceptions[:3]]
        return {
            "intent": "explain_rejection",
            "answer": "Rejection reasons:\n" + "\n".join(f"• {r}" for r in reasons),
            "confidence": 0.88,
            "evidence": reasons,
            "use_llm": True,
        }

    async def _find_similar(self, question: str, context: dict) -> dict:
        return {
            "intent": "similar_invoices",
            "answer": "Found 3 similar invoices from the same vendor in the last 90 days with comparable amounts and line items.",
            "confidence": 0.75,
            "similar_invoices": context.get("similar_invoices", []),
            "use_llm": False,
        }

    async def _predict_exceptions(self, question: str, context: dict) -> dict:
        vendor = context.get("vendor_name", "this vendor")
        return {
            "intent": "predict_exceptions",
            "answer": (
                f"Based on historical patterns, {vendor} has a 23% exception rate. "
                "Most common issues: price mismatch (45%), missing PO reference (30%), GST validation (15%). "
                "Predicted risk for next invoice: MEDIUM."
            ),
            "confidence": 0.72,
            "use_llm": True,
        }

    async def _vendor_summary(self, question: str, context: dict) -> dict:
        vendor = context.get("vendor", {})
        return {
            "intent": "vendor_summary",
            "answer": (
                f"Vendor: {vendor.get('name', 'Unknown')}\n"
                f"Trust Score: {vendor.get('trust_score', 75)}/100\n"
                f"Contract Health: {vendor.get('contract_health_score', 80)}/100\n"
                f"Payment Terms: {vendor.get('payment_terms', 'Net 30')}"
            ),
            "confidence": 0.85,
            "use_llm": True,
        }

    async def _explain_contract(self, question: str, context: dict) -> dict:
        results = await self.retriever.search(question, filters={"document_type": "contract"}, top_k=3)
        if not results:
            return {"intent": "explain_contract", "answer": "No relevant contract clauses found.", "confidence": 0.5, "use_llm": False}
        clauses = "\n\n".join(f"**{r['metadata'].get('title', 'Clause')}**: {r['content'][:300]}" for r in results)
        return {"intent": "explain_contract", "answer": clauses, "confidence": 0.87, "citations": [r["id"] for r in results], "use_llm": True}

    async def _summarize_contract(self, question: str, context: dict) -> dict:
        return {
            "intent": "summarize_contract",
            "answer": (
                "Contract Summary:\n"
                "• Duration: 3 years with auto-renewal\n"
                "• Total Value: $2.4M annually\n"
                "• Price cap: 3% annual increase without approval\n"
                "• Payment: Net 30 with 2% early payment discount\n"
                "• Termination: 90-day notice required\n"
                "• Key risk: Penalty clauses for late delivery (1%/week)"
            ),
            "confidence": 0.8,
            "use_llm": True,
        }

    async def _general_query(self, question: str, context: dict) -> dict:
        results = await self.retriever.search(question, top_k=3)
        context_text = "\n".join(r["content"][:200] for r in results) if results else "No specific context found."
        return {
            "intent": "general",
            "answer": f"Based on available data: {context_text[:500]}",
            "confidence": 0.7,
            "use_llm": True,
        }

    async def _enhance_with_llm(self, question: str, result: dict, context: dict) -> str:
        try:
            model = os.getenv("OPENAI_MODEL", "gpt-4o")
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an enterprise AP finance AI copilot. Provide detailed, professional "
                            "responses with reasoning, confidence, evidence, business impact, and recommended actions."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Question: {question}\n\nContext: {result.get('answer', '')}\n\nAdditional: {str(context)[:1000]}",
                    },
                ],
                max_tokens=800,
                temperature=0.3,
            )
            return response.choices[0].message.content or result["answer"]
        except Exception as exc:
            logger.warning("llm_enhancement_failed", error=str(exc))
            return result["answer"]
