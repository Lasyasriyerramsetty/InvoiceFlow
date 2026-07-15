from decimal import Decimal

from shared.schemas.documents import InvoiceLineItem, ExtractedInvoice


class TestSchemas:
    def test_invoice_line_item(self):
        item = InvoiceLineItem(
            line_number=1,
            description="Test Item",
            quantity=Decimal("10"),
            unit_price=Decimal("100"),
            total_amount=Decimal("1000"),
        )
        assert item.line_number == 1
        assert float(item.quantity) == 10

    def test_extracted_invoice(self):
        invoice = ExtractedInvoice(
            invoice_number="INV-001",
            vendor_name="Test Vendor",
            subtotal=Decimal("1000"),
            total_amount=Decimal("1100"),
            extraction_confidence=0.95,
        )
        assert invoice.invoice_number == "INV-001"
        assert invoice.currency == "USD"