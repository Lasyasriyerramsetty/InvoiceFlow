import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    role: str = "ap_clerk"
    department: str | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    department: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    vendor_name: str | None = None
    status: str
    total_amount: float
    currency: str
    risk_score: float
    fraud_score: float
    health_score: float
    auto_approved: bool
    ai_summary: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExceptionResponse(BaseModel):
    id: uuid.UUID
    category: str
    severity: str
    title: str
    description: str
    reasoning: str
    confidence: float
    suggested_resolution: str | None
    financial_impact: float
    status: str

    model_config = {"from_attributes": True}


class DashboardKPIs(BaseModel):
    total_invoices: int
    pending_invoices: int
    auto_approvals: int
    manual_approvals: int
    fraud_alerts: int
    avg_processing_time_ms: float
    total_invoice_value: float
    avg_risk_score: float
    savings_generated: float
    avg_approval_time_hours: float
    exception_breakdown: dict[str, int]
    status_breakdown: dict[str, int]
    monthly_trend: list[dict]
    risk_heatmap: list[dict]
    vendor_scores: list[dict]


class CopilotRequest(BaseModel):
    question: str
    invoice_id: uuid.UUID | None = None
    context: dict = Field(default_factory=dict)


class CopilotResponse(BaseModel):
    answer: str
    intent: str
    confidence: float
    evidence: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)


class ProcessingResultResponse(BaseModel):
    pipeline_id: str
    invoice_id: str
    status: str
    processing_time_ms: int
    exceptions_count: int
    risk_score: float | None
    recommendation: str | None
    agent_insights_count: int
