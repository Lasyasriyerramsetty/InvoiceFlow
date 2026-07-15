import re
from typing import Any

from agents.base import BaseAgent
from ocr.service import OCRService
from shared.schemas.documents import DocumentClassification, DocumentType


class DocumentIntakeAgent(BaseAgent):
    name = "DocumentIntakeAgent"
    description = "Classifies documents, assesses quality, and runs OCR normalization"

    def __init__(self) -> None:
        super().__init__()
        self.ocr_service = OCRService()

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        document_bytes: bytes = context["document_bytes"]
        filename: str = context.get("filename", "document.pdf")

        ocr_result = await self.ocr_service.extract_text(document_bytes, filename)
        text = ocr_result.text
        classification = self._classify_document(text, filename)
        quality_score = self._assess_quality(text, ocr_result.confidence)

        insight = self._create_insight(
            reasoning=(
                f"Document classified as {classification.document_type.value} with "
                f"{classification.confidence:.0%} confidence. Quality score: {quality_score:.0%}. "
                f"OCR provider: {ocr_result.provider}. Pages: {classification.page_count}."
            ),
            confidence=classification.confidence,
            evidence=[
                f"Filename pattern: {filename}",
                f"OCR confidence: {ocr_result.confidence:.2f}",
                f"Text length: {len(text)} characters",
            ],
            next_action="Route to Invoice Understanding Agent" if classification.document_type == DocumentType.INVOICE else "Route to Contract Intelligence Agent",
        )

        return {
            "classification": classification.model_dump(),
            "ocr_text": text,
            "ocr_provider": ocr_result.provider,
            "quality_score": quality_score,
            "normalized_text": self._normalize_text(text),
            "insight": insight,
        }

    def _classify_document(self, text: str, filename: str) -> DocumentClassification:
        text_lower = text.lower()
        filename_lower = filename.lower()

        scores = {
            DocumentType.INVOICE: 0.0,
            DocumentType.CONTRACT: 0.0,
            DocumentType.PURCHASE_ORDER: 0.0,
        }

        invoice_signals = ["invoice", "bill to", "invoice number", "inv-", "due date", "amount due"]
        contract_signals = ["agreement", "contract", "whereas", "party of the first", "termination", "clause"]
        po_signals = ["purchase order", "po number", "po-", "order date", "ship to"]

        for signal in invoice_signals:
            if signal in text_lower or signal in filename_lower:
                scores[DocumentType.INVOICE] += 0.15
        for signal in contract_signals:
            if signal in text_lower or signal in filename_lower:
                scores[DocumentType.CONTRACT] += 0.15
        for signal in po_signals:
            if signal in text_lower or signal in filename_lower:
                scores[DocumentType.PURCHASE_ORDER] += 0.15

        doc_type = max(scores, key=scores.get)
        confidence = min(0.98, max(0.5, scores[doc_type] + 0.3))

        return DocumentClassification(
            document_type=doc_type if scores[doc_type] > 0 else DocumentType.UNKNOWN,
            confidence=confidence,
            quality_score=0.85,
            page_count=max(1, text.count("\f") + 1),
            requires_ocr=len(text.strip()) < 50,
        )

    def _assess_quality(self, text: str, ocr_confidence: float) -> float:
        if not text.strip():
            return 0.1
        char_diversity = len(set(text)) / max(len(text), 1)
        length_score = min(1.0, len(text) / 500)
        return min(1.0, (ocr_confidence * 0.5) + (char_diversity * 0.25) + (length_score * 0.25))

    def _normalize_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\x00-\x7F]+", " ", text)
        return text.strip()
