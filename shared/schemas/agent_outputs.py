from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExceptionSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExceptionCategory(str, Enum):
    PRICE_MISMATCH = "price_mismatch"
    DUPLICATE_INVOICE = "duplicate_invoice"
    MISSING_PO = "missing_po"
    WRONG_GST = "wrong_gst"
    WRONG_VENDOR = "wrong_vendor"
    CONTRACT_EXPIRED = "contract_expired"
    QUANTITY_MISMATCH = "quantity_mismatch"
    CURRENCY_MISMATCH = "currency_mismatch"
    FRAUD_INDICATOR = "fraud_indicator"
    TAX_MISMATCH = "tax_mismatch"
    DELIVERY_MISMATCH = "delivery_mismatch"
    LATE_INVOICE = "late_invoice"
    UNAUTHORIZED_APPROVER = "unauthorized_approver"
    SPLIT_INVOICE = "split_invoice"
    ROUND_OFF_FRAUD = "round_off_fraud"
    REPEATED_PATTERN = "repeated_pattern"
    POLICY_VIOLATION = "policy_violation"
    BUDGET_EXCEEDED = "budget_exceeded"


class RiskLevel(str, Enum):
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentInsight(BaseModel):
    agent_name: str
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    policy_references: list[str] = Field(default_factory=list)
    contract_clauses: list[str] = Field(default_factory=list)
    suggested_resolution: str = ""
    business_impact: str = ""
    financial_impact: Decimal = Decimal("0")
    estimated_loss: Decimal = Decimal("0")
    next_action: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExceptionDetail(BaseModel):
    exception_id: str
    category: ExceptionCategory
    severity: ExceptionSeverity
    title: str
    description: str
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    contract_clause: str | None = None
    policy_reference: str | None = None
    suggested_resolution: str = ""
    business_impact: str = ""
    financial_impact: Decimal = Decimal("0")
    estimated_loss: Decimal = Decimal("0")
    field_path: str | None = None
    expected_value: str | None = None
    actual_value: str | None = None


class RiskScore(BaseModel):
    overall_score: float = Field(ge=0.0, le=100.0)
    risk_level: RiskLevel
    fraud_score: float = Field(ge=0.0, le=100.0, default=0.0)
    compliance_score: float = Field(ge=0.0, le=100.0, default=100.0)
    matching_score: float = Field(ge=0.0, le=100.0, default=100.0)
    factors: list[str] = Field(default_factory=list)
    heatmap_data: dict[str, float] = Field(default_factory=dict)


class FraudAssessment(BaseModel):
    is_suspicious: bool
    fraud_confidence: float = Field(ge=0.0, le=1.0)
    fraud_types: list[str] = Field(default_factory=list)
    indicators: list[str] = Field(default_factory=list)
    reasoning: str = ""
    recommended_action: str = ""


class RecommendationResult(BaseModel):
    summary: str
    approval_recommendation: str
    escalation_recommendation: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    business_impact: str = ""
    financial_impact: Decimal = Decimal("0")
    resolution_steps: list[str] = Field(default_factory=list)
    insights: list[AgentInsight] = Field(default_factory=list)


class WorkflowRoute(BaseModel):
    approver_role: str
    approver_name: str | None = None
    department: str
    priority: int
    reason: str
    sla_hours: int = 24


class ProcessingPipelineResult(BaseModel):
    pipeline_id: str
    invoice_id: str
    status: str
    classification: dict[str, Any] = Field(default_factory=dict)
    extracted_invoice: dict[str, Any] = Field(default_factory=dict)
    contract_clauses: list[dict[str, Any]] = Field(default_factory=list)
    po_match_result: dict[str, Any] = Field(default_factory=dict)
    policy_validation: dict[str, Any] = Field(default_factory=dict)
    exceptions: list[ExceptionDetail] = Field(default_factory=list)
    fraud_assessment: FraudAssessment | None = None
    risk_score: RiskScore | None = None
    recommendation: RecommendationResult | None = None
    workflow_routes: list[WorkflowRoute] = Field(default_factory=list)
    agent_insights: list[AgentInsight] = Field(default_factory=list)
    processing_time_ms: int = 0
    completed_at: datetime = Field(default_factory=datetime.utcnow)
