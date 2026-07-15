"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-15 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("admin", "finance_manager", "procurement", "legal", "director", "cfo", "ap_clerk", "auditor", "viewer", name="userrole"), nullable=False),
        sa.Column("department", sa.String(100)),
        sa.Column("is_active", sa.Boolean, nullable=False),
        sa.Column("oauth_provider", sa.String(50)),
        sa.Column("oauth_subject", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "vendors",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("vendor_code", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("tax_id", sa.String(100)),
        sa.Column("gst_number", sa.String(100)),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("payment_terms", sa.String(100)),
        sa.Column("trust_score", sa.Float, nullable=False),
        sa.Column("contract_health_score", sa.Float, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False),
        sa.Column("metadata_json", sa.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_vendors_vendor_code", "vendors", ["vendor_code"])
    op.create_index("ix_vendors_name", "vendors", ["name"])

    op.create_table(
        "contracts",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("contract_number", sa.String(100), unique=True, nullable=False),
        sa.Column("vendor_id", UUID, sa.ForeignKey("vendors.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True)),
        sa.Column("end_date", sa.DateTime(timezone=True)),
        sa.Column("total_value", sa.Numeric(18, 2)),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("document_path", sa.String(500)),
        sa.Column("clauses_json", sa.JSON),
        sa.Column("health_score", sa.Float, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_contracts_contract_number", "contracts", ["contract_number"])
    op.create_index("ix_contracts_vendor_id", "contracts", ["vendor_id"])

    op.create_table(
        "purchase_orders",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("po_number", sa.String(100), unique=True, nullable=False),
        sa.Column("vendor_id", UUID, sa.ForeignKey("vendors.id")),
        sa.Column("department", sa.String(100)),
        sa.Column("requester", sa.String(255)),
        sa.Column("order_date", sa.DateTime(timezone=True)),
        sa.Column("total_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("line_items_json", sa.JSON),
        sa.Column("goods_receipt_json", sa.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_purchase_orders_po_number", "purchase_orders", ["po_number"])
    op.create_index("ix_purchase_orders_vendor_id", "purchase_orders", ["vendor_id"])

    op.create_table(
        "invoices",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("invoice_number", sa.String(100), nullable=False),
        sa.Column("vendor_id", UUID, sa.ForeignKey("vendors.id")),
        sa.Column("po_id", UUID, sa.ForeignKey("purchase_orders.id")),
        sa.Column("contract_id", UUID, sa.ForeignKey("contracts.id")),
        sa.Column("status", sa.Enum("received", "processing", "pending_approval", "approved", "rejected", "escalated", "paid", "exception", name="invoicestatus"), nullable=False),
        sa.Column("invoice_date", sa.DateTime(timezone=True)),
        sa.Column("due_date", sa.DateTime(timezone=True)),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("subtotal", sa.Numeric(18, 2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("payment_terms", sa.String(100)),
        sa.Column("document_path", sa.String(500)),
        sa.Column("extracted_data_json", sa.JSON),
        sa.Column("risk_score", sa.Float, nullable=False),
        sa.Column("fraud_score", sa.Float, nullable=False),
        sa.Column("health_score", sa.Float, nullable=False),
        sa.Column("compliance_score", sa.Float, nullable=False),
        sa.Column("auto_approved", sa.Boolean, nullable=False),
        sa.Column("processing_time_ms", sa.Integer),
        sa.Column("ai_summary", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("invoice_number", "vendor_id", name="uq_invoice_vendor"),
    )
    op.create_index("ix_invoices_invoice_number", "invoices", ["invoice_number"])
    op.create_index("ix_invoices_vendor_id", "invoices", ["vendor_id"])

    op.create_table(
        "invoice_exceptions",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("invoice_id", UUID, sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("reasoning", sa.Text, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("evidence_json", sa.JSON),
        sa.Column("contract_clause", sa.Text),
        sa.Column("policy_reference", sa.String(500)),
        sa.Column("suggested_resolution", sa.Text),
        sa.Column("business_impact", sa.Text),
        sa.Column("financial_impact", sa.Numeric(18, 2), nullable=False),
        sa.Column("estimated_loss", sa.Numeric(18, 2), nullable=False),
        sa.Column("status", sa.Enum("open", "in_review", "resolved", "escalated", "dismissed", name="exceptionstatus"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_invoice_exceptions_invoice_id", "invoice_exceptions", ["invoice_id"])
    op.create_index("ix_invoice_exceptions_category", "invoice_exceptions", ["category"])

    op.create_table(
        "approval_workflows",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("invoice_id", UUID, sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("approver_id", UUID, sa.ForeignKey("users.id")),
        sa.Column("approver_role", sa.String(100), nullable=False),
        sa.Column("department", sa.String(100), nullable=False),
        sa.Column("priority", sa.Integer, nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("reason", sa.Text),
        sa.Column("sla_hours", sa.Integer, nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("comments", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_approval_workflows_invoice_id", "approval_workflows", ["invoice_id"])

    op.create_table(
        "agent_insights",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("invoice_id", UUID, sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("reasoning", sa.Text, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("evidence_json", sa.JSON),
        sa.Column("metadata_json", sa.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_insights_invoice_id", "agent_insights", ["invoice_id"])
    op.create_index("ix_agent_insights_agent_name", "agent_insights", ["agent_name"])

    op.create_table(
        "audit_logs",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(100)),
        sa.Column("details_json", sa.JSON),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    op.create_table(
        "documents",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100)),
        sa.Column("file_size", sa.Integer),
        sa.Column("checksum", sa.String(64)),
        sa.Column("ocr_text", sa.Text),
        sa.Column("classification_json", sa.JSON),
        sa.Column("indexed_in_rag", sa.Boolean, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_documents_document_type", "documents", ["document_type"])

    op.create_table(
        "human_feedback",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("invoice_id", UUID, sa.ForeignKey("invoices.id")),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id")),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("rating", sa.Integer, nullable=False),
        sa.Column("correction", sa.Text),
        sa.Column("feedback_type", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("human_feedback")
    op.drop_table("documents")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_agent_insights_agent_name", table_name="agent_insights")
    op.drop_index("ix_agent_insights_invoice_id", table_name="agent_insights")
    op.drop_table("agent_insights")
    op.drop_index("ix_approval_workflows_invoice_id", table_name="approval_workflows")
    op.drop_table("approval_workflows")
    op.drop_index("ix_invoice_exceptions_category", table_name="invoice_exceptions")
    op.drop_index("ix_invoice_exceptions_invoice_id", table_name="invoice_exceptions")
    op.drop_table("invoice_exceptions")
    op.drop_index("ix_invoices_vendor_id", table_name="invoices")
    op.drop_index("ix_invoices_invoice_number", table_name="invoices")
    op.drop_table("invoices")
    op.drop_index("ix_purchase_orders_vendor_id", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_po_number", table_name="purchase_orders")
    op.drop_table("purchase_orders")
    op.drop_index("ix_contracts_vendor_id", table_name="contracts")
    op.drop_index("ix_contracts_contract_number", table_name="contracts")
    op.drop_table("contracts")
    op.drop_index("ix_vendors_name", table_name="vendors")
    op.drop_index("ix_vendors_vendor_code", table_name="vendors")
    op.drop_table("vendors")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="invoicestatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="exceptionstatus").drop(op.get_bind(), checkfirst=True)