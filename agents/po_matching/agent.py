from decimal import Decimal
from typing import Any

from agents.base import BaseAgent
from shared.schemas.documents import InvoiceLineItem, PurchaseOrderData


class POMatchingAgent(BaseAgent):
    name = "POMatchingAgent"
    description = "Performs intelligent 3-way matching: Invoice → PO → Goods Receipt"

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        extracted = context.get("extracted_invoice", {})
        po_data = context.get("purchase_order")
        is_synthetic_po = False
        if not po_data:
            po_data = self._get_mock_po(extracted)
            is_synthetic_po = po_data is not None
        gr_data = context.get("goods_receipt") or (po_data or {}).get("goods_receipt_json", {})

        po = PurchaseOrderData(**po_data) if isinstance(po_data, dict) else po_data
        invoice_items = [
            InvoiceLineItem(**item) if isinstance(item, dict) else item
            for item in extracted.get("line_items", [])
        ]

        mismatches = []
        match_score = 100.0

        if not po:
            mismatches.append({
                "type": "missing_po",
                "severity": "high",
                "description": "No purchase order found for this invoice",
            })
            match_score -= 40
        else:
            if extracted.get("currency") != po.currency:
                mismatches.append({
                    "type": "currency_mismatch",
                    "severity": "high",
                    "description": f"Invoice currency {extracted.get('currency')} vs PO currency {po.currency}",
                    "expected": po.currency,
                    "actual": extracted.get("currency"),
                })
                match_score -= 25

            invoice_total = Decimal(str(extracted.get("total_amount", 0)))
            po_total = Decimal(str(po.total_amount))
            tolerance = po_total * Decimal("0.03")
            if abs(invoice_total - po_total) > tolerance:
                diff = invoice_total - po_total
                mismatches.append({
                    "type": "amount_mismatch",
                    "severity": "medium" if abs(diff) < po_total * Decimal("0.1") else "high",
                    "description": f"Invoice total {invoice_total} differs from PO total {po_total} by {diff}",
                    "expected": str(po_total),
                    "actual": str(invoice_total),
                    "financial_impact": float(abs(diff)),
                })
                match_score -= 20

            for inv_item in invoice_items:
                po_item = self._find_po_line(po.line_items, inv_item)
                if po_item:
                    if inv_item.quantity > po_item.quantity:
                        mismatches.append({
                            "type": "quantity_mismatch",
                            "severity": "medium",
                            "description": (
                                f"Line {inv_item.line_number}: invoiced qty {inv_item.quantity} "
                                f"exceeds PO qty {po_item.quantity}"
                            ),
                        })
                        match_score -= 10
                    price_diff = inv_item.unit_price - po_item.unit_price
                    if price_diff > po_item.unit_price * Decimal("0.03"):
                        mismatches.append({
                            "type": "price_mismatch",
                            "severity": "high",
                            "description": (
                                f"Line {inv_item.line_number}: unit price {inv_item.unit_price} "
                                f"exceeds PO price {po_item.unit_price} by {price_diff}"
                            ),
                            "financial_impact": float(price_diff * inv_item.quantity),
                        })
                        match_score -= 15

            gr_received = gr_data.get("received_quantity", po_total)
            if gr_received and invoice_total > Decimal(str(gr_received)) * Decimal("1.05"):
                mismatches.append({
                    "type": "delivery_mismatch",
                    "severity": "medium",
                    "description": "Invoice amount exceeds goods receipt value",
                })
                match_score -= 10

        match_score = max(0, match_score)
        insight = self._create_insight(
            reasoning=(
                f"3-way match completed with score {match_score:.0f}/100. "
                f"Found {len(mismatches)} mismatch(es). "
                + (mismatches[0]["description"] if mismatches else "All line items match PO and GR.")
            ),
            confidence=0.9 if match_score > 80 else 0.75,
            evidence=[m["description"] for m in mismatches],
            business_impact="Payment blocked until PO discrepancies resolved" if mismatches else "Ready for payment",
            financial_impact=sum(m.get("financial_impact", 0) for m in mismatches),
            next_action="Escalate to Procurement" if mismatches else "Proceed to policy validation",
        )

        return {
            "po_match_result": {
                "match_score": match_score,
                "mismatches": mismatches,
                "po_number": po.po_number if po else None,
                "three_way_match_status": "pass" if match_score >= 90 else "fail",
            },
            "insight": insight,
            "synthetic_po_used": is_synthetic_po,
        }

    def _find_po_line(self, po_items: list, inv_item: InvoiceLineItem) -> InvoiceLineItem | None:
        for item in po_items:
            po_item = InvoiceLineItem(**item) if isinstance(item, dict) else item
            if po_item.line_number == inv_item.line_number:
                return po_item
            if inv_item.description.lower() in po_item.description.lower():
                return po_item
        return po_items[0] if po_items else None

    def _get_mock_po(self, extracted: dict) -> dict | None:
        po_number = extracted.get("po_number")
        if not po_number:
            return None
        total = float(extracted.get("total_amount", 0))
        if total <= 0:
            return None
        return {
            "po_number": po_number,
            "vendor_name": extracted.get("vendor_name", ""),
            "total_amount": total * 0.97,
            "currency": extracted.get("currency", "USD"),
            "line_items": extracted.get("line_items", []),
            "goods_receipt_json": {"received_quantity": total * 0.97},
            "synthetic": True,
        }
