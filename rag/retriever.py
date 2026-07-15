import os
from typing import Any

import structlog

from rag.chunker import DocumentChunker
from rag.embeddings import EmbeddingService

logger = structlog.get_logger(__name__)

KNOWLEDGE_BASE = [
    {
        "id": "contract-acme-001",
        "content": (
            "Clause 4.2 — Price Revision Limit: The Supplier agrees that unit prices shall not "
            "increase by more than 3% during the contract term without prior written approval "
            "from the Procurement Manager. Any price revision exceeding this threshold requires "
            "a formal amendment signed by both parties."
        ),
        "metadata": {"document_type": "contract", "clause_type": "pricing", "vendor": "Acme Corp", "section": "4.2", "title": "Price Revision Limit"},
    },
    {
        "id": "contract-acme-002",
        "content": (
            "Clause 3.1 — Payment Terms: Payment shall be made within Net 30 days from the "
            "date of receipt of a valid invoice. Early payment discounts of 2% apply if paid "
            "within 10 days. Late payments incur interest at 1.5% per month."
        ),
        "metadata": {"document_type": "contract", "clause_type": "payment_terms", "vendor": "Acme Corp", "section": "3.1", "title": "Payment Terms"},
    },
    {
        "id": "policy-fin-001",
        "content": (
            "Finance Policy FIN-001: All invoices exceeding $100,000 require CFO approval. "
            "Invoices between $25,000 and $100,000 require Director approval. Invoices between "
            "$5,000 and $25,000 require Finance Manager approval."
        ),
        "metadata": {"document_type": "policy", "clause_type": "approval", "title": "Approval Thresholds"},
    },
    {
        "id": "policy-proc-001",
        "content": (
            "Procurement Policy PROC-001: A valid Purchase Order is mandatory for all "
            "invoices exceeding $1,000. Three-way matching (Invoice, PO, Goods Receipt) "
            "must be completed before payment authorization."
        ),
        "metadata": {"document_type": "policy", "clause_type": "procurement", "title": "PO Requirement"},
    },
    {
        "id": "policy-gst-001",
        "content": (
            "GST Compliance Policy FIN-012: All invoices from Indian vendors must include "
            "a valid 15-character GSTIN. Input tax credit cannot be claimed without valid GST "
            "documentation. Non-compliant invoices must be rejected."
        ),
        "metadata": {"document_type": "policy", "clause_type": "compliance", "title": "GST Requirements"},
    },
]


class VectorStore:
    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.documents: list[dict] = []
        self.embeddings: list[list[float]] = []
        self._load_knowledge_base()

    def _load_knowledge_base(self) -> None:
        for doc in KNOWLEDGE_BASE:
            self.add_document(doc["content"], doc["metadata"], doc["id"])

    def add_document(self, content: str, metadata: dict, doc_id: str | None = None) -> str:
        doc_id = doc_id or f"doc-{len(self.documents)}"
        embedding = self.embedding_service.embed_query(content)
        self.documents.append({"id": doc_id, "content": content, "metadata": metadata})
        self.embeddings.append(embedding)
        return doc_id

    def search(self, query_embedding: list[float], top_k: int = 5, filters: dict | None = None) -> list[dict]:
        if not self.documents:
            return []

        scores = []
        for idx, emb in enumerate(self.embeddings):
            if filters:
                meta = self.documents[idx]["metadata"]
                if filters.get("document_type") and meta.get("document_type") != filters["document_type"]:
                    continue
                if filters.get("vendor") and meta.get("vendor") and filters["vendor"].lower() not in meta.get("vendor", "").lower():
                    continue
            score = self._cosine_similarity(query_embedding, emb)
            scores.append((idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in scores[:top_k]:
            doc = self.documents[idx]
            results.append({"id": doc["id"], "content": doc["content"], "metadata": doc["metadata"], "score": score})
        return results

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


class HybridRetriever:
    def __init__(self) -> None:
        self.vector_store = VectorStore()
        self.embedding_service = EmbeddingService()
        self.chunker = DocumentChunker()
        self._bm25_index: dict[int, list[str]] = {}

    async def search(
        self, query: str, filters: dict[str, Any] | None = None, top_k: int = 5
    ) -> list[dict]:
        query_embedding = self.embedding_service.embed_query(query)
        vector_results = self.vector_store.search(query_embedding, top_k=top_k * 2, filters=filters)

        bm25_results = self._bm25_search(query, top_k=top_k * 2, filters=filters)
        merged = self._reciprocal_rank_fusion(vector_results, bm25_results, top_k)
        return self._rerank(query, merged, top_k)

    async def index_document(
        self, text: str, document_id: str, document_type: str, metadata: dict | None = None
    ) -> int:
        chunks = self.chunker.chunk_by_sections(text, document_id, document_type)
        count = 0
        for chunk in chunks:
            meta = {**(metadata or {}), **chunk["metadata"]}
            self.vector_store.add_document(chunk["content"], meta, chunk["id"])
            count += 1
        logger.info("document_indexed", document_id=document_id, chunks=count)
        return count

    def _bm25_search(self, query: str, top_k: int, filters: dict | None) -> list[dict]:
        query_terms = query.lower().split()
        scores = []
        for idx, doc in enumerate(self.vector_store.documents):
            if filters:
                meta = doc["metadata"]
                if filters.get("document_type") and meta.get("document_type") != filters["document_type"]:
                    continue
            content_lower = doc["content"].lower()
            score = sum(content_lower.count(term) for term in query_terms)
            if score > 0:
                scores.append((idx, score / max(len(query_terms), 1)))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [
            {
                "id": self.vector_store.documents[idx]["id"],
                "content": self.vector_store.documents[idx]["content"],
                "metadata": self.vector_store.documents[idx]["metadata"],
                "score": score,
            }
            for idx, score in scores[:top_k]
        ]

    def _reciprocal_rank_fusion(
        self, vector_results: list[dict], bm25_results: list[dict], top_k: int, k: int = 60
    ) -> list[dict]:
        scores: dict[str, float] = {}
        docs: dict[str, dict] = {}

        for rank, result in enumerate(vector_results):
            doc_id = result["id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
            docs[doc_id] = result

        for rank, result in enumerate(bm25_results):
            doc_id = result["id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
            docs[doc_id] = docs.get(doc_id, result)

        sorted_ids = sorted(scores, key=scores.get, reverse=True)[:top_k]
        return [{**docs[doc_id], "score": scores[doc_id]} for doc_id in sorted_ids]

    def _rerank(self, query: str, results: list[dict], top_k: int) -> list[dict]:
        query_terms = set(query.lower().split())
        for result in results:
            content_terms = set(result["content"].lower().split())
            overlap = len(query_terms & content_terms) / max(len(query_terms), 1)
            result["score"] = result["score"] * 0.7 + overlap * 0.3
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
