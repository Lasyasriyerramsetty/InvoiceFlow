import hashlib
import os
from dataclasses import dataclass
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ChunkMetadata:
    document_id: str
    document_type: str
    chunk_index: int
    title: str
    clause_type: str | None = None
    vendor: str | None = None
    section: str | None = None


class DocumentChunker:
    CHUNK_SIZE = 512
    CHUNK_OVERLAP = 64

    def chunk_text(
        self,
        text: str,
        document_id: str,
        document_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        meta = metadata or {}
        chunks = []
        words = text.split()
        step = self.CHUNK_SIZE - self.CHUNK_OVERLAP

        for i in range(0, len(words), step):
            chunk_words = words[i : i + self.CHUNK_SIZE]
            if not chunk_words:
                continue
            content = " ".join(chunk_words)
            chunk_id = hashlib.md5(f"{document_id}:{i}".encode()).hexdigest()[:12]
            chunks.append({
                "id": chunk_id,
                "content": content,
                "metadata": {
                    "document_id": document_id,
                    "document_type": document_type,
                    "chunk_index": len(chunks),
                    "title": meta.get("title", f"Chunk {len(chunks)}"),
                    "clause_type": meta.get("clause_type"),
                    "vendor": meta.get("vendor"),
                    "section": meta.get("section"),
                },
            })
        return chunks

    def chunk_by_sections(self, text: str, document_id: str, document_type: str) -> list[dict]:
        import re

        sections = re.split(r"(?=(?:Clause|Section|Article)\s+\d+[\.\:])", text, flags=re.IGNORECASE)
        chunks = []
        for idx, section in enumerate(sections):
            section = section.strip()
            if len(section) < 20:
                continue
            clause_match = re.match(r"(?:Clause|Section|Article)\s+([\d\.]+)", section, re.IGNORECASE)
            section_num = clause_match.group(1) if clause_match else str(idx)
            clause_type = self._detect_clause_type(section)
            chunks.append({
                "id": f"{document_id}-sec-{idx}",
                "content": section[:2000],
                "metadata": {
                    "document_id": document_id,
                    "document_type": document_type,
                    "chunk_index": idx,
                    "title": f"Section {section_num}",
                    "section": section_num,
                    "clause_type": clause_type,
                },
            })
        return chunks if chunks else self.chunk_text(text, document_id, document_type)

    def _detect_clause_type(self, text: str) -> str:
        text_lower = text.lower()
        type_keywords = {
            "pricing": ["price", "pricing", "rate", "cost", "fee"],
            "payment_terms": ["payment", "net 30", "due date", "invoice date"],
            "termination": ["termination", "terminate", "cancel"],
            "renewal": ["renewal", "renew", "extension"],
            "penalties": ["penalty", "penalties", "late fee", "liquidated"],
            "discount": ["discount", "rebate", "reduction"],
            "service_agreement": ["service", "sla", "deliverable", "scope"],
        }
        for clause_type, keywords in type_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return clause_type
        return "general"
