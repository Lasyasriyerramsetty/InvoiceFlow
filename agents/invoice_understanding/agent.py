import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from agents.base import BaseAgent
from shared.schemas.documents import ExtractedInvoice, InvoiceLineItem


class InvoiceUnderstandingAgent(BaseAgent):
    name = "InvoiceUnderstandingAgent"
    description = "Extracts structured invoice data with confidence scores"

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        text: str = context.get("normalized_text") or context.get("ocr_text", "")
        extracted = self._extract_invoice(text)

        insight = self._create_insight(
            reasoning=(
                f"Extracted invoice {extracted.invoice_number} from vendor '{extracted.vendor_name}' "
                f"for {extracted.currency} {extracted.total_amount:,.2f}. "
                f"Found {len(extracted.line_items)} line items with "
                f"{extracted.extraction_confidence:.0%} overall confidence."
            ),
            confidence=extracted.extraction_confidence,
            evidence=[
                f"Invoice Number: {extracted.invoice_number}",
                f"Vendor: {extracted.vendor_name}",
                f"Total: {extracted.currency} {extracted.total_amount}",
                f"Line items: {len(extracted.line_items)}",
            ],
            next_action="Proceed to PO Matching and Contract Intelligence",
        )

        return {"extracted_invoice": extracted.model_dump(), "insight": insight}

    def _extract_invoice(self, text: str) -> ExtractedInvoice:
        invoice_number = self._extract_pattern(
            text,
            [
                r"invoice\s*(?:number|no|num|#)\s*[:\s]*([A-Z0-9][A-Z0-9\-/]*)",
                r"inv[\-\.]?\s*(?:no|number|num|#)?\s*[:\s]*([A-Z0-9][A-Z0-9\-/]*)",
            ],
            default="INV-UNKNOWN",
        )
        vendor_name = self._extract_pattern(
            text,
            [r"(?:from|vendor|supplier)[:\s]+([A-Za-z0-9\s&.,]+?)(?:\n|$)", r"(?:bill from)[:\s]+(.+?)(?:\n|$)"],
            default="Unknown Vendor",
        ).strip()[:100]
        po_number = self._extract_pattern(
            text, [r"(?:po\s*(?:no|number|#)?[:\s]*)([A-Z0-9\-/]+)"], default=None
        )
        currency = self._detect_currency(text)
        total = self._extract_amount(
            text,
            [r"(?:total|amount due|grand total)[:\s]*(?:[\$₹€£])?\s*([\d,]+\.?\d*)"],
            default=Decimal("0"),
        )
        subtotal = self._extract_amount(
            text, [r"(?:subtotal|sub-total)[:\s]*(?:[\$₹€£])?\s*([\d,]+\.?\d*)"], default=total
        )
        tax = self._extract_amount(
            text,
            [r"(?:tax|gst|vat)[:\s]*(?:[\$₹€£])?\s*([\d,]+\.?\d*)", r"(?:gst\s*\d+%)[:\s]*([\d,]+\.?\d*)"],
            default=Decimal("0"),
        )
        gst_number = self._extract_pattern(
            text, [r"(?:gst(?:in)?|tax id)[:\s]*([A-Z0-9]+)"], default=None
        )
        payment_terms = self._extract_pattern(
            text, [r"(?:payment terms|terms)[:\s]+(.+?)(?:\n|$)"], default="Net 30"
        )
        line_items = self._extract_line_items(text)
        confidence = self._calculate_confidence(invoice_number, vendor_name, total, line_items)

        return ExtractedInvoice(
            invoice_number=invoice_number,
            vendor_name=vendor_name,
            invoice_date=self._extract_date(text),
            due_date=self._extract_due_date(text),
            currency=currency,
            subtotal=subtotal,
            tax_amount=tax,
            total_amount=total,
            payment_terms=payment_terms,
            po_number=po_number,
            gst_number=gst_number,
            line_items=line_items,
            extraction_confidence=confidence,
            raw_text=text[:5000],
        )

    def _extract_pattern(self, text: str, patterns: list[str], default: str | None = None) -> str | None:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return default

    def _extract_amount(self, text: str, patterns: list[str], default: Decimal) -> Decimal:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return Decimal(match.group(1).replace(",", ""))
                except InvalidOperation:
                    continue
        return default

    def _detect_currency(self, text: str) -> str:
        if "₹" in text or "INR" in text.upper():
            return "INR"
        if "€" in text or "EUR" in text.upper():
            return "EUR"
        if "£" in text or "GBP" in text.upper():
            return "GBP"
        return "USD"

    def _extract_date(self, text: str) -> date | None:
        patterns = [
            r"(?:invoice date|date)[:\s]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
            r"(\d{4}-\d{2}-\d{2})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_date(match.group(1))
        return None

    def _extract_due_date(self, text: str) -> date | None:
        match = re.search(r"(?:due date)[:\s]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})", text, re.IGNORECASE)
        if match:
            return self._parse_date(match.group(1))
        return None

    def _parse_date(self, date_str: str) -> date | None:
        for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None

    def _extract_line_items(self, text: str) -> list[InvoiceLineItem]:
        items: list[InvoiceLineItem] = []
        line_pattern = re.compile(
            r"([A-Za-z][A-Za-z0-9 .&\-]*?)\s+(\d+\.?\d*)\s+(?:[₹$€£]\s*)?([\d,]+\.?\d*)\s+(?:[₹$€£]\s*)?([\d,]+\.?\d*)"
        )
        for idx, match in enumerate(line_pattern.finditer(text), start=1):
            try:
                items.append(
                    InvoiceLineItem(
                        line_number=idx,
                        description=match.group(1).strip(),
                        quantity=Decimal(match.group(2)),
                        unit_price=Decimal(match.group(3).replace(",", "")),
                        total_amount=Decimal(match.group(4).replace(",", "")),
                        confidence=0.85,
                    )
                )
            except InvalidOperation:
                continue

        if not items:
            amount_match = re.search(r"(?:total|amount)[:\s]*(?:[\$₹€£])?\s*([\d,]+\.?\d*)", text, re.IGNORECASE)
            if amount_match:
                total = Decimal(amount_match.group(1).replace(",", ""))
                items.append(
                    InvoiceLineItem(
                        line_number=1,
                        description="General Services",
                        quantity=Decimal("1"),
                        unit_price=total,
                        total_amount=total,
                        confidence=0.6,
                    )
                )
        return items

    def _calculate_confidence(
        self, invoice_number: str, vendor: str, total: Decimal, line_items: list
    ) -> float:
        score = 0.5
        if invoice_number and invoice_number != "INV-UNKNOWN":
            score += 0.15
        if vendor and vendor != "Unknown Vendor":
            score += 0.15
        if total > 0:
            score += 0.1
        if line_items:
            score += 0.1
        return min(0.98, score)
