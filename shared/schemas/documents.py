from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    PURCHASE_ORDER = "purchase_order"
    GOODS_RECEIPT = "goods_receipt"
    VENDOR_AGREEMENT = "vendor_agreement"
    POLICY = "policy"
    UNKNOWN = "unknown"


class DocumentClassification(BaseModel):
    document_type: DocumentType
    confidence: float = Field(ge=0.0, le=1.0)
    quality_score: float = Field(ge=0.0, le=1.0)
    language: str = "en"
    page_count: int = 1
    is_scanned: bool = False
    requires_ocr: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class InvoiceLineItem(BaseModel):
    line_number: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    total_amount: Decimal
    tax_amount: Decimal = Decimal("0")
    sku: str | None = None
    po_line_reference: str | None = None
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)


class ExtractedInvoice(BaseModel):
    invoice_number: str
    vendor_name: str
    vendor_id: str | None = None
    vendor_tax_id: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    currency: str = "USD"
    subtotal: Decimal
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal
    payment_terms: str | None = None
    po_number: str | None = None
    shipping_amount: Decimal = Decimal("0")
    gst_number: str | None = None
    line_items: list[InvoiceLineItem] = Field(default_factory=list)
    extraction_confidence: float = Field(ge=0.0, le=1.0)
    raw_text: str = ""


class ContractClause(BaseModel):
    clause_id: str
    clause_type: str
    title: str
    content: str
    section: str | None = None
    effective_date: date | None = None
    expiry_date: date | None = None
    relevance_score: float = Field(ge=0.0, le=1.0)
    source_document_id: str | None = None


class PurchaseOrderData(BaseModel):
    po_number: str
    vendor_name: str
    vendor_id: str | None = None
    order_date: date | None = None
    currency: str = "USD"
    total_amount: Decimal
    line_items: list[InvoiceLineItem] = Field(default_factory=list)
    status: str = "open"
    department: str | None = None
    requester: str | None = None
