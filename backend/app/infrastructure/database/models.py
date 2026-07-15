import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserRole(str, PyEnum):
    ADMIN = "admin"
    FINANCE_MANAGER = "finance_manager"
    PROCUREMENT = "procurement"
    LEGAL = "legal"
    DIRECTOR = "director"
    CFO = "cfo"
    AP_CLERK = "ap_clerk"
    AUDITOR = "auditor"
    VIEWER = "viewer"


class InvoiceStatus(str, PyEnum):
    RECEIVED = "received"
    PROCESSING = "processing"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    PAID = "paid"
    EXCEPTION = "exception"


class ExceptionStatus(str, PyEnum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    DISMISSED = "dismissed"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.AP_CLERK)
    department: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    oauth_provider: Mapped[str | None] = mapped_column(String(50))
    oauth_subject: Mapped[str | None] = mapped_column(String(255))

    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")
    approvals: Mapped[list["ApprovalWorkflow"]] = relationship(back_populates="approver")


class Vendor(Base, TimestampMixin):
    __tablename__ = "vendors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    tax_id: Mapped[str | None] = mapped_column(String(100))
    gst_number: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(2), default="US")
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    payment_terms: Mapped[str | None] = mapped_column(String(100))
    trust_score: Mapped[float] = mapped_column(Float, default=75.0)
    contract_health_score: Mapped[float] = mapped_column(Float, default=80.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)

    invoices: Mapped[list["Invoice"]] = relationship(back_populates="vendor")
    contracts: Mapped[list["Contract"]] = relationship(back_populates="vendor")


class Contract(Base, TimestampMixin):
    __tablename__ = "contracts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_number: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendors.id"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_value: Mapped[float | None] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[str] = mapped_column(String(50), default="active")
    document_path: Mapped[str | None] = mapped_column(String(500))
    clauses_json: Mapped[dict | None] = mapped_column(JSON)
    health_score: Mapped[float] = mapped_column(Float, default=85.0)

    vendor: Mapped["Vendor"] = relationship(back_populates="contracts")


class PurchaseOrder(Base, TimestampMixin):
    __tablename__ = "purchase_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_number: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("vendors.id"), index=True)
    department: Mapped[str | None] = mapped_column(String(100))
    requester: Mapped[str | None] = mapped_column(String(255))
    order_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_amount: Mapped[float] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[str] = mapped_column(String(50), default="open")
    line_items_json: Mapped[dict | None] = mapped_column(JSON)
    goods_receipt_json: Mapped[dict | None] = mapped_column(JSON)


class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_number: Mapped[str] = mapped_column(String(100), index=True)
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("vendors.id"), index=True)
    po_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("purchase_orders.id"))
    contract_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("contracts.id"))
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus), default=InvoiceStatus.RECEIVED)
    invoice_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    subtotal: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    tax_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    payment_terms: Mapped[str | None] = mapped_column(String(100))
    document_path: Mapped[str | None] = mapped_column(String(500))
    extracted_data_json: Mapped[dict | None] = mapped_column(JSON)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    fraud_score: Mapped[float] = mapped_column(Float, default=0.0)
    health_score: Mapped[float] = mapped_column(Float, default=100.0)
    compliance_score: Mapped[float] = mapped_column(Float, default=100.0)
    auto_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer)
    ai_summary: Mapped[str | None] = mapped_column(Text)

    vendor: Mapped["Vendor | None"] = relationship(back_populates="invoices")
    exceptions: Mapped[list["InvoiceException"]] = relationship(back_populates="invoice")
    approvals: Mapped[list["ApprovalWorkflow"]] = relationship(back_populates="invoice")
    agent_insights: Mapped[list["AgentInsightRecord"]] = relationship(back_populates="invoice")

    __table_args__ = (UniqueConstraint("invoice_number", "vendor_id", name="uq_invoice_vendor"),)


class InvoiceException(Base, TimestampMixin):
    __tablename__ = "invoice_exceptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id"), index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    severity: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    reasoning: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    evidence_json: Mapped[dict | None] = mapped_column(JSON)
    contract_clause: Mapped[str | None] = mapped_column(Text)
    policy_reference: Mapped[str | None] = mapped_column(String(500))
    suggested_resolution: Mapped[str | None] = mapped_column(Text)
    business_impact: Mapped[str | None] = mapped_column(Text)
    financial_impact: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    estimated_loss: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    status: Mapped[ExceptionStatus] = mapped_column(Enum(ExceptionStatus), default=ExceptionStatus.OPEN)

    invoice: Mapped["Invoice"] = relationship(back_populates="exceptions")


class ApprovalWorkflow(Base, TimestampMixin):
    __tablename__ = "approval_workflows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id"), index=True)
    approver_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    approver_role: Mapped[str] = mapped_column(String(100))
    department: Mapped[str] = mapped_column(String(100))
    priority: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    reason: Mapped[str | None] = mapped_column(Text)
    sla_hours: Mapped[int] = mapped_column(Integer, default=24)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    comments: Mapped[str | None] = mapped_column(Text)

    invoice: Mapped["Invoice"] = relationship(back_populates="approvals")
    approver: Mapped["User | None"] = relationship(back_populates="approvals")


class AgentInsightRecord(Base, TimestampMixin):
    __tablename__ = "agent_insights"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id"), index=True)
    agent_name: Mapped[str] = mapped_column(String(100), index=True)
    reasoning: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    evidence_json: Mapped[dict | None] = mapped_column(JSON)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)

    invoice: Mapped["Invoice"] = relationship(back_populates="agent_insights")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100), index=True)
    resource_type: Mapped[str] = mapped_column(String(100))
    resource_id: Mapped[str | None] = mapped_column(String(100))
    details_json: Mapped[dict | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    user: Mapped["User | None"] = relationship(back_populates="audit_logs")


class DocumentRecord(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(500))
    document_type: Mapped[str] = mapped_column(String(50), index=True)
    storage_path: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    file_size: Mapped[int | None] = mapped_column(Integer)
    checksum: Mapped[str | None] = mapped_column(String(64))
    ocr_text: Mapped[str | None] = mapped_column(Text)
    classification_json: Mapped[dict | None] = mapped_column(JSON)
    indexed_in_rag: Mapped[bool] = mapped_column(Boolean, default=False)


class FeedbackRecord(Base, TimestampMixin):
    __tablename__ = "human_feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("invoices.id"))
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    agent_name: Mapped[str] = mapped_column(String(100))
    rating: Mapped[int] = mapped_column(Integer)
    correction: Mapped[str | None] = mapped_column(Text)
    feedback_type: Mapped[str] = mapped_column(String(50))
